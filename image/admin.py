from django.contrib import admin
from .models import *

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class CommentInLine(admin.TabularInline):
    model = Comment
    extra = 1

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'title', 'slug',
                    'image', 'description',
                    'created')
    prepopulated_fields = {'slug': ('title',)}
    inlines = (CommentInLine,)
