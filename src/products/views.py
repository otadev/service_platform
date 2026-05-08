from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from products.models import Order
from products.serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user).select_related(
            'subscription',
            'subscription__tariff'
        ) #показывать пользователю только его подписки

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save()  # юзер берётся из payload
        else:
            serializer.save(user=self.request.user) #при создании подписки авто постановка user
