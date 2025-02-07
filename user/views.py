from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from action.utils import create_action
from image.count_views import CountViewsImage
from image.tasks import generate_thumbnail
from .models import CustomUser, Follow
from .permissions import IsSelfOrReadOnly, IsSelf
from .serializers import CustomUserSerializer, CustomDetailUserSerializer
from image.models import Comment, Image
from image.serializers import CommentSerializer, ImageSerializer
from rest_framework.filters import SearchFilter, OrderingFilter

class UserViewSet(ListModelMixin,
                  RetrieveModelMixin,
                  UpdateModelMixin,
                  GenericViewSet):

    queryset = CustomUser.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsSelfOrReadOnly]

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['username']

    def get_serializer_class(self):
        if self.action == 'update' or self.action == 'retrieve':
            return CustomDetailUserSerializer
        return CustomUserSerializer

    def retrieve(self, request, *args, **kwargs):
        # Получаем пользователя
        user = self.get_object()
        count = CountViewsImage()
        # Получаем количество просмотров всех изображений пользователя
        images_views = 0
        images = user.images.all()
        for image in images:
            images_views += int(count.get(image.id))

        # Передаем общее количество просмотров в контексте сериализатора
        serializer = self.get_serializer(user, context={'request': request,
                                                        'images_views': images_views})
        return Response(serializer.data)

    def perform_update(self, serializer):
        instance = serializer.save()
        generate_thumbnail.delay(instance.photo.name)

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def follow(self, request, pk=None):
        """Подписка или отписка от пользователя"""
        target_user = get_object_or_404(CustomUser, id=pk)

        if target_user == request.user:
            raise ValidationError("Нельзя подписаться на самого себя")

        if request.method == 'POST':
            return self._follow_user(request.user, target_user)
        else:
            return self._unfollow_user(request.user, target_user)

    @action(methods=['get'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def comments(self, request, pk=None):
        """Возвращает комментарии пользователя,
         оставленные под постами текущего пользователя"""
        target_user = get_object_or_404(CustomUser, id=pk)

        if target_user == request.user:
            comments = Comment.objects.filter(owner=request.user)
            return self._serialize_comments(request, comments)

        comments = Comment.objects.filter(
            image__in = request.user.images.all(),
            owner=target_user).select_related('owner')

        return self._serialize_comments(request, comments)

    @action(methods=['get'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def followings(self, request, pk=None):
        """Возвращает список на кого подписан пользователь"""
        target_user = get_object_or_404(CustomUser, id=pk)
        followings = target_user.following.all()
        serializer = CustomUserSerializer(followings, many=True, context={'request': request})
        return Response(serializer.data)

    @action(methods=['get'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def followers(self, request, pk=None):
        """Возвращает список подписчиков"""
        target_user = get_object_or_404(CustomUser, id=pk)
        followers = target_user.followers.all()
        serializer = CustomUserSerializer(followers, many=True, context={'request': request})
        return Response(serializer.data)

    @action(methods=['get'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def liked_images(self, request, pk=None):
        """Возвращает понравившиеся пользователю изображения"""
        target_user = get_object_or_404(CustomUser, id=pk)
        if (target_user.is_open_liked_images and self._is_mutual_follow(request.user, target_user)
                or target_user==request.user):
            images = target_user.liked_images.all()
            serializer = ImageSerializer(images, many=True, context={'request': request})
            return Response(serializer.data)
        return Response({'detail', 'нет доступа'})

    def _follow_user(self, user, target_user):
        """Создает подписку, если ее нет"""
        _, created = Follow.objects.get_or_create(user_from=user, user_to=target_user)
        create_action(user, "followed", target_user)
        if created:
            return Response({'detail': 'Подписка оформлена'}, status=status.HTTP_201_CREATED)
        return Response({'detail': 'Вы уже подписаны'}, status=status.HTTP_400_BAD_REQUEST)

    def _unfollow_user(self, user, target_user):
        """Удаляет подписку, если она существует."""
        deleted, _ = Follow.objects.filter(user_from=user, user_to=target_user).delete()
        if deleted:
            return Response({"detail": "Подписка удалена."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Вы не были подписаны."}, status=status.HTTP_400_BAD_REQUEST)

    def _is_mutual_follow(self, user1, user2):
        """Проверяет, подписаны ли пользователи друг на друга"""
        return Follow.objects.filter(
                    Q(user_from=user1, user_to=user2)|
                    Q(user_from=user2, user_to=user1)
                ).count() == 2

    def _serialize_comments(self, request, comments):
        serializer = CommentSerializer(comments, many=True, context={'request': request}, include_image_url=True)
        return Response(serializer.data)



