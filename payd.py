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
from payapp.models import PaymentHistory

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Misc
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
import json
from datetime import datetime
from time import mktime
from time import time

from payapp.paymentez import PaymentezGateway
from payapp.paymentez import PaymentezTx
from payapp.misc import paymentez_translator

from payapp.intercom import Intercom

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
        msg = "User %s has not card enabled" % user.user_id
        logging.error("get_card(): %s" % msg)
        return None
    except MultipleObjectsReturned:
        msg = "User %s has multiple cards enabled" % user.user_id
        logging.error("get_card(): %s" % msg)
        return None

    return card


def paymentez_payment(up, card):
    try:
        gw = PaymentezGateway(IntegratorSetting.get_var(card.integrator,'paymentez_server_application_code'),
                              IntegratorSetting.get_var(card.integrator,'paymentez_server_app_key'),
                              IntegratorSetting.get_var(card.integrator,'paymentez_endpoint'))
    except Exception as e:
        msg = "could not create user payment: (%s)" % str(e)
        up.error(msg)
        logging.error("paymentez_payment(): %s" % msg)
        return False

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
    payment_id = "PH_%s_%d" % (up.user.user_id, int(time.time()))

    # Creo el registro en PaymentHistory
    ph = PaymentHistory.create(up, card, payment_id, amount, disc_pct)
    logging.info("paymentez_payment(): Payment history created. ID: %s" % ph.payment_id)


    # Realizo el pago
    try:
        logging.info("paymentez_payment(): Executing payment - User: %s - email: %s - amount: %s - "
                     "card: %s - payment_id: %s" % (up.user.user_id, up.user.email, amount, card.token, ph.payment_id))
        ret, content = gw.doPost(PaymentezTx(up.user.user_id, up.user.email, ph.amount, 'HotGo',
                                             ph.payment_id, ph.taxable_amount, ph.vat_amount, card.token))
    except Exception as e:
        logging.info("paymentez_payment(): Communication error. New PaymentHistory status: Waiting Callback")
        # Pongo el pago en Waiting Callback
        ph.status = "W"
        ph.save()
        return False

    if ret:
        # Obtengo los valores segun la respuesta de Paymentez
        pr = paymentez_translator(content)
        # Seteo los valores de la UserPayment
        logging.info("paymentez_payment(): Setting UserPayment values: status: %s - enabled: %s - message: %s"
                     % (pr["up_status"], str(pr["up_recurrence"]), pr["up_recurrence"]))
        up.status  = pr["up_status"]
        up.message = pr["up_message"]
        up.enabled = pr["up_recurrence"]

        if up.status == 'AC':
            # calcular next_payment_day
            up.payment_date = up.calc_payment_date()
            # Fija la fecha de expiration del usuario
            logging.info("paymentez_payment(): New user expiration %d for user %s" % (up.recurrence, up.user.user_id))
            up.user.add_to_expiration(up.recurrence)
            if disc_flag:
                up.disc_counter = up.disc_counter - 1
        else:
            up.channel = 'R'
        up.save()

        # Seteo los valores del PaymentHistory
        logging.info("paymentez_payment(): Setting PaymentHistory values: status: %s - gateway_id: %s - message: %s"
                     % (pr["ph_status"], pr["ph_gatewayid"], pr["ph_message"]))
        ph.status = pr["ph_status"]
        ph.gateway_id = pr["ph_gatewayid"]
        ph.message = pr["ph_message"]
        ph.save()

        if pr["user_expire"]:
            logging.info("paymentez_payment(): Disabling user access to %s" % up.user.user_id)
            up.user.expire()

        if pr["intercom"]["action"]:
            logging.info("paymentez_payment(): Sending event to Intercom: %s" % pr["intercom"]["event"])
            ep = Setting.get_var('intercom_endpoint')
            token = Setting.get_var('intercom_token')
            try:
                intercom = Intercom(ep, token)
                reply = intercom.submitEvent(up.user.user_id, up.user.email, pr["intercom"]["event"],
                                             {"paymentez": content})
                if not reply:
                    msg = "Intercom error: cannot post the event"
                    ph.message = "%s - %s" % (ph.message, msg)
                    logging.info("paymentez_payment(): %s" % msg)
                    ph.save()
            except Exception as e:
                msg = "Intercom error: %s" % str(e)
                ph.message = "%s - %s" % (ph.message, msg)
                logging.info("paymentez_payment(): %s" % msg)
                ph.save()

        logging.info("paymentez_payment(): Payment executed succesfully - UserPayment: %s" % up.user_payment_id)

        return True


def make_payment(up, card):
    if card.integrator.name == 'paymentez':
        ret = paymentez_payment(up, card)
    else:
        ret = False
    return ret


def payd_main():
    logging.basicConfig(format   = '%(asctime)s - payd.py -[%(levelname)s]: %(message)s',
                        filename = LOG_FILE,
                        level    = logging.INFO)

    settings = load_settings()
    if settings is None:
        exit(2)

    while True:
        # Obtengo todos los UserPayments activos y habilitados con payment_date vencido.
        logging.info("payd_main(): Getting active UserPayemnts to pay...")
        payments = UserPayment.objects.filter(status='AC', enabled=True, payment_date__lte=timezone.now())
        ips = Setting.get_var("payment_slot")
        for up in payments:
            if ips > 0:
                # Cambio a Pending.
                up.status = 'PE'
                up.save()
                logging.info("payd_main(): UserPayment %s new status... Pending" % up.user_payment_id)

                # Obtengo la tarjeta habilitada para el usuario
                card = get_card(up.user)
                if card is None:
                    msg = "Error getting card for user %s" % up.user.user_id
                    up.error(msg)
                    continue

                make_payment(up, card)
                ips = ips - 1
            else:
                logging.info("payd_main(): Payment slot limit reached. Next execution in %s seconds"
                             % str(settings['sleep_time_daemon']))

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
