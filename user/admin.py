from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Follow, CustomUser
from django.utils.translation import gettext_lazy as _

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user_from', 'user_to', 'created')

class FollowInLine(admin.TabularInline):
    """Для управления подписок"""
    model = Follow
    fk_name = 'user_from'
    extra = 1


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Какие поля отображать в админке
    list_display = ('username', 'email', 'date_of_birth', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_of_birth')

    # Поля для редактирования в форме пользователя
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal Info'), {'fields': ('email', 'date_of_birth', 'photo')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Поля при добавлении нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    search_fields = ('username', 'email')
    ordering = ('email',)
    inlines = [FollowInLine]



