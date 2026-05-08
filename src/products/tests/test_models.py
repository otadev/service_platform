from django.test import TestCase
from django.contrib.auth import get_user_model
from subscriptions.models import Tariff, UserSubscription
from products.models import Order
import datetime

User = get_user_model()

class OrderModelTest(TestCase):

    def setUp(self):
        """Создаём тестовые данные перед каждым тестом"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.tariff = Tariff.objects.create(
            name='Базовый',
            price=999.00,
            duration_days=30
        )
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            tariff=self.tariff,
            end_date=datetime.date.today() + datetime.timedelta(days=30)
        )
        self.order = Order.objects.create(
            user=self.user,
            subscription=self.subscription,
            amount=999.00,
            comment='Тестовый заказ'
        )

    def test_order_created(self):
        """Заказ успешно создаётся"""
        self.assertEqual(Order.objects.count(), 1)

    def test_order_default_status(self):
        """Статус по умолчанию — pending"""
        self.assertEqual(self.order.status, Order.Status.PENDING)

    def test_order_str(self):
        """Проверяем строковое представление"""
        result = str(self.order)
        self.assertIn(str(self.order.pk), result)
        self.assertIn(self.user.username, result)
        self.assertIn(str(self.order.amount), result)

    def test_order_belongs_to_user(self):
        """Заказ привязан к правильному пользователю"""
        self.assertEqual(self.order.user, self.user)

    def test_order_linked_to_subscription(self):
        """Заказ привязан к подписке"""
        self.assertEqual(self.order.subscription, self.subscription)

    def test_order_amount(self):
        """Сумма заказа сохраняется корректно"""
        self.assertEqual(float(self.order.amount), 999.00)

    def test_order_without_subscription(self):
        """Заказ можно создать без подписки"""
        order = Order.objects.create(
            user=self.user,
            amount=500.00
        )
        self.assertIsNone(order.subscription)

    def test_order_status_change(self):
        """Статус заказа можно изменить"""
        self.order.status = Order.Status.PAID
        self.order.save()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)

    def test_order_deleted_with_user(self):
        """При удалении пользователя сначала удаляем защищённые связи."""
        # Сначала удаляем подписку (PROTECT не даёт удалить юзера напрямую)
        UserSubscription.objects.filter(user=self.user).delete()
        self.user.delete()
        self.assertFalse(Order.objects.filter(pk=self.order.pk).exists())