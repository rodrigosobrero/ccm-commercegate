#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Django
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from django.db.models.functions import Lower
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from datetime import timedelta
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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

LOG_FILE = Setting.get_var('log_path')

#==========================================INTERFAZ HTML==========================================

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            print 'debuglogin_home'
            login(request, user)
            return redirect(home)
        else:
            messages.warning(request,'Usuario o Contrasenia Incorrecto')

    return render(request, 'payapp/views/default/login.html', None)





def logout_view(request):
    logout(request)
    # Redirect to a success page.
    return redirect(login_view)


@require_http_methods(["GET"])
@login_required(login_url='login')
def home(request):
    context = {}
    return render(request, 'payapp/views/default/index.html', context)


@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def users(request):
    search = ''
    fecha = datetime.today()

    if request.method == 'GET':
        order_by = request.GET.get('order_by')
        direction = request.GET.get('direction')
        ordering = order_by
        if direction == 'desc':
            ordering = '-{}'.format(ordering)

        if ordering:
            users = User.objects.order_by(ordering)
        else:
            users = User.objects.all().order_by('-id')

    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            users = User.objects.filter(Q(user_id__icontains=search)).order_by('-id')


    paginator = Paginator(users, LIST_ROWS_DISPLAY)
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    context = {'registros':users, 'search':search, 'now':fecha }
    return render(request, 'payapp/views/users/list.html', context)





@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def usersactives(request):
    search = ''
    fecha = datetime.today()

    if request.method == 'GET':
        order_by = request.GET.get('order_by')
        direction = request.GET.get('direction')
        ordering = order_by
        if direction == 'desc':
            ordering = '-{}'.format(ordering)

        if ordering:
            users = User.objects.filter(expiration__gt=fecha).order_by(ordering)
        else:
            users = User.objects.all().filter(expiration__gt=fecha).order_by('-id')



    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            users  = User.objects.filter(Q(user_id__icontains=search)).filter(Q(expiration__gt=fecha)).order_by('-id')


    paginator = Paginator(users, LIST_ROWS_DISPLAY)
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    context = {'registros':users, 'search':search,'now':fecha }
    return render(request, 'payapp/views/users/listactives.html', context)






@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def listusersexpire(request):
    search = ''
    fecha = datetime.today()

    if request.method == 'GET':
        order_by = request.GET.get('order_by')
        direction = request.GET.get('direction')
        ordering = order_by
        if direction == 'desc':
            ordering = '-{}'.format(ordering)

        if ordering:
            users = User.objects.filter(Q(expiration__lte=fecha) | (Q(expiration=None))).order_by(ordering)
        else:
            users = User.objects.filter(Q(expiration__lte=fecha) | (Q(expiration=None))).order_by('-id')



    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            users = User.objects.filter(Q(user_id__icontains=search)).filter(Q(expiration__lte=fecha) | (Q(expiration=None))).order_by('-id')

    paginator = Paginator(users, LIST_ROWS_DISPLAY)
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    context = {'registros':users ,'search':search}
    return render(request, 'payapp/views/users/listexpires.html', context)




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
def paymenthistory(request,user_payment_id='', user_id=''):
    search = ''

    if request.method == 'GET':
        order_by  = request.GET.get('order_by')
        direction = request.GET.get('direction')
        ordering  = order_by
        if direction == 'desc':
            ordering = '-{}'.format(ordering)

        if ordering:
            paymenthistories = PaymentHistory.objects.all().order_by(ordering)
        else:
            paymenthistories = PaymentHistory.objects.all().order_by('-creation_date')

        if user_payment_id != '':
            user_payment = UserPayment.objects.get(user_payment_id=user_payment_id)
            paymenthistories = PaymentHistory.objects.filter(user_payment=user_payment).order_by('-creation_date')
            search = user_payment_id


    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            paymenthistories = PaymentHistory.objects.filter(Q(user_payment__user_payment_id__icontains=search) | Q(payment_id__icontains=search)).order_by('-creation_date')

    for ph in paymenthistories:
        ph.description = ''
        ph.code = ''
        try:
            data = json.loads(ph.message.replace("'","\"").replace("u\"", "\"").replace("None", "null"))
        except:
            continue
        if 'transaction' in data:
            if 'message' in data['transaction']:
                ph.description = data['transaction']['message']
            if 'authorization_code' in data['transaction']:
                ph.code = data['transaction']['authorization_code']
        
        if 'card' in data:
            if 'number' in data['card']:
                ph.card_number = "XXXX-XXXX-XXXX-%s" % data['card']['number']
                        
    registros = paymenthistories
    paginator = Paginator(registros, LIST_ROWS_DISPLAY)
    page = request.GET.get('page')
    try:
        registros = paginator.page(page)
    except PageNotAnInteger:
        registros = paginator.page(1)
    except EmptyPage:
        registros = paginator.page(paginator.num_pages)

    context = {'registros': registros,'search':search, 'status': dict(STATUS_PAYMENT_HISTORY)}
    return render(request, 'payapp/views/paymentshistory/list.html', context)

	
@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def paymenthistory_manual(request, user_payment_id='', user_id=''):
    search = ''


    if request.method == 'GET':
        order_by  = request.GET.get('order_by')
        direction = request.GET.get('direction')
        ordering  = order_by
        if direction == 'desc':
            ordering = '-{}'.format(ordering)

        if ordering:
            paymenthistories = PaymentHistory.objects.filter(manual=True).order_by(ordering)
        else:
            paymenthistories = PaymentHistory.objects.filter(manual=True).order_by('-creation_date')

        if user_payment_id != '':
            user_payment = UserPayment.objects.get(user_payment_id=user_payment_id)
            paymenthistories = PaymentHistory.objects.filter(user_payment=user_payment).order_by('-creation_date')
            search = user_payment_id


    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            paymenthistories = PaymentHistory.objects.filter(Q(user_payment__user_payment_id__icontains=search) | Q(payment_id__icontains=search)).order_by('-creation_date')

    for ph in paymenthistories:
        ph.description = ''
        ph.code = ''
        try:
            data = json.loads(ph.message.replace("'","\"").replace("u\"", "\"").replace("None", "none"))
        except:
            continue
        if 'transaction' in data:
            if 'message' in data['transaction']:
                ph.description = data['transaction']['message']
            if 'authorization_code' in data['transaction']:
                ph.code = data['transaction']['authorization_code']
                
        if 'card' in data:
            if 'number' in data['card']:
                ph.card_number = "XXXX-XXXX-XXXX-%s" % str(data['card']['number'])

    registros = paymenthistories
    paginator = Paginator(registros, LIST_ROWS_DISPLAY)
    page = request.GET.get('page')
    try:
        registros = paginator.page(page)
    except PageNotAnInteger:
        registros = paginator.page(1)
    except EmptyPage:
        registros = paginator.page(paginator.num_pages)

    context = {'registros': registros,'search':search, 'status': dict(STATUS_PAYMENT_HISTORY)}
    return render(request, 'payapp/views/paymentshistory/listmanual.html', context)



@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def userpaymentdesactivated(request):
    search = ''

    if request.method == 'GET':
        order_by = request.GET.get('order_by')
        direction = request.GET.get('direction')
        ordering = order_by
        if direction == 'desc':
            ordering = '-{}'.format(ordering)

        if ordering:
            userpayments = UserPayment.objects.filter(enabled=False).order_by(ordering)
        else:
            userpayments = UserPayment.objects.filter(enabled=False)


    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            userpayments = UserPayment.objects.filter(Q(user_payment_id__icontains=search) | Q(user__user_id__icontains=search)).filter(enabled=False).order_by('-user_id')

    registros = userpayments
    paginator = Paginator(registros, LIST_ROWS_DISPLAY)
    page = request.GET.get('page')
    try:
        registros = paginator.page(page)
    except PageNotAnInteger:
        registros = paginator.page(1)
    except EmptyPage:
        registros = paginator.page(paginator.num_pages)

    context = {'registros':registros,'search':search,'status': dict(STATUS_USER_PAYMENT)}
    return render(request, 'payapp/views/userpayments/listdesactivated.html', context)




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

        return redirect(userpayments)




@require_http_methods(["GET", "POST"])
@login_required(login_url='login')
def userpayments(request):
    # filtrar desde listado de usuario los payment user del usuario
    # quitar payday, status mostrar descripcion, cambiar leyenda boton por desactivar
    fecha = datetime.today()
    search = ''
    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            userpayments = UserPayment.objects.filter(Q(user_payment_id__icontains=search) | Q(user__user_id__icontains=search)).order_by('-modification_date')

    if request.method == 'GET':
        order_by  = request.GET.get('order_by')
        direction = request.GET.get('direction')
        ordering = order_by
        if direction == 'desc':
            ordering = '-{}'.format(ordering)

        #user_id se usa para cuando se accede desde el listado de Users
        if 'user_id' in request.GET:
            user_id = request.GET.get('user_id')
            try:
                user = User.objects.get(user_id=user_id)
                userpayments = UserPayment.objects.filter(user=user).order_by('-modification_date')
                search = user
            except Exception as e:
                messages.success(request, 'No existe el Usuario')
                userpayments = UserPayment.objects.all().order_by('-modification_date')
        
        elif 'userpayment_id' in request.GET:        
            user_payment_id = request.GET.get('userpayment_id')
            userpayments = UserPayment.objects.filter(user_payment_id=user_payment_id).order_by('-modification_date')
            if len(userpayments) > 0:
                search = user_payment_id
            else:
                messages.success(request, 'No existe la recurrencia')
                userpayments = UserPayment.objects.all().order_by('-modification_date')
        else:
            if ordering:
                userpayments = UserPayment.objects.all().order_by(ordering)
            else:
                userpayments = UserPayment.objects.all().order_by('-modification_date')
        
    registros = userpayments
    paginator = Paginator(registros, LIST_ROWS_DISPLAY)
    page = request.GET.get('page')
    try:
        registros = paginator.page(page)
    except PageNotAnInteger:
        registros = paginator.page(1)
    except EmptyPage:
        registros = paginator.page(paginator.num_pages)

    context = {'registros': registros, 'search': search, 'status': dict(STATUS_USER_PAYMENT), 'hoy':fecha}
    return render(request, 'payapp/views/userpayments/list.html', context)




@require_http_methods(["GET", "POST"])
@login_required(login_url='login')
def userpaymentsactives(request, user_id=''):
    # filtrar desde listado de usuario los payment user del usuario
    # quitar payday, status mostrar descripcion, cambiar leyenda boton por desactivar
    search = ''
    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            userpayments = UserPayment.objects.filter(Q(user_payment_id__icontains=search) | Q(user__user_id__icontains=search)).filter(enabled=True).order_by('-user_id')

    if request.method == 'GET':
        order_by = request.GET.get('order_by')
        direction = request.GET.get('direction')
        ordering = order_by
        if direction == 'desc':
            ordering = '-{}'.format(ordering)

        if ordering:
            userpayments = UserPayment.objects.filter(enabled=True).order_by(ordering)
        else:
            userpayments = UserPayment.objects.filter(enabled=True).order_by('-modification_date')

        if user_id != '':
            try:
                user = User.objects.get(user_id=user_id)
                userpayments = UserPayment.objects.filter(user=user).filter(enabled=True)
                search = user_id
            except Exception as e:
                messages.success(request, 'No existe el Usuario')
                userpayments = UserPayment.objects.filter(enabled=True)




    registros = userpayments
    paginator = Paginator(registros, LIST_ROWS_DISPLAY)
    page = request.GET.get('page')
    try:
        registros = paginator.page(page)
    except PageNotAnInteger:
        registros = paginator.page(1)
    except EmptyPage:
        registros = paginator.page(paginator.num_pages)

    context = {'registros': registros, 'search': search, 'status': dict(STATUS_USER_PAYMENT)}
    return render(request, 'payapp/views/userpayments/listactives.html', context)


@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def userpayment_recurring_error(request):
    search = ''

    if request.method == 'GET':
        order_by = request.GET.get('order_by')
        direction = request.GET.get('direction')
        ordering = order_by
        if direction == 'desc':
            ordering = '-{}'.format(ordering)

        if ordering:
            userpayments = UserPayment.objects.filter(status='RE').order_by(ordering)
        else:
            userpayments = UserPayment.objects.filter(status='RE').order_by('-modification_date')


    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            userpayments = UserPayment.objects.filter(Q(user_payment_id__icontains=search) | Q(user__user_id__icontains=search)).filter(enabled=False).order_by('-user_id')

    registros = userpayments
    paginator = Paginator(registros, LIST_ROWS_DISPLAY)
    page = request.GET.get('page')
    try:
        registros = paginator.page(page)
    except PageNotAnInteger:
        registros = paginator.page(1)
    except EmptyPage:
        registros = paginator.page(paginator.num_pages)

    context = {'registros':registros,'search':search,'status': dict(STATUS_USER_PAYMENT)}
    return render(request, 'payapp/views/userpayments/listrecurringerror.html', context)


    
    
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
        messages.success(request, msg)
        return redirect(userpayments)
        
    logging.basicConfig(format   = '%(asctime)s - manual_payments -[%(levelname)s]: %(message)s', filename = LOG_FILE, level = logging.INFO)
        
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
        return redirect(userpayments)
    else:
        messages.success(request, 'Error al realizar el pago: verificar PaymentHistory')
        return redirect(userpayments)
    
    
