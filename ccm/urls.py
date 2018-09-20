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

from payapp.callback_views import callback_paymentez
from payapp.frontend_views import home, userpayments, users, deleteuserpayment, paymenthistory,\
                                    expireuser, listusersexpire, userpaymentdesactivated, login_view, logout_view,usersactives,userpaymentsactives
from payapp.frontend_views import manual_payment, userpayment_recurring_error, paymenthistory_manual, activateuser

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

    url(r'^ui/home/', home, name='home'),

    #url(r'^ui/userpayments/(?P<user_id>[\w\-]+)', userpayments, name='userpaymentsfilter'),
    url(r'^ui/userpayments/', userpayments, name='userpayments'),
    url(r'^ui/userpaymentsactives/', userpaymentsactives, name='userpaymentsactives'),
    url(r'^ui/userpaymentdesactivated', userpaymentdesactivated, name='userpaymentdesactivated'),
    url(r'^ui/userpaymentrecurringerror', userpayment_recurring_error, name='userpayment_recurring_error'),


    url(r'^ui/users', users, name='users'),
    url(r'^ui/listusersactive', usersactives, name='usersactives'),
    url(r'^ui/listusersexpire', listusersexpire, name='listusersexpire'),

    url(r'^ui/expireuser', expireuser, name='expireuser'),
	url(r'^ui/activateuser', activateuser, name='activateuser'),	
    url(r'^ui/deleteuserpayment', deleteuserpayment, name='deleteuserpayment'),
    url(r'^ui/manualpayment', manual_payment, name='manual_payment'),
    

    url(r'^ui/paymenthistory/(?P<user_payment_id>[\w\-]+)', paymenthistory, name='paymenthistoryfilter'),
    url(r'^ui/paymenthistory/', paymenthistory, name='paymenthistory'),
    url(r'^ui/paymenthistorymanual/', paymenthistory_manual, name='paymenthistory_manual'),

    url(r'^ui/login/', login_view, name='login'),
    url(r'^ui/logout/', logout_view, name='logout'),

]
