import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from ..models import CustomUser

class GoogleLoginAPIView(APIView):
    """
    Получение Google access_token, регистрация/вход пользователя, возврат JWT.
    """
    def post(self, request, *args, **kwargs):
        access_token = request.data.get("access_token")
        if not access_token:
            return Response({"error": "Access token is required"}, status=400)

        # Запрос данных пользователя от Google
        google_url = "https://www.googleapis.com/oauth2/v1/userinfo?alt=json"
        headers = {"Authorization": f"Bearer {access_token}"}
        google_response = requests.get(google_url, headers=headers)

        if google_response.status_code != 200:
            return Response({"error": "Invalid Google access token"}, status=400)

        user_data = google_response.json()

        # Получение/Создание пользователя
        user, created = CustomUser.objects.get_or_create(
            email=user_data["email"],
            defaults={
                "first_name": user_data.get("given_name", ""),
                "last_name": user_data.get("family_name", ""),
                "username": str(uuid.uuid4()),
            },
        )

        # Генерация JWT токенов
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })





