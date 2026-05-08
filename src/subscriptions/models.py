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

    def save(self, *args, **kwargs):
        if self._state.adding and not self.end_date: #проверка на объект создается или обновляется
            self.end_date = (self.start_date + timedelta(days=self.tariff.duration_days)) #добавление к дате создания длительность тарифа
        super().save(*args, **kwargs) #сохранение в базе данных


    def __str__(self):
        return f"{self.user.username} - {self.tariff}"
