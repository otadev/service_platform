from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from subscriptions.models import Tariff, UserSubscription
from products.models import Order
import datetime

User = get_user_model()


class OrderAPITest(APITestCase):

    def setUp(self):
        """Создаём тестовые данные перед каждым тестом"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
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

    # ─── Аутентификация ────────────────────────────────────────

    def test_unauthorized_user_cannot_access(self):
        """Неавторизованный пользователь не может получить список заказов"""
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ])

    # ─── GET list ──────────────────────────────────────────────

    def test_user_can_get_own_orders(self):
        """Авторизованный пользователь видит свои заказы"""
        self.client.force_authenticate(user=self.user)
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_user_cannot_see_other_orders(self):
        """Пользователь не видит чужие заказы"""
        Order.objects.create(
            user=self.other_user,
            amount=500.00
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('order-list')
        response = self.client.get(url)
        # видим только свой заказ, не чужой
        self.assertEqual(len(response.data), 1)

    # ─── POST ──────────────────────────────────────────────────

    def test_user_can_create_order(self):
        """Пользователь может создать заказ"""
        self.client.force_authenticate(user=self.user)
        url = reverse('order-list')
        data = {
            'amount': '500.00',
            'comment': 'Новый заказ'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)

    def test_order_user_set_automatically(self):
        """user в заказе ставится автоматически из сессии"""
        self.client.force_authenticate(user=self.user)
        url = reverse('order-list')
        data = {'amount': '500.00'}
        response = self.client.post(url, data)
        self.assertEqual(response.data['user'], self.user.id)

    def test_cannot_create_order_with_negative_amount(self):
        """Нельзя создать заказ с отрицательной суммой"""
        self.client.force_authenticate(user=self.user)
        url = reverse('order-list')
        data = {'amount': '-100.00'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    # ─── GET detail ────────────────────────────────────────────

    def test_user_can_get_own_order_detail(self):
        """Пользователь может получить свой заказ по id"""
        self.client.force_authenticate(user=self.user)
        url = reverse('order-detail', kwargs={'pk': self.order.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['amount']), 999.00)

    def test_user_cannot_get_other_order_detail(self):
        """Пользователь не может получить чужой заказ"""
        other_order = Order.objects.create(
            user=self.other_user,
            amount=500.00
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('order-detail', kwargs={'pk': other_order.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ─── PATCH ─────────────────────────────────────────────────

    def test_user_can_update_own_order(self):
        """Пользователь может обновить свой заказ"""
        self.client.force_authenticate(user=self.user)
        url = reverse('order-detail', kwargs={'pk': self.order.pk})
        data = {'comment': 'Обновлённый комментарий'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.comment, 'Обновлённый комментарий')

    # ─── DELETE ────────────────────────────────────────────────

    def test_user_can_delete_own_order(self):
        """Пользователь может удалить свой заказ"""
        self.client.force_authenticate(user=self.user)
        url = reverse('order-detail', kwargs={'pk': self.order.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Order.objects.count(), 0)

    def test_user_cannot_delete_other_order(self):
        """Пользователь не может удалить чужой заказ"""
        other_order = Order.objects.create(
            user=self.other_user,
            amount=500.00
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('order-detail', kwargs={'pk': other_order.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Order.objects.count(), 2)