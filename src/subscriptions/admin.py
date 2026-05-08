from django.contrib import admin

from subscriptions.models import Tariff, UserSubscription

admin.site.register(Tariff)
admin.site.register(UserSubscription)

# @admin.register(Tariff)
# class TariffAdmin(admin.ModelAdmin):
#     list_display = ('name', 'price', 'duration_days')
#
# @admin.register(UserSubscription)
# class UserSubscriptionAdmin(admin.ModelAdmin):
#     list_display = ('user', 'tariff', 'start_date', 'end_date', 'is_active')

