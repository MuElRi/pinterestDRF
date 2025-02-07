from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from taggit.managers import TaggableManager


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['name'])]
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Image(models.Model):
    category = models.ForeignKey(Category,
                                 related_name='products',
                                 on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='images',
                             on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    image = models.ImageField(upload_to='images/%Y/%m/%d')
    description = models.TextField(blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateField(auto_now_add=True)
    users_like = models.ManyToManyField(settings.AUTH_USER_MODEL,
                             related_name='liked_images',
                             blank=True)
    total_likes = models.PositiveIntegerField(default=0)
    tags = TaggableManager(blank=True)

    class Meta:
        indexes = [models.Index(fields=['-created'])]
        ordering = ['-created']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('image-detail', args=[self.id])

    def __str__(self):
        return self.title


class ActivatedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(active=True)

class Comment(models.Model):
    image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    text = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    actived = ActivatedManager()
    objects = models.Manager()

    class Meta:
        ordering = ['-created']
        indexes = [models.Index(fields=['-created'])]

    def get_absolute_url(self):
        return reverse('image-comments-detail', args=[self.id])

    def __str__(self):
        return f'Comment by {self.owner.username} on {self.image.title}]'
