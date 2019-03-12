
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Django
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.core.exceptions import *

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# App Models
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from models import User
from models import UserPayment
from models import Setting
from models import Card
from models import PaymentHistory
from models import Currency
from models import Integrator
from models import Country
from models import IntegratorSetting

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Misc
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
import json
import hashlib
from datetime import datetime
from time import mktime
from time import time

from misc import paymentez_translator
from misc import paymentez_intercom_metadata

from intercom import Intercom

import logging

logger = logging.getLogger(__name__)

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Response Codes
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
http_POST_OK              = 201
http_REQUEST_OK           = 200
http_NOT_FOUND            = 404
http_BAD_REQUEST          = 400
http_UNPROCESSABLE_ENTITY = 422
http_NOT_ALLOWED          = 405
http_UNAUTHORIZED         = 401
http_INTERNAL_ERROR       = 500


def __validate_json(json_data, keys):
    for item in keys:
        for key, value in item.iteritems():
            if key in json_data:
                for v in value:
                    if v not in json_data[key]:
                        message = "missing key in json: %s" % v
                        return {'status': 'error', 'message': message}
            else:
                message = "missing key in json: %s" % key
                return {'status': 'error', 'message': message}

    return {'status': 'success'}


def __validate_stoken(data, country):
    country    = Country.objects.get(code=country)
    integrator = Integrator.objects.get(name="paymentez", country=country)
    tx_id    = data["transaction"]["id"]
    app_code = data["transaction"]["application_code"]
    stoken   = data["transaction"]["stoken"]
    user_id  = data["user"]["id"]
    app_key  = IntegratorSetting.get_var(integrator, 'paymentez_server_app_key')

    string = "%s_%s_%s_%s" % (tx_id, app_code, user_id, app_key)

    if stoken.lower() == hashlib.md5(string).hexdigest():
        return True
    else:
        return False


def __callback_paymentez_proc(data, country):
    # Verifico el stoken
    if not __validate_stoken(data, country):
        body = {"status": "error", "message": "not authorized"}
        return HttpResponse(json.dumps(body), content_type="application/json", status=200)

    # Obtengo los valores segun la respuesta de Paymentez
    pr = paymentez_translator(data)

    # Obtengo el PaymentHistory con el dev_reference informado
    try:
        ph = PaymentHistory.objects.get(payment_id=data["transaction"]["dev_reference"])
    except ObjectDoesNotExist:
        body = {"status": "error", "message": "invalid dev_refence"}
        return HttpResponse(json.dumps(body), content_type="application/json", status=200)

    # Verifico que este en Waiting Callback
    if ph.status == 'W' or (ph.status == 'A' and pr["ph_status"] == 'C'):

        # Seteo los valores de la UserPayment
        ph.user_payment.status  = pr["up_status"]
        ph.user_payment.message = pr["up_message"]
        ph.user_payment.enabled = pr["up_recurrence"]

        if ph.user_payment.status == 'AC':
            # calcular next_payment_day
            ph.user_payment.payment_date = ph.user_payment.calc_payment_date()
            # Fija la fecha de expiration del usuario
            ph.user_payment.user.set_expiration(ph.user_payment.payment_date)
            if ph.user_payment.disc_counter > 0:
                ph.user_payment.disc_counter = ph.user_payment.disc_counter - 1
        else:
            ph.user_payment.channel = 'C'
        ph.user_payment.save()

        # Seteo los valores del PaymentHistory
        ph.status     = pr["ph_status"]
        ph.gateway_id = pr["ph_gatewayid"]
        ph.message    = pr["ph_message"]
        ph.save()

        if pr["user_expire"]:
            ph.user_payment.user.expire()

        if pr["intercom"]["action"]:
            ep = Setting.get_var('intercom_endpoint')
            token = Setting.get_var('intercom_token')
            try:
                intercom = Intercom(ep, token)
                reply = intercom.submitEvent(ph.user_payment.user.user_id, ph.user_payment.user.email,
                                             pr["intercom"]["event"], paymentez_intercom_metadata(data['transaction']))
                if not reply:
                    ph.message = "%s - Intercom error: cannot post the event" % (ph.message)
                    ph.save()
            except Exception as e:
                ph.message = "%s - Intercom error: %s" % (ph.message, str(e))
                ph.save()

    else:
        body = {"status": "error", "message": "ignoring callback: PH status %s" % ph.status}
        return HttpResponse(json.dumps(body), content_type="application/json", status=200)

    body = {'status': 'success', 'message': ''}
    return HttpResponse(json.dumps(body), content_type="application/json", status=200)


@require_http_methods(["POST"])
def callback_paymentez(request):
    # Cargo el json
    try:
        data = json.loads(request.body)
    except Exception:
        body = {"status": "error", "message": "error loading json"}
        return HttpResponse(json.dumps(body), content_type="application/json", status=200)

    # Verifico las key mandatorios del json
    keys = [{'transaction': ['id', 'application_code', 'dev_reference', 'stoken']}, {'user':['id']}]
    json_loader = __validate_json(data, keys)
    if json_loader['status'] == 'error':
        return HttpResponse(json.dumps(json_loader), content_type="application/json", status=200)

    # Verifico
    if data["transaction"]["application_code"] == "HOTG-EC-SERVER":
        print "CALLBACK: %s" % str(data)
        return __callback_paymentez_proc(data, 'ec')
    elif data["transaction"]["application_code"] == "HOTG-MX-SERVER":
        print "CALLBACK: %s" % str(data)
        return __callback_paymentez_proc(data, 'mx')
    else:
        print "CALLBACK_CLIENT: %s" % str(data)
        body = {"status": "error", "message": "ignoring callback: app_code"}
        return HttpResponse(json.dumps(body), content_type="application/json", status=200)

# Callback CommerceGate
@require_http_methods(["POST"])
def callback_commercegate(request):
    try:
        data = request.body
    except Exception:
        body = { 'status': 'error', 'message': 'error loading request' }
        return HttpResponse(json.dumps(body), content_type='application/json', status=200)

    data_array = data.split('#')

    logger.error(data_array)

    data = {}
    data['transaction_type']            = message[0]
    data['transaction_id']              = message[1]
    data['transaction_reference_id']    = message[2]
    data['offer_name']                  = message[3]
    data['offer_id']                    = message[4]
    data['ammount']                     = message[5]
    data['currency']                    = message[6]
    data['user_id']                     = message[7]
    data['user_pw']                     = message[8]
    data['email']                       = message[9]
    data['ip']                          = message[10]
    data['country_iso']                 = message[11]
    data['card_holder']                 = message[12]
    data['customer_id']                 = message[13]
    data['website_id']                  = message[14]

    body = { 'status': 'success', 'message': data }

    logger.info(json.dumps(body))
    return HttpResponse(json.dumps(body), content_type='application/json', status=200)