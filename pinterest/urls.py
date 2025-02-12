"""
URL configuration for pinterest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from action.views import ActionView
from image.views import CommentViewSet, ImageViewSet
from user.views import UserViewSet
from user.endpoints.google import GoogleLoginAPIView
from .yasg import urlpatterns as doc_urls

# Основной роутер для изображений и пользователей
router = DefaultRouter()
router.register(r'images', ImageViewSet)
router.register(r'users', UserViewSet)

# Вложенный роутер для комментариев
nested_router = NestedSimpleRouter(router, r'images', lookup='image')
nested_router.register(r'comments', CommentViewSet, basename='image-comments')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('auth/google/', GoogleLoginAPIView.as_view(), name='google_login'),
    path('drf-auth/', include('rest_framework.urls')),
    path('action/', ActionView.as_view(), name='action'),

    *router.urls,
    *nested_router.urls,
]

urlpatterns += doc_urls

from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
