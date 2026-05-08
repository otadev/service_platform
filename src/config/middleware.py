from django.http import JsonResponse
from datetime import date

class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/orders/'): #Срабатывает только на эндпоинтах заказов

            if not request.user.is_authenticated: #Анонимных пропускаем-это обработает permissions
                return self.get_response(request)

            if not self._has_active_subscription(request.user): #Проверка активной подписки
                return JsonResponse({'error': 'Для доступа к заказам у вас нет активной подписки.'}, status=403)
        return self.get_response(request)

    def _has_active_subscription(self, user): #проверка активной подписки
        try:
            sub = user.subscription #related_name='subscription'
            return sub.end_date >= date.today()
        except Exception:
            return False