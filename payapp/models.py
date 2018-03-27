from __future__ import unicode_literals

from django.db import models
from datetime import datetime

# Create your models here.

class Setting(models.Model):
    TYPES = (('I', 'Integer'),
             ('S', 'String'),
             ('F', 'Float'))

    key        = models.CharField(max_length=128, help_text='Configuration key')
    value      = models.CharField(max_length=128, help_text='Configuration value')
    dtype      = models.CharField(max_length=1, choices=TYPES, default='I', help_text='Data type')

    @classmethod
    def get_var(cls,key,cast=True):
        try:
            v = cls.objects.get(key=key)
            if cast:
                return v.cast()
            else:
                return v
        except ObjectDoesNotExist:
            return None

    def cast(self):
        if self.dtype == 'I':
            return int(self.value)
        if self.dtype == 'F':
            return float(self.value)
        if self.dtype == 'S':
            return self.value

    def __unicode__(self):
        return self.key


class Currency(models.Model):
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=3)

    def __unicode__(self):
        return self.name


class Country(models.Model):
    name      = models.CharField(max_length=128)
    code      = models.CharField(max_length=2)
    currency  = models.ForeignKey(Currency)

    def __unicode__(self):
        return self.name


class Integrator(models.Model):
    METHOD = (('TO', 'TOKEN'),
              ('DI', 'DIRECT'))

    name    = models.CharField(max_length=32)
    country = models.ForeignKey(Country)
    method  = models.CharField(max_length=2, choices=METHOD, default='TO')

    def __unicode__(self):
        return self.name


class IntegratorSetting(models.Model):
    TYPES = (('I', 'Integer'),
             ('S', 'String'),
             ('F', 'Float'))

    integrator = models.ForeignKey(Integrator)
    key        = models.CharField(max_length=128, help_text='Configuration key')
    value      = models.CharField(max_length=128, help_text='Configuration value')
    dtype      = models.CharField(max_length=1, choices=TYPES, default='I', help_text='Data type')

    @classmethod
    def get_var(cls,integrator,key,cast=True):
        try:
            i = Integrator.objects.get(name=integrator)
            v = cls.objects.get(integrator=i, key=key)
            if cast:
                return v.cast()
            else:
                return v
        except ObjectDoesNotExist:
            return None

    def cast(self):
        if self.dtype == 'I':
            return int(self.value)
        if self.dtype == 'F':
            return float(self.value)
        if self.dtype == 'S':
            return self.value

    def __unicode__(self):
        return "%s:%s" % (self.integrator.name, self.key)


class User(models.Model):
    user_id       = models.CharField(max_length=128)
    email         = models.CharField(max_length=128)
    country       = models.ForeignKey(Country)
    expiration    = models.DateTimeField(auto_now_add=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.user_id
        
    @classmethod
    def create(cls, user_id, email, country):
        us         = cls()
        us.user_id = user_id
        us.email   = email
        us.country = country        
        us.save()
        return us

class UserPayment(models.Model):
    STATUS = (('PE', 'Pending'),
              ('AC', 'Active'),
              ('CA', 'Cancelled'),
              ('ER', 'Error'))

    user          = models.ForeignKey(User)
    amount        = models.FloatField(default=0)
    currency      = models.ForeignKey(Currency)
    payment_date  = models.DateField(auto_now_add=False, help_text="Next payment date")
    payday        = models.IntegerField(help_text='Payday number')
    recurrence    = models.IntegerField(help_text="Monthly recurrence")
    disc_pct      = models.IntegerField(default=0, help_text="Discount percentage")
    disc_counter  = models.IntegerField(default=0, help_text="Payments with discount remaining")
    status        = models.CharField(max_length=2, choices=STATUS, default='PE', help_text='Payment status')
    message       = models.CharField(max_length=1024, blank=True)
    enabled       = models.BooleanField(default=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s:%s" % (self.user, self.id)
        
    @classmethod
    def create(cls, user, amount, currency, payment_date, payday, recurrence, discount=0, disc_counter=0):
        up              = cls()
        up.user         = user
        up.amount       = amount
        up.currency     = currency
        up.payment_date = datetime.fromtimestamp(int(payment_date))
        up.payday       = payday
        up.recurrence   = recurrence
        up.disc_pct     = discount
        up.disc_counter = disc_counter
        up.status       = 'PE'
        up.enabled      = True
        up.save()
        return up
    
    def discount(self, discount, disc_counter):
        self.disc_pct     = discount
        self.disc_counter = disc_counter
        self.save()
        
    def disable(self):
        self.enabled = False
        self.save()
    
    def enable(self):
        self.enabled = True
        self.save()
    
    def error(self, message=''):
        self.status  = 'ER'
        self.message = message
        self.save()
        

class Card(models.Model):
    user          = models.ForeignKey(User)
    number        = models.CharField(max_length=64, blank=True)
    card_type     = models.CharField(max_length=128, blank=True)
    name          = models.CharField(max_length=128, blank=True)
    expiration    = models.CharField(max_length=6, blank=True, help_text="MMAAAA")
    cvc           = models.CharField(max_length=8, blank=True)
    token         = models.CharField(max_length=256, blank=True)
    integrator    = models.ForeignKey(Integrator)
    enabled       = models.BooleanField(default=False)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s:%s" % (self.user.user_id, self.id)
    
    @classmethod
    def create_with_token(cls, user, token, integrator):
        cd            = cls()
        cd.user       = user
        cd.token      = token
        cd.integrator = integrator
        cd.enabled    = True
        cd.save()
        return cd
    
    def enable(self):
        self.enabled = True
        self.save()
        
    def disable(self):
        self.enabled = False
        self.save()

class PaymentHistory(models.Model):
    card          = models.ForeignKey(Card)
    user_payment  = models.ForeignKey(UserPayment)
    message       = models.CharField(max_length=512, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.id
