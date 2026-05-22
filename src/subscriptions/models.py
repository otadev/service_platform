from datetime import timedelta, date

from django.db import models

from config import settings


class Tariff(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.price}$"

class UserSubscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='subscription', on_delete=models.PROTECT)
    tariff = models.ForeignKey(Tariff, related_name='subscription', on_delete=models.PROTECT, null=True)
    price = models.PositiveIntegerField(default=0)
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(blank=True, null=True)
    comment = models.CharField(max_length=100, default='', db_index=True)

    @classmethod
    def create(cls, user, tariff, price=0, comment='', start_date=None, end_date=None):
        if start_date is None:
            start_date = date.today()
        if end_date is None and tariff is not None:
            end_date = start_date + timedelta(days=tariff.duration_days)
        return cls.objects.create(user=user, tariff=tariff, price=price, start_date=start_date, end_date=end_date, comment=comment)


    def __str__(self):
        return f"{self.user.username} - {self.tariff}"
