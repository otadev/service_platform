from django.urls import reverse
from django.contrib.auth import get_user_model
from subscriptions.models import Tariff, UserSubscription
from rest_framework.test import APIClient, APITestCase
import datetime

User = get_user_model()


class SubscriptionMiddlewareTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.tariff = Tariff.objects.create(
            name='Базовый',
            price=999.00,
            duration_days=30
        )

    def test_user_without_subscription_cannot_access_orders(self):
        """Пользователь без подписки не может обращаться к заказам"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)


    def test_user_with_active_subscription_can_access_orders(self):
        """Пользователь с активной подпиской может обращаться к заказам"""
        UserSubscription.objects.create(
            user=self.user,
            tariff=self.tariff,
            end_date=datetime.date.today() + datetime.timedelta(days=30),
        )
        self.client.login(username='testuser', password='testpass123')
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_user_with_expired_subscription_cannot_access_orders(self):
        """Пользователь с истёкшей подпиской не может обращаться к заказам"""
        sub = UserSubscription.objects.create(
            user=self.user,
            tariff=self.tariff,
            end_date=datetime.date.today() - datetime.timedelta(days=1),
        )

        self.client.login(username='testuser', password='testpass123')
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_tariffs_accessible_without_subscription(self):
        """Тарифы доступны без подписки"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tariff-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_admin_panel_accessible_without_subscription(self):
        """Админка доступна без подписки"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/admin/')
        self.assertNotEqual(response.status_code, 403)