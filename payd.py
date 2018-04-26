import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ccm.settings")
django.setup()
from django.utils import timezone

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Base Exceptions
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned 

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# App Model
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from payapp.models import Setting
from payapp.models import UserPayment
from payapp.models import Card
from payapp.models import IntegratorSetting


from paymentez import PaymentezGateway
from paymentez import PaymentezTx


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# System
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from daemon import Daemon
from sys    import exit
from sys    import argv

import logging
import time


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Basic Config
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
LOG_FILE = './log/payd.log'
ERR_FILE = './log/payd.err'
PID_FILE = './pid/payd.pid'


def load_settings():
    settings = {}

    try:
        settings['sleep_time_daemon'] = Setting.get_var('sleep_time_daemon')
    except ObjectDoesNotExist:
        logging.error("load_settings(): Setting with code sleep_time_daemon does not exist")
        return None

    return settings


def get_card(user):
    try:
        card = Card.objects.get(user=user, enabled=True)
    except ObjectDoesNotExist:
        msg = "User %s has not card enabled" % payment.user.user_id
        loggin.error("get_card(): %s" % msg)
        return None
    except MultipleObjectsReturned:
        msg = "User %s has multiple cards enabled" % payment.user.user_id
        loggin.error("get_card(): %s" % msg)
        return None

    return card


def paymentez_payment(up, card):
    try:
        gw = PaymentezGateway(IntegratorSetting.get_var(integrator,'paymentez_server_application_code'),
                              IntegratorSetting.get_var(integrator,'paymentez_server_app_key'),
                              IntegratorSetting.get_var(integrator,'paymentez_endpoint'))
    except Exception as e:
        msg = "could not create user payment: (%s)" % str(e)
        up.error(msg)
        logging.error("paymentez_payment(): %s" % msg)
        return None

    # Aplico descuento si corresponde
    disc_flag = False
    if up.disc_counter > 0:
        disc_flag = True
        amount    = up.calculate_discount()
        disc_pct  = up.disc_pct
        logging.info("paymentez_payment(): Calculating discount. New amount: %s" % amount)
    else:
        amount   = up.amount
        disc_pct = 0

    # Genero tx id sumando al userid el timestamp
    payment_id = "PH_%s_%d" % (user.user_id, int(time()))

    # Creo el registro en PaymentHistory
    ph = PaymentHistory.create(up, card, payment_id, amount, disc_pct)
    logging.info("paymentez_payment(): Payment history created. ID: %s" % ph.payment_id)


    # Realizo el pago
    try:
        logging.info("paymentez_payment(): Executing payment - User: %s - email: %s - amount: %s - card: %s - payment_id: %s" % (up.user.user_id, up.user.email, amount, card.token, ph.payment_id))
        ret, content = gw.doPost(PaymentezTx(user.user_id,user.email,ph.amount,'HotGo',ph.payment_id,ph.taxable_amount,ph.vat_amount,card.token))
    except Excepcion as e:
        pass
        # Definir con SC que hacemos en caso de error de comunicacion al momento del pago.
        # Se activa el UserPayment? Se activa la recurrencia? Que se le notifica al usuario?
        return None

    if ret:
        logging.info("paymentez_payment(): Reply content: %s" % content)
        # Fija la fecha de expiration del usuario
        up.user.add_to_expiration(int(data['recurrence']))
        # Lo pone activo
        up.status = 'AC'
        if disc_flag:
            up.disc_counter = up.disc_counter - 1
        up.save()
        ph.approve(content['transaction']['id'])
        logging.info("paymentez_payment(): Payment executed successfully. Next payment date: %s" % up.payment_date)
    else:
        message = 'type: %s, help: %s, description: %s' % (content['error']['type'],content['error']['help'],content['error']['description'])
        up.reply_error(message)
        ph.error(message)
        logging.error("paymentez_payment(): Payment error: %s" % message)
        return None

        return up


def make_payment(up, card):
    if card.integrator.name == 'paymentez':
        ret = paymentez_payment(up, card)

    return ret


def payd_main():
    logging.basicConfig(format   = '%(asctime)s - payd.py -[%(levelname)s]: %(message)s',
                        filename = LOG_FILE,
                        level    = logging.INFO)

    settings = load_settings()
    if settings is None:
        exit(2)

    while True:
        # Obtengo todos los UserPayments activos y habilitados con payment date vencido.
        logging.info("payd_main(): Getting active UserPayemnts to pay...")
        payments = UserPayment.objects.filter(status='AC', enabled=True, payment_date__lte=timezone.now())
        for up in payments:
            # Cambio a Pending todos los pagos pendientes de cobro.
            up.status = 'PE'
            up.save()
            logging.info("payd_main(): UserPayment %s new status... Pending" % up.user.user_id)

        # Obtengo todos los UserPayments en pending
        logging.info("payd_main(): Getting pending UserPayemnts...")
        payments = UserPayment.objects.filter(status='PE')
        for up in payments:
            # Obtengo la tarjeta habilitada para el usuario
            card = get_card(up.user)
            if card is None:
                msg = "Error getting card for user %s" % up.user.user_id
                up.error(msg)
                continue

            make_payment(up, card)

        time.sleep(settings['sleep_time_daemon'])


class DaemonMain(Daemon):
    def run(self):
        try:
            payd_main()
        except KeyboardInterrupt:
            exit()


if __name__ == "__main__":
    daemon = DaemonMain(PID_FILE, stdout=LOG_FILE, stderr=ERR_FILE)
    if len(argv) == 2:
        if 'start'     == argv[1]:
            daemon.start()
        elif 'stop'    == argv[1]:
            daemon.stop()
        elif 'restart' == argv[1]:
            daemon.restart()
        elif 'run'     == argv[1]:
            daemon.run()
        elif 'status'  == argv[1]:
            daemon.status()
        else:
            print "Unknown command"
            exit(2)
        exit(0)
    else:
        print "usage: %s start|stop|restart|run" % argv[0]
        exit(2)
