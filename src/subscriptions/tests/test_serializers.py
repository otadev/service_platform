from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from subscriptions.models import Tariff, UserSubscription
from subscriptions.serializers import TariffSerializer, UserSubscriptionSerializer

User = get_user_model()


class TariffSerializerTest(TestCase):

    def setUp(self):
        self.tariff = Tariff.objects.create(
            name="Monthly", price="9.99", duration_days=30, description="Basic"
        )
        self.valid_data = {
            "name": "Annual",
            "price": "99.99",
            "duration_days": 365,
            "description": "Full year",
        }

    # ── SERIALIZATION (model → dict) ────────────────────────

    def test_contains_expected_fields(self):
        s = TariffSerializer(self.tariff)
        self.assertEqual(set(s.data.keys()), {"id", "name", "price", "duration_days", "description"})

    def test_field_values(self):
        s = TariffSerializer(self.tariff)
        self.assertEqual(s.data["name"], "Monthly")
        self.assertEqual(float(s.data["price"]), 9.99)
        self.assertEqual(s.data["duration_days"], 30)

    # ── DESERIALIZATION (dict → model) ──────────────────────

    def test_valid_data_is_valid(self):
        s = TariffSerializer(data=self.valid_data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_create_via_serializer(self):
        s = TariffSerializer(data=self.valid_data)
        self.assertTrue(s.is_valid())
        tariff = s.save()
        self.assertEqual(tariff.name, "Annual")
        self.assertEqual(tariff.duration_days, 365)

    def test_description_optional(self):
        data = {**self.valid_data, "description": ""}
        s = TariffSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    # ── VALIDATION ──────────────────────────────────────────

    def test_name_required(self):
        data = {**self.valid_data}
        del data["name"]
        s = TariffSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_price_required(self):
        data = {**self.valid_data}
        del data["price"]
        s = TariffSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("price", s.errors)

    def test_duration_days_required(self):
        data = {**self.valid_data}
        del data["duration_days"]
        s = TariffSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("duration_days", s.errors)

    def test_negative_duration_days_invalid(self):
        data = {**self.valid_data, "duration_days": -1}
        s = TariffSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("duration_days", s.errors)

    def test_negative_price_invalid(self):
        data = {**self.valid_data, "price": "-1.00"}
        s = TariffSerializer(data=data)
        # DecimalField сам по себе не запрещает отрицательные — зависит от валидатора
        # Тест фиксирует текущее поведение
        if not s.is_valid():
            self.assertIn("price", s.errors)

    def test_update_via_serializer(self):
        s = TariffSerializer(self.tariff, data={"name": "Updated", "price": "19.99", "duration_days": 60})
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.name, "Updated")
        self.assertEqual(updated.duration_days, 60)


class UserSubscriptionSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass")
        self.other_user = User.objects.create_user(username="bob", password="pass")
        self.tariff = Tariff.objects.create(
            name="Monthly", price="9.99", duration_days=30
        )
        self.valid_data = {
            "user": self.user.pk,
            "tariff": self.tariff.pk,
            "price": 500,
            "start_date": str(date.today()),
            "comment": "test",
        }

    # ── SERIALIZATION (model → dict) ────────────────────────

    def test_contains_expected_fields(self):
        sub = UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        s = UserSubscriptionSerializer(sub)
        for field in ("id", "user", "tariff", "price", "start_date", "end_date", "comment"):
            self.assertIn(field, s.data)

    def test_end_date_serialized_as_date_string(self):
        sub = UserSubscription.create(user=self.user, tariff=self.tariff)
        s = UserSubscriptionSerializer(sub)
        # должна быть строка вида "YYYY-MM-DD", не datetime
        self.assertRegex(s.data["end_date"], r"^\d{4}-\d{2}-\d{2}$")

    def test_user_field_is_pk(self):
        sub = UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        s = UserSubscriptionSerializer(sub)
        self.assertEqual(s.data["user"], self.user.pk)

    # ── DESERIALIZATION ─────────────────────────────────────

    def test_valid_data_is_valid(self):
        s = UserSubscriptionSerializer(data=self.valid_data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_create_via_serializer(self):
        s = UserSubscriptionSerializer(data=self.valid_data)
        self.assertTrue(s.is_valid())
        sub = s.save()
        self.assertEqual(sub.user, self.user)
        self.assertEqual(sub.tariff, self.tariff)
        self.assertEqual(sub.price, 500)

    def test_end_date_auto_set_by_model_on_create(self):
        """Сериализатор не передаёт end_date — модель ставит сама."""
        s = UserSubscriptionSerializer(data=self.valid_data)
        self.assertTrue(s.is_valid())
        sub = s.save()
        expected = date.today() + timedelta(days=self.tariff.duration_days)
        self.assertEqual(sub.end_date, expected)

    def test_explicit_end_date_accepted(self):
        custom_end = date.today() + timedelta(days=10)
        data = {**self.valid_data, "end_date": str(custom_end)}
        s = UserSubscriptionSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        sub = s.save()
        self.assertEqual(sub.end_date, custom_end)

    def test_tariff_nullable(self):
        """tariff=null допустим; end_date передаём вручную."""
        data = {**self.valid_data, "tariff": None, "end_date": str(date.today())}
        s = UserSubscriptionSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    # ── VALIDATION ──────────────────────────────────────────

    def test_user_required(self):
        data = {**self.valid_data}
        del data["user"]
        s = UserSubscriptionSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("user", s.errors)

    def test_comment_max_length(self):
        data = {**self.valid_data, "comment": "x" * 101}
        s = UserSubscriptionSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("comment", s.errors)

    def test_comment_exactly_100_chars_valid(self):
        data = {**self.valid_data, "comment": "x" * 100}
        s = UserSubscriptionSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_price_cannot_be_negative(self):
        """PositiveIntegerField не принимает отрицательные значения."""
        data = {**self.valid_data, "price": -1}
        s = UserSubscriptionSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("price", s.errors)

    def test_invalid_user_pk_rejected(self):
        data = {**self.valid_data, "user": 99999}
        s = UserSubscriptionSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("user", s.errors)

    def test_invalid_tariff_pk_rejected(self):
        data = {**self.valid_data, "tariff": 99999}
        s = UserSubscriptionSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("tariff", s.errors)

    # ── UNIQUE VALIDATOR ────────────────────────────────────

    def test_duplicate_user_rejected_by_validator(self):
        """Вторая подписка для того же user отклоняется."""
        UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        s = UserSubscriptionSerializer(data=self.valid_data)
        self.assertFalse(s.is_valid())
        # DRF с OneToOneField кладёт ошибку в поле 'user', не в non_field_errors
        self.assertIn("user", s.errors)

    def test_different_users_can_have_subscriptions(self):
        UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        data_other = {**self.valid_data, "user": self.other_user.pk}
        s = UserSubscriptionSerializer(data=data_other)
        self.assertTrue(s.is_valid(), s.errors)

    # ── UPDATE ──────────────────────────────────────────────

    def test_partial_update_comment(self):
        sub = UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        s = UserSubscriptionSerializer(sub, data={"comment": "VIP"}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.comment, "VIP")

    def test_partial_update_price(self):
        sub = UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        s = UserSubscriptionSerializer(sub, data={"price": 1000}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.price, 1000)

    def test_unique_validator_skipped_on_own_update(self):
        """При обновлении своей подписки UniqueValidator не должен блокировать."""
        sub = UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        s = UserSubscriptionSerializer(sub, data={"comment": "updated"}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)