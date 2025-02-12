from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from .models import CustomUser
from image.serializers import ImageSerializer
from .common_serializers import CustomUserSerializer


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password')  # Поля, которые нужно указать при создании пользователя

    def validate_email(self, value):
        # Проверяем уникальность email
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError({"email": "Пользователь с таким email уже существует."})
        return value


    def validate_username(self, value):
        # Проверяем уникальность username
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError({"username": "Пользователь с таким username уже существует."})
        return value


class CustomDetailUserSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    is_following = serializers.SerializerMethodField()
    images_views = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'email',
            'date_of_birth', 'photo',
            'is_open_liked_images', 'is_following',
            'images_views', 'images',
        )

        read_only_fields = ('email', 'username')


    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.following.filter(id=obj.id).exists()
        return False

    def get_images_views(self, obj):
        # Получаем количество просмотров из контекста
        return self.context.get('images_views', 0)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.is_superuser:
            representation['admin'] = True
        return representation

