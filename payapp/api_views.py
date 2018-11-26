from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from models import User, UserPayment, PaymentHistory

import json

http_POST_OK              = 201
http_REQUEST_OK           = 200
http_NOT_FOUND            = 404
http_BAD_REQUEST          = 400
http_UNPROCESSABLE_ENTITY = 422
http_NOT_ALLOWED          = 405
http_UNAUTHORIZED         = 401
http_PAYMENT_REQUIRED     = 402
http_INTERNAL_ERROR       = 500

# Get user by id
@require_http_methods(["GET"])
@login_required(login_url='login')
def get_user(request, user_id):
    try:
        user = User.objects.get(user_id=user_id)
    except ObjectDoesNotExist:
        message = 'user_id not found'
        body = { 'status': 'error', 'message': message }
        return HttpResponse(json.dumps(body), content_type='application/json', status=http_BAD_REQUEST)

    card = user.get_card()

    ret = {}
    ret['card']             = card.number
    ret['country']          = user.country.name
    ret['creation_date']    = user.creation_date
    ret['email']            = user.email
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
        message = ''
        body = { 'status': 'error', 'message': message }
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
        ret['is_active']            = user.is_active
        ret['modification_date']    = user.modification_date
        ret['user_id']              = user.user_id
        ret['has_recurrence']       = has_recurrence

        value.append(ret)    

    body = { 'status': 'success', 'data': value }
    return HttpResponse(json.dumps(body, cls=DjangoJSONEncoder), content_type='application/json', status=http_REQUEST_OK)

# Get user payment by user id
@require_http_methods(["GET"])
@login_required(login_url='login')
def get_user_payment(request, user_id, records = 'all'):
    try:
        if records == 'all':
            payments = UserPayment.objects.filter(user__user_id=user_id).order_by('-modification_date')
        else:
            payments = UserPayment.objects.filter(user__user_id=user_id).order_by('-modification_date')[:records]

        count = UserPayment.objects.filter(user__user_id=user_id).count()
    except ObjectDoesNotExist:
        message = 'user_id not found'
        body = { 'status': 'error', 'message': message }
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
        message = ''
        body = { 'status': 'error', 'message': message }
        return HttpResponse(json.dumps(body), content_type='application/json', status=http_BAD_REQUEST)

    value = []

    for payment in payments:
        ret = {}
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
def get_payment_history(request, user_id, records = 'all'):
    try:
        if records == 'all':
            payments = PaymentHistory.objects.filter(user_payment__user__user_id=user_id).order_by('-modification_date')
        else:
            payments = PaymentHistory.objects.filter(user_payment__user__user_id=user_id).order_by('-modification_date')[:records]

        count = PaymentHistory.objects.filter(user_payment__user__user_id=user_id).count()

    except ObjectDoesNotExist:
        message = ''
        body = { 'status': 'error', 'message': message }
        return HttpResponse(json.dumps(body), content_type='application/json', status=http_BAD_REQUEST)

    value = []

    for payment in payments:
        payment.description = ''
        payment.code = ''

        try:
            data = json.loads(payment.message.replace("'","\"").replace("u\"", "\"").replace("None", "null"))
        except:
            continue
        if 'transaction' in data:
            if 'message' in data['transaction']:
                payment.description = data['transaction']['message']
            if 'authorization_code' in data['transaction']:
                payment.code = data['transaction']['authorization_code']

        ret = {}
        ret['amount']                = payment.amount
        ret['card']                  = payment.card.number
        ret['code']                  = payment.code
        ret['creation_date']         = payment.creation_date
        ret['description']           = payment.description
        ret['disc_pct']              = payment.disc_pct
        ret['gateway_id']            = payment.gateway_id
        ret['integrator']            = payment.integrator.name
        ret['manual']                = payment.manual
        ret['message']               = payment.message
        ret['modification_date']     = payment.modification_date
        ret['payment_id']            = payment.payment_id
        ret['status']                = payment.status
        ret['taxable_amount']        = payment.taxable_amount
        ret['user_payment']          = payment.user_payment.user_payment_id
        ret['user']                  = payment.user_payment.user.user_id
        ret['vat_amount']            = payment.vat_amount

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
        message = ''
        body = { 'status': 'error', 'message': message }
        return HttpResponse(json.dumps(body), content_type='application/json', status=http_BAD_REQUEST)

    value = []

    for payment in payments:
        payment.description = ''
        payment.code = ''

        try:
            data = json.loads(payment.message.replace("'","\"").replace("u\"", "\"").replace("None", "null"))
        except:
            continue
        if 'transaction' in data:
            if 'message' in data['transaction']:
                payment.description = data['transaction']['message']
            if 'authorization_code' in data['transaction']:
                payment.code = data['transaction']['authorization_code']

        ret = {}
        ret['amount']                = payment.amount
        ret['card']                  = payment.card.number
        ret['card_id']               = payment.card.card_id
        ret['code']                  = payment.code 
        ret['creation_date']         = payment.creation_date
        ret['description']           = payment.description
        ret['disc_pct']              = payment.disc_pct
        ret['gateway_id']            = payment.gateway_id
        ret['integrator']            = payment.integrator.name
        ret['manual']                = payment.manual
        ret['message']               = payment.message
        ret['modification_date']     = payment.modification_date
        ret['payment_id']            = payment.payment_id
        ret['status']                = payment.status
        ret['taxable_amount']        = payment.taxable_amount
        ret['user_payment']          = payment.user_payment.user_payment_id
        ret['user']                  = payment.user_payment.user.user_id
        ret['vat_amount']            = payment.vat_amount

        value.append(ret)

    body = { 'status': 'success', 'data': value }
    return HttpResponse(json.dumps(body, cls=DjangoJSONEncoder), content_type='application/json', status=http_REQUEST_OK)