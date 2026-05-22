import httpx
import os


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