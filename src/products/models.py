from django.db import models

from config import settings
from subscriptions.models import UserSubscription


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'В обработке'
        PAID = 'paid', 'Оплачен'
        CANCELED = 'canceled', 'Отменён'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.CASCADE)
    subscription = models.ForeignKey(UserSubscription, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(choices=Status.choices, default=Status.PENDING, max_length=20)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Заказ #{self.id} - {self.user.username} - {self.amount}$"
