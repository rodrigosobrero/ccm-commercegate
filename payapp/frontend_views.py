#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Django
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from django.db.models.functions import Lower
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from datetime import timedelta, date
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core import serializers

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# App Models
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from models import User
from models import UserPayment
from models import PaymentHistory
from models import Setting

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Misc
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
import json
from django.http import JsonResponse
from datetime import datetime
import logging
from misc import make_payment
from intercom import Intercom

from time import mktime

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
http_PAYMENT_REQUIRED     = 402
http_INTERNAL_ERROR       = 500
LIST_ROWS_DISPLAY         = 20

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

#==========================================INTERFAZ HTML==========================================

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            print 'debuglogin_home'
            login(request, user)
            #return redirect(home)
            return redirect(dashboard)
        else:
            messages.warning(request,'Usuario o Contrasenia Incorrecto')

    #return render(request, 'payapp/views/default/login.html', None)
    return render(request, 'login/login.html', None)

def logout_view(request):
    logout(request)
    # Redirect to a success page.
    return redirect(login_view)

@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def expireuser(request):
        if request.is_ajax():
            if request.method == 'GET':
                fecha = datetime.today()
                users = User.objects.filter(Q(expiration__lt=fecha) | Q(expiration=None))

            if request.method == 'POST':
                try:
                    json_data = json.loads(request.body)
                    user_id   = json_data['user_id']
                    user      = User.objects.get(user_id=user_id)
                    fecha     = datetime.today()
                    d         = timedelta(days=1)
                    fecha    -= d
                    user.expiration = fecha
                    user.save()

                    # Envio envento a intercom
                    ep    = Setting.get_var('intercom_endpoint')
                    token = Setting.get_var('intercom_token')
                    try:
                        intercom = Intercom(ep, token)
                        metadata = {"event_description": "usuario expirado por el administrador", "expire_at": str(int(mktime(user.expiration.timetuple())))}
                        reply = intercom.submitEvent(user.user_id, user.email, "user_expired", metadata)
                    except Exception as e:
                        pass

                    messages.success(request, 'Usuario expirado correctamente!')

                    return JsonResponse({'message': 'Guardado Correctamente', 'data': fecha}, status=200)
                    #return redirect(users)
                except Exception as e:
                    return JsonResponse({'message': 'Hubo un Error', 'data': e.message},status=500)
        return JsonResponse({ 'message': 'Metodo no permitido', 'data': ''}, status=500)
		
@require_http_methods(["POST"])
@login_required(login_url='login')
def activateuser(request):
	if request.POST.has_key('days'):
		days = request.POST['days']
	if request.POST.has_key('user_id'):
		user_id = request.POST['user_id']

	user = User.objects.get(user_id=user_id)
	
	# Sumar la cantidad de dias a hoy
	date = user.enable_for(days)
	
	# Envio envento a intercom
	ep    = Setting.get_var('intercom_endpoint')
	token = Setting.get_var('intercom_token')
	try:
		intercom = Intercom(ep, token)
		metadata = {"event_description": "usuario activado por el administrador", "expire_at": str(int(mktime(date.timetuple())))}
		reply = intercom.submitEvent(user.user_id, user.email, "user_activated", metadata)
	except Exception as e:
		pass	
	
	messages.success(request, "Usuario %s activado correctamente!" % user_id)

	return redirect(users)

@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def deleteuserpayment(request):
    if request.method == 'POST':
        txtmessage= ''
        if request.POST.has_key('txtmessage'):
            txtmessage = request.POST['txtmessage']
        if request.POST.has_key('userpayment_id'):
            id = request.POST['userpayment_id']

        registro   = UserPayment.objects.get(id=id)

        registro.message = txtmessage
        registro.enabled = False
        registro.status  = 'CA'
        registro.channel = 'X'
        registro.save()

        # Envio envento a intercom
        ep    = Setting.get_var('intercom_endpoint')
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

        messages.success(request, 'Recurrencia desactivada correctamente!')

        return redirect(request.META['HTTP_REFERER'])

@require_http_methods(["POST"])
@login_required(login_url='login')   
def manual_payment(request):
    if not request.POST.has_key('userpayment_id'):
        msg = 'Error al realizar el pago: contactar al administador.'
        messages.success(request, msg)
        return redirect(userpayments)
    
    up = UserPayment.get_by_id(request.POST['userpayment_id'])
    if up is None:
        msg = 'Error al realizar el pago: %s no existe' % request.POST['userpayment_id']
        messages.warning(request, msg)
        return redirect(userpayments)

    if up.user.has_active_recurrence():
        msg = 'Error al realizar el pago: el usuario ya posee una recurrencia activa.'
        messages.warning(request, msg)
        return redirect(request.META['HTTP_REFERER'])
        
    logging.basicConfig(format   = '%(asctime)s - manual_payments -[%(levelname)s]: %(message)s', filename = Setting.get_var('log_path'), level = logging.INFO)
        
    # Cambio a Pending.
    up.status = 'PE'
    up.save()
    
    # Obtengo la tarjeta habilitada para el usuario
    card = up.user.get_card()
    if card is None:
        msg = "Error al obtener la tarjeta para el usuario %s" % up.user.user_id
        up.error(msg)
        messages.success(request, msg)
        return redirect(userpayments)
    
    pay = make_payment(up, card, logging, True)
    
    if pay:
        msg = 'Pago efectuado correctamente para %s' % up.user.user_id
        messages.success(request, msg)
        return redirect(request.META['HTTP_REFERER'])
    else:
        messages.success(request, 'Error al realizar el pago: verificar PaymentHistory')
        return redirect(request.META['HTTP_REFERER'])

# Dashboard
@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def dashboard(request):
    userpaymentsErrors = UserPayment.objects.filter(status='RE').count()
    userpaymentsAct = UserPayment.objects.filter(status='RE', user__expiration__gt = date.today()).count()
    userpaymentsDes = UserPayment.objects.filter(status='RE', user__expiration__lt = date.today()).count()

    context = { 'title': 'Dashboard', 'userpaymentserrors': userpaymentsErrors, 'userpaymentsact': userpaymentsAct, 'userpaymentsdes': userpaymentsDes }
    return render(request, 'content/dashboard.html', context)

# Pagos recurrentes
@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def userpayments(request):

    context = { 'title': 'Pagos Recurrentes' }
    return render(request, 'content/content.html', context)

# Historial de pagos
@require_http_methods(["GET", "POST"])
@login_required(login_url='login')
def paymenthistory(request):

    context = { 'title': 'Historial de Pagos' }
    return render(request, 'content/content.html', context)

# Usuarios
@require_http_methods(["GET", "POST"])
@login_required(login_url='login')
def users(request):

    context = { 'title': 'Usuarios' }
    return render(request, 'content/content.html', context)