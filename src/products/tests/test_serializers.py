from django.test import TestCase
from django.contrib.auth import get_user_model
from subscriptions.models import Tariff, UserSubscription
from products.models import Order
from products.serializers import OrderSerializer
import datetime

User = get_user_model()


class OrderSerializerTest(TestCase):

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

    def test_serializer_contains_expected_fields(self):
        """Сериализатор содержит все нужные поля"""
        serializer = OrderSerializer(instance=self.order)
        fields = set(serializer.data.keys())
        expected = {'id', 'user', 'subscription', 'amount', 'status', 'comment', 'created_at', 'updated_at'}
        self.assertEqual(fields, expected)

    def test_serializer_field_values(self):
        """Значения полей корректны"""
        serializer = OrderSerializer(instance=self.order)
        self.assertEqual(float(serializer.data['amount']), 999.00)
        self.assertEqual(serializer.data['status'], 'pending')
        self.assertEqual(serializer.data['comment'], 'Тестовый заказ')

    def test_serializer_read_only_fields(self):
        """user, created_at, updated_at — только для чтения"""
        data = {
            'user': 999,          # пытаемся подменить юзера
            'amount': 500.00,
            'status': 'paid',
            'comment': 'Попытка'
        }
        serializer = OrderSerializer(instance=self.order, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)  # ← сначала проверяем валидность
        updated_order = serializer.save()
        # user не должен измениться несмотря на то что передали 999
        self.assertEqual(updated_order.user, self.user)

    def test_valid_data(self):
        """Сериализатор валиден с корректными данными"""
        data = {
            'amount': '500.00',
            'status': 'pending',
            'comment': 'Новый заказ'
        }
        serializer = OrderSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_status(self):
        """Недопустимый статус не проходит валидацию"""
        data = {
            'amount': '500.00',
            'status': 'unknown_status',  # ← несуществующий статус
        }
        serializer = OrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)

    def test_invalid_amount(self):
        """Некорректная сумма не проходит валидацию"""
        data = {
            'amount': 'не число',
            'status': 'pending',
        }
        serializer = OrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)

    def test_negative_amount(self):
        """Отрицательная сумма не должна проходить"""
        data = {
            'amount': '-100.00',
            'status': 'pending',
        }
        serializer = OrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)