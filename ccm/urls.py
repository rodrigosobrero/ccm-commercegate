"""ccm URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from payapp.views import create_payment
from payapp.views import payment_discount
from payapp.views import cancel_payment
from payapp.views import change_token_card
from payapp.views import user_status
from payapp.views import get_cards
from payapp.views import get_enabled_card
from payapp.views import change_user_email
from payapp.views import refund
from payapp.views import delete_card

from payapp.api_views import get_user, get_all_users, get_user_payment, get_all_payments, get_payment_history, get_all_payment_history
from payapp.frontend_views import login_view, logout_view, expireuser, activateuser, deleteuserpayment, manual_payment, dashboard, userpayments, paymenthistory, users

from payapp.callback_views import callback_paymentez

urlpatterns = [

    url(r'^admin/', admin.site.urls),
    url(r'^api/v1/set/userpayment', create_payment),
    url(r'^api/v1/set/discount', payment_discount),
    url(r'^api/v1/set/cancel', cancel_payment),
    url(r'^api/v1/set/changecard', change_token_card),
    url(r'^api/v1/set/changeemail', change_user_email),
    url(r'^api/v1/get/deletecard/(?P<token>[\w\-]+)', delete_card),
    url(r'^api/v1/get/userstatus/(?P<user_id>[\w\-]+)', user_status),
    url(r'^api/v1/callback/paymentez/', callback_paymentez),
    url(r'^api/v1/get/cards/(?P<user_id>[\w\-]+)', get_cards),
    url(r'^api/v1/get/enabledcard/(?P<user_id>[\w\-]+)', get_enabled_card),
    url(r'^api/v1/get/refund/(?P<payment_id>[\w\-]+)', refund),

    url(r'^api/v1/api/users/(?P<user_id>[\w\-]+)', get_user),
    url(r'^api/v1/api/users', get_all_users),
    url(r'^api/v1/api/payments/(?P<user_id>[\w\-]+)/(?P<records>[\w\-]+)', get_user_payment),
    url(r'^api/v1/api/payments', get_all_payments),
    url(r'^api/v1/api/paymenthistory/(?P<user_id>[\w\-]+)/(?P<records>[\w\-]+)', get_payment_history),
    url(r'^api/v1/api/paymenthistory', get_all_payment_history),

    url(r'^ui/dashboard/', dashboard, name='dashboard'),

    url(r'^ui/expireuser', expireuser, name='expireuser'),
	url(r'^ui/activateuser', activateuser, name='activateuser'),	
    url(r'^ui/deleteuserpayment', deleteuserpayment, name='deleteuserpayment'),
    url(r'^ui/manualpayment', manual_payment, name='manual_payment'),

    url(r'^ui/login/', login_view, name='login'),
    url(r'^ui/logout/', logout_view, name='logout'),

    url(r'^ui/usuarios/', users, name='users'),
    url(r'^ui/pagos-recurrentes/', userpayments, name='userpayments'),
    url(r'^ui/historial-pagos/', paymenthistory, name='paymenthistory'),
]
