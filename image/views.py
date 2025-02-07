from django.db.models import When, Case, Value, IntegerField
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import viewsets, mixins
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from action.utils import create_action
from user.serializers import CustomUserSerializer
from .count_views import CountViewsImage
from .permissions  import IsOwnerOrReadOnly
from .models import *
from .serializers import *
from .tasks import post_image, generate_thumbnail, generate_image_tags
from .filters import ImageFilter


class ImageViewSet(viewsets.ModelViewSet):

    queryset = Image.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ImageFilter
    search_fields = ['title', 'category__name', 'tags__name', 'owner__username']
    ordering_fields = ['created', 'updated', 'total_likes']


    def get_serializer_class(self):
        if self.action == 'update' or self.action == 'retrieve':
            return ImageDetailSerializer
        return ImageSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        count = CountViewsImage()
        views = count.incr(instance.id)
        serializer = self.get_serializer(instance,
                                         context={
                                             'request': request,
                                             'views': int(views)
                                         })
        return Response(serializer.data)


    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)
        create_action(self.request.user, 'posted', target=instance)
        post_image.delay(instance.id, self.request.user.id)
        generate_thumbnail.delay(instance.image.name)
        if not instance.tags.exists():
            generate_image_tags.delay(instance.id, instance.image.name)

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def like(self, request, pk):
        """Добавление или удаления лайка у изображения"""
        image = get_object_or_404(Image, id=pk)
        if request.method == 'POST':
            image.users_like.add(request.user)
            create_action(request.user, 'liked', target=image)
            return Response({'detail': 'like добавлен'})
        else:
            image.users_like.remove(request.user)
            return Response({'detail': 'like удален'})

    @action(methods=['get'],
            detail=True)
    def users_like(self, request, pk):
        """Список пользователей, которым понравилось изображение"""
        image = get_object_or_404(Image, id=pk)
        users_like = image.users_like.all()

        followings_ids = request.user.following.values_list('id', flat=True)

        #Сортируем: сначала те, на кого подписан текущий пользователь
        users_like = users_like.annotate(
            is_following=Case(
                When(id__in=followings_ids, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-is_following', 'username')

        serializers = CustomUserSerializer(users_like, many=True, context={'request': request})
        return Response(serializers.data)


class CommentViewSet(mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(image_id=self.kwargs['image_pk'], active=True)

    def perform_create(self, serializer):
        image = get_object_or_404(Image, id=self.kwargs['image_pk'])
        instance = serializer.save(owner=self.request.user, image=image)
        create_action(self.request.user, 'commented', target=instance)












