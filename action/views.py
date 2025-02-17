from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from image.models import Comment, Image
from user.models import CustomUser
from .filters import ActionFilter
from .serializers import ActionSerializer
from .models import Action


class ActionView(ListAPIView):
    serializer_class = ActionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ActionFilter
    search_fields = ['user__username', 'verb']
    ordering_fields = ['created']

    def get_queryset(self):
        # Исключаем действия, совершённые самим пользователем
        queryset = Action.objects.exclude(user=self.request.user)

        # Получаем ContentType для моделей
        user_ct = ContentType.objects.get_for_model(CustomUser)
        image_ct = ContentType.objects.get_for_model(Image)
        comment_ct = ContentType.objects.get_for_model(Comment)

        # 1. Действия "followed": когда кто-то подписался на текущего пользователя
        q_follow = Q(
            target_ct=user_ct,
            target_id=self.request.user.id,
            verb__iexact='followed'
        )

        # 2. Действия "commented": оставленные комментарии,
        # при этом комментарий должен принадлежать изображению, чей владелец — текущий пользователь
        comment_ids = Comment.objects.filter(image__owner=self.request.user) \
            .values_list('id', flat=True)
        q_comment = Q(
            target_ct=comment_ct,
            target_id__in=list(comment_ids),
            verb__iexact='commented'
        )

        # 3. Действия "liked": лайки под изображениями, принадлежащими текущему пользователю
        image_ids = Image.objects.filter(owner=self.request.user) \
            .values_list('id', flat=True)
        q_like = Q(
            target_ct=image_ct,
            target_id__in=list(image_ids),
            verb__iexact='liked'
        )

        # 4. Действия "posted": когда followings выкладывают фото.
        # То есть, если пользователь, совершающий действие, входит в число пользователей на кого подписан
        # текущий пользователь,
        # а действие имеет verb "posted" и target — изображение
        following_ids = self.request.user.followings.values_list('id', flat=True)
        q_post = Q(
            user_id__in=list(following_ids),
            verb__iexact='posted',
            target_ct=image_ct
        )

        # Объединяем все условия через OR
        queryset = queryset.filter(q_follow | q_comment | q_like | q_post)

        return queryset
