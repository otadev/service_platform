from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from subscriptions.models import Tariff, UserSubscription
from subscriptions.serializers import TariffSerializer, UserSubscriptionSerializer


class TariffViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tariff.objects.all()
    serializer_class = TariffSerializer


class UserSubscriptionViewSet(viewsets.ModelViewSet):
    # queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return UserSubscription.objects.all()
        return UserSubscription.objects.filter(user=self.request.user) #показывать пользователю только его подписки

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save()  # юзер берётся из payload
        else:
            serializer.save(user=self.request.user) #при создании подписки авто постановка user

