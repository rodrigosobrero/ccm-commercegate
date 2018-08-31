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
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# App Models
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from models import User
from models import UserPayment
from models import PaymentHistory

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Misc
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
import json
from django.http import JsonResponse
from datetime import datetime


from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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

STATUS_USER_PAYMENT = (('PE', 'Pending'),
          ('AC', 'Active'),
          ('CA', 'Cancelled'),
          ('ER', 'Error'))

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
        users = User.objects.all()

    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            users = User.objects.filter(Q(user_id__icontains=search)).order_by('-user_id')


    paginator = Paginator(users, LIST_ROWS_DISPLAY)
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    context = {'registros':users, 'search':search }
    return render(request, 'payapp/views/users/list.html', context)





@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def usersactives(request):
    search = ''
    fecha = datetime.today()

    if request.method == 'GET':
        users = User.objects.filter(expiration__gte=fecha)

    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            users = User.objects.filter(Q(user_id__icontains=search)).filter(Q(expiration__gt=fecha) | Q(expiration=None)).order_by('-user_id')


    paginator = Paginator(users, LIST_ROWS_DISPLAY)
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    context = {'registros':users, 'search':search }
    return render(request, 'payapp/views/users/listactives.html', context)






@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def listusersexpire(request):
    search = ''
    fecha = datetime.today()

    if request.method == 'GET':
        users = User.objects.filter(Q(expiration__lt=fecha)| (Q(expiration=None)))

    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            users = User.objects.filter(Q(user_id__icontains=search)).filter(expiration__lt=fecha).order_by('-user_id')

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
                    messages.success(request, 'Usuario Desactivado Correctamente!')

                    return JsonResponse({'message': 'Guardado Correctamente', 'data': fecha}, status=200)
                    #return redirect(users)
                except Exception as e:
                    return JsonResponse({'message': 'Hubo un Error', 'data': e.message},status=500)
        return JsonResponse({ 'message': 'Metodo no permitido', 'data': ''}, status=500)







@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def userpaymentdesactivated(request):
    search = ''
    if request.method == 'GET':
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

        messages.success(request, 'UserPayment Desactivado Correctamente!')

        return redirect(userpayments)




@require_http_methods(["GET","POST"])
@login_required(login_url='login')
def paymenthistory(request,user_payment_id='', user_id=''):
    search = ''
    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            paymenthistories = PaymentHistory.objects.filter(Q(user_payment__user_payment_id__icontains=search) | Q(payment_id__icontains=search)).order_by('-creation_date')

    if request.method == 'GET':
        if user_payment_id != '':
            user_payment     = UserPayment.objects.get(user_payment_id = user_payment_id)
            paymenthistories = PaymentHistory.objects.filter(user_payment = user_payment).order_by('-creation_date')
            search = user_payment_id
        else:
            paymenthistories = PaymentHistory.objects.all().order_by('-creation_date')

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





@require_http_methods(["GET", "POST"])
@login_required(login_url='login')
def userpayments(request, user_id=''):
    # filtrar desde listado de usuario los payment user del usuario
    # quitar payday, status mostrar descripcion, cambiar leyenda boton por desactivar
    order_by = request.GET.get('order_by')
    direction = request.GET.get('direction')
    ordering  = order_by
    if direction == 'desc':
        ordering = '-{}'.format(ordering)



    search = ''
    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            userpayments = UserPayment.objects.filter(Q(user_payment_id__icontains=search) | Q(user__user_id__icontains=search)).order_by('-modification_date')

    if request.method == 'GET':
        #user_id se usa para cuando se accede desde el listado de Users
        if user_id != '':
            try:
                user = User.objects.get(user_id=user_id)
                userpayments = UserPayment.objects.filter(user=user).order_by('-modification_date')
                search = user_id
            except Exception as e:
                messages.success(request, 'No existe el Usuario')
                userpayments = UserPayment.objects.all().order_by('-modification_date')
        else:
            if ordering:
                userpayments = UserPayment.objects.all().order_by(ordering)
            else:
                userpayments = UserPayment.objects.all()

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
            userpayments = UserPayment.objects.filter(
                Q(user_payment_id__icontains=search) | Q(user__user_id__icontains=search)).filter(enabled=True).order_by('-user_id')

    if request.method == 'GET':
        if user_id != '':
            try:
                user = User.objects.get(user_id=user_id)
                userpayments = UserPayment.objects.filter(user=user).filter(enabled=True)
                search = user_id
            except Exception as e:
                messages.success(request, 'No existe el Usuario')
                userpayments = UserPayment.objects.filter(enabled=True)
        else:
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

