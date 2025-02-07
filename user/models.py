from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint
from django.urls import reverse


class CustomUser(AbstractUser):
    email = models.EmailField(max_length=255, unique=True)
    date_of_birth = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to='users/%Y/%m/%d',
                              blank=True, null=True)
    following = models.ManyToManyField('self',
                                       through='Follow',
                                       related_name='followers',
                                       symmetrical=False,
                                       blank=True)
    is_open_liked_images = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('customuser-detail', args=[self.id])

class Follow(models.Model):
    user_from = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='rel_from_set', on_delete=models.CASCADE)
    user_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='rel_to_set', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['-created'])]
        ordering = ['-created']

    def __str__(self):
        return f'{self.user_from} follows {self.user_to}'