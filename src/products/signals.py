import httpx
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


def send_telegram_message(telegram_id: int, text: str):
    """Отправляет сообщение пользователю через Telegram API"""
    token = os.getenv('BOT_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        httpx.post(url, json={
            'chat_id': telegram_id,
            'text': text
        })
    except Exception as e:
        print(f"Ошибка отправки Telegram сообщения: {e}")



@receiver(post_save, sender=Order)
def notify_user_new_order(sender, instance, created, **kwargs): #Отправляет уведомление когда создаётся новый заказ

    if not created:
        return  # обновление — ничего не делаем

    telegram_id = instance.user.telegram_id

    if not telegram_id:
        print(f"У пользователя {instance.user.username} нет Telegram ID")
        return

    send_telegram_message(
        telegram_id=telegram_id,
        text='Вам пришёл новый заказ!'
    )