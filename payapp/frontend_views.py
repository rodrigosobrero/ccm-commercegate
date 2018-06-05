#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Django
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from datetime import timedelta
from django.db.models import Q

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




#==========================================INTERFAZ HTML==========================================
@require_http_methods(["GET"])
def home(request):
    context = {}
    return render(request, 'payapp/views/default/index.html', context)


@require_http_methods(["GET","POST"])
def users(request):

    search = ''
    if request.method == 'GET':
        users = User.objects.filter(expiration=None)

    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            users = User.objects.filter(Q(user_id__icontains=search)).filter(expiration=None).order_by('-user_id')


    context = {'registros':users, 'search':search }
    return render(request, 'payapp/views/users/list.html', context)



@require_http_methods(["GET","POST"])
def listusersexpire(request):
    search = ''
    fecha = datetime.today()

    if request.method == 'GET':
        users = User.objects.filter(expiration=None)

    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            users = User.objects.filter(Q(user_id__icontains=search)).filter(expiration__gte=fecha).order_by('-user_id')


    context = {'registros':users ,'search':search}
    return render(request, 'payapp/views/users/listexpires.html', context)




@require_http_methods(["GET","POST"])
def expireuser(request):
        if request.is_ajax():
            if request.method == 'POST':
                try:
                    print 'Ingreso'
                    json_data = json.loads(request.body)
                    user_id = json_data['user_id']
                    user = User.objects.get(user_id=user_id)
                    fecha = datetime.today()
                    d = timedelta(days=1)
                    fecha -= d
                    user.expiration = fecha
                    user.save()
                    messages.success(request, 'Usuario Desactivado Correctamente!')

                    return JsonResponse({'message': 'Guardado Correctamente', 'data': fecha}, status=200)
                    #return redirect(users)
                except Exception as e:
                    return JsonResponse({'message': 'Hubo un Error', 'data': e.message},status=500)
        return JsonResponse({ 'message': 'Metodo no permitido', 'data': ''}, status=500)





@require_http_methods(["GET","POST"])
def userpayments(request):
    search = ''
    if request.method == 'GET':
        userpayments = UserPayment.objects.filter(enabled=True)

    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            userpayments = UserPayment.objects.filter(Q(user_payment_id__icontains=search) | Q(user__user_id__icontains=search)).filter(enabled=True).order_by('-user_id')


    context = {'registros':userpayments,'search':search}
    return render(request, 'payapp/views/userpayments/list.html', context)



@require_http_methods(["GET","POST"])
def userpaymentdesactivated(request):
    search = ''
    if request.method == 'GET':
        userpayments = UserPayment.objects.filter(enabled=False)

    if request.method == 'POST':
        if request.POST.has_key('search'):
            search = request.POST['search']
            userpayments = UserPayment.objects.filter(Q(user_payment_id__icontains=search) | Q(user__user_id__icontains=search)).filter(enabled=False).order_by('-user_id')


    context = {'registros':userpayments,'search':search}
    return render(request, 'payapp/views/userpayments/listdesactivated.html', context)



@require_http_methods(["GET","POST"])
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




@require_http_methods(["GET"])
def paymenthistory(request):
    paymenthistories = PaymentHistory.objects.all()
    context = {'registros': paymenthistories}
    return render(request, 'payapp/views/paymentshistory/list.html', context)

#INTERFAZ HTML