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
from payapp.frontend_views import home, userpayments, users, deleteuserpayment, paymenthistory,expireuser, listusersexpire, userpaymentdesactivated

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

    url(r'^home/', home, name='home'),
    url(r'^userpayments/(?P<user_id>[\w\-]+)', userpayments, name='userpaymentsfilter'),
    url(r'^userpayments/', userpayments, name='userpayments'),

    url(r'^userpaymentdesactivated', userpaymentdesactivated, name='userpaymentdesactivated'),

    url(r'^users', users, name='users'),
    url(r'^expireuser', expireuser, name='expireuser'),
    url(r'^listusersexpire', listusersexpire, name='listusersexpire'),

    url(r'^deleteuserpayment', deleteuserpayment, name='deleteuserpayment'),

    url(r'^paymenthistory/(?P<user_payment_id>[\w\-]+)', paymenthistory, name='paymenthistoryfilter'),
    url(r'^paymenthistory/', paymenthistory, name='paymenthistory'),

]
