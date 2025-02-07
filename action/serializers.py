from rest_framework import serializers
from image.models import Image, Comment
from image.serializers import ImageSerializer, CommentSerializer
from .models import Action
from user.common_serializers import CustomUserSerializer


class ActionSerializer(serializers.ModelSerializer):
    target_object = serializers.SerializerMethodField()
    user = CustomUserSerializer()
    class Meta:
        model = Action
        exclude = ['target_id', 'target_ct']

    def get_target_object(self, obj):
        """Возвращает имя и полный URL целевого объекта"""
        request = self.context.get('request')  # Получаем объект request
        if not obj.target:
            return None

        if isinstance(obj.target, Image):
            return ImageSerializer(obj.target, context={'request': request}).data

        if isinstance(obj.target, Comment):
            return CommentSerializer(
                obj.target,
                context={'request': request},
                include_image_url=True,
                exclude=['owner']
            ).data

        return None

    def to_representation(self, instance):
        # Получаем представление с помощью базового метода
        representation = super().to_representation(instance)

        # Если target_object равно None, удаляем его из представления
        if representation.get('target_object') is None:
            del representation['target_object']

        return representation