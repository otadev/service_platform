from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from subscriptions.models import Tariff, UserSubscription

User = get_user_model()


class TariffModelTest(TestCase):

    def setUp(self):
        self.tariff = Tariff.objects.create(
            name="Monthly",
            price="9.99",
            duration_days=30,
            description="Basic plan",
        )

    def test_str(self):
        self.assertEqual(str(self.tariff), "Monthly - 9.99$")

    def test_fields_saved_correctly(self):
        t = Tariff.objects.get(pk=self.tariff.pk)
        self.assertEqual(t.name, "Monthly")
        self.assertEqual(float(t.price), 9.99)
        self.assertEqual(t.duration_days, 30)
        self.assertEqual(t.description, "Basic plan")

    def test_description_optional(self):
        t = Tariff.objects.create(name="Free", price="0.00", duration_days=7)
        self.assertEqual(t.description, "")


class UserSubscriptionModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass")
        self.tariff = Tariff.objects.create(
            name="Monthly", price="9.99", duration_days=30
        )

    #тест CREATE

    def test_end_date_auto_set_on_create(self):
        """end_date = start_date + tariff.duration_days при создании."""
        sub = UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        self.assertEqual(sub.end_date, sub.start_date + timedelta(days=30))

    def test_end_date_not_overwritten_if_provided(self):
        """Явно переданный end_date сохраняется как есть."""
        custom_end = date.today() + timedelta(days=10)
        sub = UserSubscription.objects.create(
            user=self.user, tariff=self.tariff, end_date=custom_end
        )
        self.assertEqual(sub.end_date, custom_end)

    def test_start_date_defaults_to_today(self):
        sub = UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        self.assertEqual(sub.start_date, date.today())

    def test_custom_start_date(self):
        start = date(2025, 1, 1)
        sub = UserSubscription.objects.create(
            user=self.user, tariff=self.tariff, start_date=start
        )
        self.assertEqual(sub.start_date, start)
        self.assertEqual(sub.end_date, date(2025, 1, 31))

    def test_price_defaults_to_zero(self):
        sub = UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        self.assertEqual(sub.price, 0)

    def test_comment_defaults_to_empty_string(self):
        sub = UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        self.assertEqual(sub.comment, "")

    def test_tariff_nullable(self):
        """tariff=null разрешён моделью."""
        sub = UserSubscription.objects.create(
            user=self.user, tariff=None, end_date=date.today()
        )
        self.assertIsNone(sub.tariff)

    #тест UPDATE

    def test_end_date_not_recalculated_on_update(self):
        """При update() save() не трогает end_date (не _state.adding)."""
        sub = UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        original_end = sub.end_date

        sub.price = 999
        sub.save()
        sub.refresh_from_db()

        self.assertEqual(sub.end_date, original_end)

    def test_end_date_can_be_changed_manually_on_update(self):
        sub = UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        new_end = date.today() + timedelta(days=90)
        sub.end_date = new_end
        sub.save()
        sub.refresh_from_db()
        self.assertEqual(sub.end_date, new_end)

    #тест CONSTRAINTS

    def test_one_subscription_per_user(self):
        """OneToOneField — второй объект для того же user бросает IntegrityError."""
        UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        with self.assertRaises(IntegrityError):
            UserSubscription.objects.create(user=self.user, tariff=self.tariff)

    def test_different_users_can_have_subscriptions(self):
        other = User.objects.create_user(username="bob", password="pass")
        sub1 = UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        sub2 = UserSubscription.objects.create(user=other, tariff=self.tariff)
        self.assertNotEqual(sub1.pk, sub2.pk)

    #тест STR

    def test_str(self):
        sub = UserSubscription.objects.create(user=self.user, tariff=self.tariff)
        self.assertEqual(str(sub), f"alice - {self.tariff}")

    #тест на BUSINESS LOGIC

    def test_subscription_active_within_dates(self):
        sub = UserSubscription.objects.create(
            user=self.user,
            tariff=self.tariff,
            start_date=date.today() - timedelta(days=5),
        )
        self.assertGreater(sub.end_date, date.today())

    def test_subscription_expired(self):
        sub = UserSubscription.objects.create(
            user=self.user,
            tariff=self.tariff,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() - timedelta(days=1),
        )
        self.assertLess(sub.end_date, date.today())