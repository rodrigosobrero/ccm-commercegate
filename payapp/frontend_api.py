from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect

from models import User, UserPayment, PaymentHistory, Setting

import json
import logging

from datetime import timedelta, date, datetime
from intercom import Intercom
from misc import make_payment
from time import mktime

http_POST_OK = 201
http_REQUEST_OK = 200
http_NOT_FOUND = 404
http_BAD_REQUEST = 400
http_UNPROCESSABLE_ENTITY = 422
http_NOT_ALLOWED = 405
http_UNAUTHORIZED = 401
http_PAYMENT_REQUIRED = 402
http_INTERNAL_ERROR = 500
LIST_ROWS_DISPLAY = 20

STATUS_USER_PAYMENT = (('PE', 'Pendiente'),
                       ('AC', 'Activo'),
                       ('CA', 'Cancelado'),
                       ('ER', 'Error'),
                       ('RE', 'Error en recurrencia'))

STATUS_PAYMENT_HISTORY = (('P', 'Processing'),
                          ('W', 'Waiting callback'),
                          ('A', 'Approved'),
                          ('R', 'Rejected'),
                          ('C', 'Cancelled'),
                          ('E', 'Error'))

CHANNEL = (('E', ''),
           ('U', 'User'),
           ('R', 'Reply'),
           ('C', 'Callback'),
           ('T', 'Timeout'),
           ('F', 'Refund'),
           ('X', 'Claxson'))

# Get user by id
@require_http_methods(["GET"])
@login_required(login_url='login')
def get_user(request, user_id):
    try:
        user = User.objects.get(user_id=user_id)
    except ObjectDoesNotExist:
        body = { 'status': 'error', 'message': 'El usuario ' + user_id + ' no existe' }
        return HttpResponse(json.dumps(body), content_type='application/json', status=http_BAD_REQUEST)

    card = user.get_card()

    ret                     = {}
    ret['card']             = card.number
    ret['country']          = user.country.name
    ret['creation_date']    = user.creation_date
    ret['email']            = user.email
    ret['expiration']       = user.expiration
    ret['is_active']        = user.is_active
    ret['user_id']          = user_id

    body = { 'status': 'success', 'value': ret }
    return HttpResponse(json.dumps(body, cls=DjangoJSONEncoder), content_type='application/json', status=http_REQUEST_OK)

# Get all users
@require_http_methods(["GET"])
@login_required(login_url='login')
def get_all_users(request):
    try:
        users = User.objects.all().order_by('-modification_date')
    except ObjectDoesNotExist:
        body = { 'status': 'error', 'message': 'No se puede consultar la lista de usuarios' }
        return HttpResponse(json.dumps(body), content_type='application/json', status=http_BAD_REQUEST)

    value = []

    for user in users:
        card = user.get_card()
        has_recurrence = user.has_recurrence()

        ret = {}
        ret['card']                 = card.number
        ret['country']              = user.country.name
        ret['creation_date']        = user.creation_date
        ret['email']                = user.email
        ret['expiration']           = user.expiration
        ret['has_recurrence']       = has_recurrence
        ret['is_active']            = user.is_active
        ret['modification_date']    = user.modification_date
        ret['user_id']              = user.user_id

        value.append(ret)

    body = { 'status': 'success', 'data': value }
    return HttpResponse(json.dumps(body, cls=DjangoJSONEncoder), content_type='application/json', status=http_REQUEST_OK)

# Get user payment by user id
@require_http_methods(["GET"])
@login_required(login_url='login')
def get_user_payment(request, user_id, records='all'):
    try:
        if records == 'all':
            payments = UserPayment.objects.filter(
                user__user_id=user_id).order_by('-modification_date')
        else:
            payments = UserPayment.objects.filter(
                user__user_id=user_id).order_by('-modification_date')[:records]

        count = UserPayment.objects.filter(user__user_id=user_id).count()
    except ObjectDoesNotExist:
        body = { 'status': 'error', 'message': 'No existen pagos recurrentes para el usuario ' + user_id }
        return HttpResponse(json.dumps(body), content_type='application/json', status=http_BAD_REQUEST)

    value = []

    for payment in payments:
        ret = {}
        ret['amount']               = payment.amount
        ret['channel']              = payment.channel
        ret['creation_date']        = payment.creation_date
        ret['currency']             = payment.currency.name
        ret['disc_counter']         = payment.disc_counter
        ret['disc_pct']             = payment.disc_pct
        ret['enabled']              = payment.enabled
        ret['message']              = payment.message
        ret['modification_date']    = payment.modification_date
        ret['payday']               = payment.payday
        ret['recurrence']           = payment.recurrence
        ret['retries']              = payment.retries
        ret['status']               = payment.status

        value.append(ret)

    body = { 'status': 'success', 'data': value, 'records': count }
    return HttpResponse(json.dumps(body, cls=DjangoJSONEncoder), content_type='application/json', status=http_REQUEST_OK)

# All users payments
@require_http_methods(["GET"])
@login_required(login_url='login')
def get_all_payments(request):
    try:
        payments = UserPayment.objects.all().order_by('-modification_date')
    except ObjectDoesNotExist:
        body = { 'status': 'error', 'message': 'No se puede consultar la lista de pagos recurrentes' }
        return HttpResponse(json.dumps(body), content_type='application/json', status=http_BAD_REQUEST)

    value = []

    for payment in payments:
        ret                         = {}
        ret['amount']               = payment.amount
        ret['channel']              = payment.channel
        ret['country']              = payment.user.country.name
        ret['creation_date']        = payment.creation_date
        ret['currency']             = payment.currency.name
        ret['disc_counter']         = payment.disc_counter
        ret['disc_pct']             = payment.disc_pct
        ret['enabled']              = payment.enabled
        ret['is_active']            = payment.user.is_active
        ret['message']              = payment.message
        ret['modification_date']    = payment.modification_date
        ret['payday']               = payment.payday
        ret['payment_date']         = payment.payment_date
        ret['recurrence']           = payment.recurrence
        ret['retries']              = payment.retries
        ret['status']               = payment.status
        ret['user_payment_id']      = payment.user_payment_id
        ret['user']                 = payment.user.user_id

        value.append(ret)

    body = { 'status': 'success', 'data': value }
    return HttpResponse(json.dumps(body, cls=DjangoJSONEncoder), content_type='application/json', status=http_REQUEST_OK)

# Get payment history by user id
@require_http_methods(["GET"])
@login_required(login_url='login')
def get_payment_history(request, user_id, records='all'):
    try:
        if records == 'all':
            payments = PaymentHistory.objects.filter(
                user_payment__user__user_id=user_id).order_by('-modification_date')
        else:
            payments = PaymentHistory.objects.filter(
                user_payment__user__user_id=user_id).order_by('-modification_date')[:records]

        count = PaymentHistory.objects.filter(
            user_payment__user__user_id=user_id).count()

    except ObjectDoesNotExist:
        body = { 'status': 'error', 'message': 'No existe historial de pagos para el usuario ' + user_id }
        return HttpResponse(json.dumps(body), content_type='application/json', status=http_BAD_REQUEST)

    value = []

    for payment in payments:
        payment.description = ''
        payment.code = ''

        try:
            data = json.loads(payment.message.replace(
                "'", "\"").replace("u\"", "\"").replace("None", "null"))
        except:
            continue
        if 'transaction' in data:
            if 'message' in data['transaction']:
                payment.description = data['transaction']['message']
            if 'authorization_code' in data['transaction']:
                payment.code = data['transaction']['authorization_code']

        ret = {}
        ret['amount']               = payment.amount
        ret['card']                 = payment.card.number
        ret['code']                 = payment.code
        ret['creation_date']        = payment.creation_date
        ret['description']          = payment.description
        ret['disc_pct']             = payment.disc_pct
        ret['gateway_id']           = payment.gateway_id
        ret['integrator']           = payment.integrator.name
        ret['manual']               = payment.manual
        ret['message']              = payment.message
        ret['modification_date']    = payment.modification_date
        ret['payment_id']           = payment.payment_id
        ret['status']               = payment.status
        ret['taxable_amount']       = payment.taxable_amount
        ret['user_payment']         = payment.user_payment.user_payment_id
        ret['user']                 = payment.user_payment.user.user_id
        ret['vat_amount']           = payment.vat_amount

        value.append(ret)

    body = { 'status': 'success', 'data': value, 'records': count }
    return HttpResponse(json.dumps(body, cls=DjangoJSONEncoder), content_type='application/json', status=http_REQUEST_OK)

# Get all payments history
@require_http_methods(["GET"])
@login_required(login_url='login')
def get_all_payment_history(request):
    try:
        payments = PaymentHistory.objects.all().order_by('-modification_date')
    except ObjectDoesNotExist:
        body = { 'status': 'error', 'message': 'No se puede consultar la lista de historial de pagos' }
        return HttpResponse(json.dumps(body), content_type='application/json', status=http_BAD_REQUEST)

    value = []

    for payment in payments:
        payment.description = ''
        payment.code = ''

        try:
            data = json.loads(payment.message.replace(
                "'", "\"").replace("u\"", "\"").replace("None", "null"))
        except:
            continue
        if 'transaction' in data:
            if 'message' in data['transaction']:
                payment.description = data['transaction']['message']
            if 'authorization_code' in data['transaction']:
                payment.code = data['transaction']['authorization_code']

        ret = {}
        ret['amount']               = payment.amount
        ret['card']                 = payment.card.number
        ret['card_id']              = payment.card.card_id
        ret['code']                 = payment.code
        ret['creation_date']        = payment.creation_date
        ret['description']          = payment.description
        ret['disc_pct']             = payment.disc_pct
        ret['gateway_id']           = payment.gateway_id
        ret['integrator']           = payment.integrator.name
        ret['manual']               = payment.manual
        ret['message']              = payment.message
        ret['modification_date']    = payment.modification_date
        ret['payment_id']           = payment.payment_id
        ret['status']               = payment.status
        ret['taxable_amount']       = payment.taxable_amount
        ret['user_payment']         = payment.user_payment.user_payment_id
        ret['user']                 = payment.user_payment.user.user_id
        ret['vat_amount']           = payment.vat_amount

        value.append(ret)

    body = { 'status': 'success', 'data': value }
    return HttpResponse(json.dumps(body, cls=DjangoJSONEncoder), content_type='application/json', status=http_REQUEST_OK)

@require_http_methods(["GET", "POST"])
@login_required(login_url='login')
def expireuser(request):
    if request.is_ajax():
        if request.method == 'GET':
            fecha = datetime.today()

        if request.method == 'POST':
            try:
                json_data       = json.loads(request.body)
                user_id         = json_data['user_id']
                user            = User.objects.get(user_id=user_id)
                fecha           = datetime.today()
                d               = timedelta(days=1)
                fecha          -= d
                user.expiration = fecha
                user.save()

                # Envio envento a intercom
                ep = Setting.get_var('intercom_endpoint')
                token = Setting.get_var('intercom_token')
                try:
                    intercom = Intercom(ep, token)
                    metadata = {"event_description": "usuario expirado por el administrador", "expire_at": str(
                        int(mktime(user.expiration.timetuple())))}
                    reply = intercom.submitEvent(
                        user.user_id, user.email, "user_expired", metadata)
                except Exception as e:
                    pass

                return JsonResponse({'message': 'Guardado correctamente', 'data': fecha}, status=200)
            except Exception as e:
                return JsonResponse({'message': 'Hubo un error', 'data': e.message}, status=500)
    return JsonResponse({'message': 'Metodo no permitido', 'data': ''}, status=500)

@require_http_methods(["POST"])
@login_required(login_url='login')
def activateuser(request):
    if request.is_ajax():
        if request.method == 'POST':
            try:
                json_data   = json.loads(request.body)
                user_id     = json_data['user_id']
                days        = json_data['days']
                user        = User.objects.get(user_id=user_id)

                # Sumar la cantidad de dias a hoy
                date = user.enable_for(days)

                # Envio evento a intercom
                ep = Setting.get_var('intercom_endpoint')
                token = Setting.get_var('intercom_token')

                try:
                    intercom = Intercom(ep, token)
                    metadata = {
                        'event_description': 'usuario activado por el administrador',
                        'expire_at': str(int(mktime(date.timetuple())))
                    }
                    reply = intercom.submitEvent(
                        user.user_id, user.email, 'user_activated', metadata)
                except Exception as e:
                    pass

                return JsonResponse({'message': 'activado correctamente'}, status=200)
            except Exception as e:
                return JsonResponse({'message': 'Hubo un error', 'data': e.message}, status=500)
    return JsonResponse({'message': 'Metodo no permitido', 'data': ''}, status=500)

@require_http_methods(["POST"])
@login_required(login_url='login')
def deleteuserpayment(request):
    if request.is_ajax():
        if request.method == 'POST':
            txtmessage = ''

            try:
                json_data = json.loads(request.body)

                if json_data['txtmessage']:
                    txtmessage = json_data['txtmessage']

                userpayment_id      = json_data['userpayment_id']
                registro            = UserPayment.objects.get(user_payment_id=userpayment_id)
                registro.message    = txtmessage
                registro.enabled    = False
                registro.status     = 'CA'
                registro.channel    = 'X'
                registro.save()

                # Envio envento a intercom
                ep = Setting.get_var('intercom_endpoint')
                token = Setting.get_var('intercom_token')

                try:
                    intercom = Intercom(ep, token)
                    reply = intercom.submitEvent(registro.user.user_id, registro.user.email, "cancelled-sub",
                                                 {"event_description": "recurrencia cancelada por el administrador"})
                    if not reply:
                        registro.message = "Intercom error: cannot post the event"
                        registro.save()
                except Exception as e:
                    registro.message = "Intercom error: %s" % str(e)
                    registro.save()

                return JsonResponse({'message': 'activado correctamente'}, status=200)
            except Exception as e:
                return JsonResponse({'message': 'Hubo un error', 'data': e.message}, status=500)
    return JsonResponse({'message': 'Metodo no permitido', 'data': ''}, status=500)

@require_http_methods(["POST"])
@login_required(login_url='login')
def manual_payment(request):
    if request.is_ajax():
        if request.method == 'POST':
            try:
                json_data = json.loads(request.body)
                userpayment_id = json_data['userpayment_id']
                up = UserPayment.get_by_id(userpayment_id)

                if up is None:
                    return JsonResponse({'message': 'Error al realizar el pago, el usuario no existe'}, status=500)

                if up.user.has_active_recurrence():
                    return JsonResponse({'message': 'Error al realizar el pago: el usuario ya posee una recurrencia activa'}, status=500)

                logging.basicConfig(
                    format='%(asctime)s - manual_payments -[%(levelname)s]: %(message)s', filename=Setting.get_var('log_path'), level=logging.INFO)

                # Cambio a estado Pending
                up.status = 'PE'
                up.save()

                # Obtengo la tarjeta habilitada para el usuario
                card = up.user.get_card()

                if card is None:
                    msg = 'Error al obtener la tarjeta para el usuario'
                    up.error(msg)
                    return JsonResponse({'message': msg}, status=500)

                pay = make_payment(up, card, logging, True)

                if pay:
                    return JsonResponse({'message': 'Pago efectuado correctamente'}, status=200)
                else:
                    return JsonResponse({'message': 'Error al realizar el pago: verificar PaymentHistory'}, status=500)
            except Exception:
                return JsonResponse({'message': 'Hubo un error'}, status=500)
    return JsonResponse({'message': 'metodo no permitido'}, status=500)