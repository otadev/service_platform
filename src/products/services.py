from products.models import Order
from products.notifications import send_telegram_message


def create_order(user, **kwargs):
    order = Order.objects.create(user=user, **kwargs)

    telegram_id = user.telegram_id
    if not telegram_id:
        print(f"У пользователя {user.username} нет Telegram ID")
        return order

    send_telegram_message(
        telegram_id=telegram_id,
        text='Вам пришёл новый заказ!'
    )
    return order