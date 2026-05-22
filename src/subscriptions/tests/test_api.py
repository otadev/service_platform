from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from subscriptions.models import Tariff, UserSubscription
from subscriptions.serializers import TariffSerializer
from datetime import date, timedelta

from django.contrib.auth import get_user_model

User = get_user_model()

class TariffApiTestCase(APITestCase):
    def test_get(self):
        tariff_1 = Tariff.objects.create(name="Tariff 1", price=100, duration_days=10)
        tariff_2 = Tariff.objects.create(name="Tariff 2", price=200, duration_days=20)
        url = reverse('tariff-list')
        response = self.client.get(url)
        serializer_data = TariffSerializer([tariff_1, tariff_2], many=True).data

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)


class UserSubscriptionAPITestCase(APITestCase): #базовый класс для создания пользователя и тарифов

    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="admin123")
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.other_user = User.objects.create_user(username="otheruser", password="pass123")

        self.tariff_monthly = Tariff.objects.create(name="Monthly", duration_days=30, price=500)
        self.tariff_annual = Tariff.objects.create(name="Annual", duration_days=365, price=5000)

        self.list_url = reverse("subscription-list")

    def detail_url(self, pk):
        return reverse("subscription-detail", kwargs={"pk": pk})

    def _auth(self, user):
        self.client.force_authenticate(user=user)


class CreateSubscriptionTests(UserSubscriptionAPITestCase): #CREATE  (POST)

    def test_admin_can_create_subscription(self):
        """Администратор создает подписку; дата окончания рассчитывается автоматически."""
        self._auth(self.admin)
        today = date.today()
        payload = {
            "user": self.user.pk,
            "tariff": self.tariff_monthly.pk,
            "price": 500,
            "start_date": str(today),
            "comment": "test comment",
        }
        response = self.client.post(self.list_url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        sub = UserSubscription.objects.get(user=self.user)
        expected_end = today + timedelta(days=self.tariff_monthly.duration_days)
        self.assertEqual(sub.end_date, expected_end)

    def test_end_date_auto_calculated_from_tariff_duration(self):
        """end_date = start_date + tariff.duration_days"""
        self._auth(self.admin)
        start = date(2025, 1, 1)
        payload = {
            "user": self.user.pk,
            "tariff": self.tariff_annual.pk,
            "price": 5000,
            "start_date": str(start),
        }
        self.client.post(self.list_url, payload)

        sub = UserSubscription.objects.get(user=self.user)
        self.assertEqual(sub.end_date, start + timedelta(days=365))

    def test_explicit_end_date_is_preserved_on_create(self):
        """Если при создании явно указана дата end_date, она сохраняется без изменений."""
        self._auth(self.admin)
        start = date.today()
        custom_end = start + timedelta(days=10)
        payload = {
            "user": self.user.pk,
            "tariff": self.tariff_monthly.pk,
            "price": 0,
            "start_date": str(start),
            "end_date": str(custom_end),
        }
        self.client.post(self.list_url, payload)

        sub = UserSubscription.objects.get(user=self.user)
        self.assertEqual(sub.end_date, custom_end)


    def test_unauthenticated_cannot_create(self):
        """Анонимные запросы должны быть отклонены."""
        payload = {"user": self.user.pk, "tariff": self.tariff_monthly.pk}
        response = self.client.post(self.list_url, payload)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_regular_user_cannot_create_for_another_user(self):
        """Обычный юзер всегда создаёт подписку только для себя, даже если передал чужой user."""
        self._auth(self.user)
        payload = {
            "user": self.other_user.pk,  # пытается создать для другого
            "tariff": self.tariff_monthly.pk,
            "price": 0,
        }
        response = self.client.post(self.list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Подписка создалась для self.user, а не для other_user
        sub = UserSubscription.objects.get(user=self.user)
        self.assertFalse(UserSubscription.objects.filter(user=self.other_user).exists())


    def test_duplicate_subscription_for_same_user_rejected(self):
        """OneToOneField — повторная подписка для одного и того же пользователя должна завершиться сбоем."""
        self._auth(self.admin)
        payload = {
            "user": self.user.pk,
            "tariff": self.tariff_monthly.pk,
            "price": 0,
        }
        self.client.post(self.list_url, payload)
        response = self.client.post(self.list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReadSubscriptionTests(UserSubscriptionAPITestCase): #READ  (GET list/detail)

    def setUp(self):
        super().setUp()
        self.sub = UserSubscription.objects.create(
            user=self.user,
            tariff=self.tariff_monthly,
            price=500,
        )

    def test_admin_can_list_all_subscriptions(self):
        self._auth(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_admin_can_retrieve_subscription(self):
        self._auth(self.admin)
        response = self.client.get(self.detail_url(self.sub.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], self.user.pk)

    def test_user_can_retrieve_own_subscription(self):
        self._auth(self.user)
        response = self.client.get(self.detail_url(self.sub.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_see_another_users_subscription(self):
        """У пользователя other_user нет подписки; доступ к подписке этого пользователя должен быть заблокирован."""
        self._auth(self.other_user)
        response = self.client.get(self.detail_url(self.sub.pk))
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )

    def test_response_contains_expected_fields(self):
        self._auth(self.admin)
        response = self.client.get(self.detail_url(self.sub.pk))
        for field in ("user", "tariff", "price", "start_date", "end_date", "comment"):
            self.assertIn(field, response.data)


class UpdateSubscriptionTests(UserSubscriptionAPITestCase): #UPDATE  (PUT / PATCH)

    def setUp(self):
        super().setUp()
        self.sub = UserSubscription.objects.create(
            user=self.user,
            tariff=self.tariff_monthly,
            price=500,
        )

    def test_admin_can_patch_comment(self):
        self._auth(self.admin)
        response = self.client.patch(
            self.detail_url(self.sub.pk), {"comment": "VIP client"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.comment, "VIP client")

    def test_admin_can_change_tariff(self):
        self._auth(self.admin)
        response = self.client.patch(
            self.detail_url(self.sub.pk), {"tariff": self.tariff_annual.pk}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.tariff, self.tariff_annual)

    def test_update_does_not_recalculate_end_date(self):
        """Функция save() автоматически устанавливает значение end_date только при выполнении операции _state.adding; при обновлении этого параметра не следует изменять."""
        self._auth(self.admin)
        original_end = self.sub.end_date
        self.client.patch(self.detail_url(self.sub.pk), {"price": 999})
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.end_date, original_end)

    def test_admin_can_manually_set_end_date_on_update(self):
        self._auth(self.admin)
        new_end = date.today() + timedelta(days=90)
        response = self.client.patch(
            self.detail_url(self.sub.pk), {"end_date": str(new_end)}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.end_date, new_end)

    def test_regular_user_cannot_update_subscription(self):
        self._auth(self.other_user)
        response = self.client.patch(
            self.detail_url(self.sub.pk), {"comment": "hacked"}
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )

    def test_comment_max_length_validation(self):
        self._auth(self.admin)
        response = self.client.patch(
            self.detail_url(self.sub.pk), {"comment": "x" * 101}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteSubscriptionTests(UserSubscriptionAPITestCase): #DELETE

    def setUp(self):
        super().setUp()
        self.sub = UserSubscription.objects.create(
            user=self.user,
            tariff=self.tariff_monthly,
            price=0,
        )

    def test_admin_can_delete_subscription(self):
        self._auth(self.admin)
        response = self.client.delete(self.detail_url(self.sub.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserSubscription.objects.filter(pk=self.sub.pk).exists())

    def test_regular_user_can_delete_subscription(self):
        """Юзер может удалить только свою подписку через get_queryset."""
        self._auth(self.other_user)  # other_user не имеет подписки self.sub
        response = self.client.delete(self.detail_url(self.sub.pk))
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],  # 404 — объект не в queryset
        )

class SubscriptionBusinessLogicTests(UserSubscriptionAPITestCase): #BUSINESS-LOGIC / MODEL BEHAVIOUR

    def test_subscription_is_active_within_dates(self):
        """Helper: проверьте наличие свойства is_active или аннотации, если таковые имеются."""
        sub = UserSubscription.create(
            user=self.user,
            tariff=self.tariff_monthly,
            price=0,
            start_date=date.today() - timedelta(days=5),
        )
        # end_date should be today - 5 + 30 = 25 days from now → still active
        self.assertGreater(sub.end_date, date.today())

    def test_subscription_is_expired_past_end_date(self):
        sub = UserSubscription.objects.create(
            user=self.user,
            tariff=self.tariff_monthly,
            price=0,
            start_date=date.today() - timedelta(days=40),
            end_date=date.today() - timedelta(days=10),  #явно указанная end_date
        )
        self.assertLess(sub.end_date, date.today())

    def test_default_price_is_zero(self):
        sub = UserSubscription.objects.create(
            user=self.user,
            tariff=self.tariff_monthly,
        )
        self.assertEqual(sub.price, 0)

    def test_default_comment_is_empty_string(self):
        sub = UserSubscription.objects.create(
            user=self.user,
            tariff=self.tariff_monthly,
        )
        self.assertEqual(sub.comment, "")

    def test_start_date_defaults_to_today(self):
        sub = UserSubscription.objects.create(
            user=self.user,
            tariff=self.tariff_monthly,
        )
        self.assertEqual(sub.start_date, date.today())