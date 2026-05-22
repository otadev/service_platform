from rest_framework import serializers
from subscriptions.models import Tariff, UserSubscription


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = '__all__'

class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = '__all__'

    def create(self, validated_data):
        return UserSubscription.create(**validated_data)
