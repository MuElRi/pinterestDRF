from rest_framework import serializers
from taggit.models import Tag
from taggit.serializers import TagListSerializerField

from .favourites import FavoriteSessionManager
from .models import Image, Comment, Category
from user.common_serializers import CustomUserSerializer


class CommentSerializer(serializers.ModelSerializer):
    owner = CustomUserSerializer()
    image = serializers.HyperlinkedRelatedField(view_name='image-detail', many=False, read_only=True )

    class Meta:
        model = Comment
        exclude = ('active', )

    def __init__(self, *args, **kwargs):
        include_image_url = kwargs.pop('include_image_url', False)
        exclusions = kwargs.pop('exclude', None)
        super().__init__(*args, **kwargs)

        # Если нужно, добавляем поле image
        if not include_image_url:
            self.fields.pop('image', None)

        if exclusions:
            for exclude in exclusions:
                self.fields.pop(exclude, None)


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    tags = TagListSerializerField(required=False)
    category = serializers.SlugRelatedField(queryset=Category.objects.all(), slug_field='name')

    class Meta:
        model = Image
        exclude = ('users_like', 'updated', 'created')
        read_only_fields = ('total_likes', )

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        image = super().create(validated_data)

        # Добавляем теги к изображению
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            image.tags.add(tag)
        return image

    def validate_image(self, value):
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("The image size should not exceed 10MB.")
        return value


class ImageDetailSerializer(serializers.ModelSerializer):
    views = serializers.SerializerMethodField(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    owner = CustomUserSerializer(read_only=True)
    tags = TagListSerializerField(required=False)
    category = serializers.SlugRelatedField(read_only=True, slug_field='name')
    is_like =  serializers.SerializerMethodField(read_only=True)
    is_favorite =  serializers.SerializerMethodField(read_only=True)


    class Meta:
        model = Image
        exclude = ('users_like',)
        read_only_fields = ('total_likes', 'title', 'image', 'tags')

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])

        # Обновление тега
        instance = super().update(instance, validated_data)

        # Обновляем теги
        instance.tags.clear()  # Очищаем текущие теги
        if tags_data:
            for tag_name in tags_data:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                instance.tags.add(tag)

        return instance

    def get_is_like(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.users_like.filter(id=request.user.id).exists()
        return False

    def get_views(self, obj):
        # Получаем количество просмотров из контекста
        return self.context.get('views', 0)

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        session_manager = FavoriteSessionManager(request)
        favorites = session_manager.get_favorites()
        if str(obj.id) in favorites:
            return True
        return False

