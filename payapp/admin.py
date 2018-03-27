from django.contrib import admin
import models

# Register your models here.

@admin.register(models.Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'dtype']

@admin.register(models.Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']

@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'email', 'country', 'expiration', 'creation_date']

@admin.register(models.Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'currency']

@admin.register(models.Integrator)
class IntegratorAdmin(admin.ModelAdmin):
    list_display = ['name', 'country']

@admin.register(models.IntegratorSetting)
class IntegratorSettingAdmin(admin.ModelAdmin):
    list_display = ['integrator', 'key', 'value', 'dtype']

@admin.register(models.UserPayment)
class UserPaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'currency', 'payment_date', 'recurrence', 'status', 'enabled', 'creation_date']

@admin.register(models.Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'integrator', 'enabled', 'creation_date']

@admin.register(models.PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'card', 'user_payment']
