import os
import logging
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from celery import shared_task, signals
from django.core.mail import send_mail
from PIL import Image as PiLImage
from user.models import CustomUser
from .models import Image

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification_email(self, subject, message, recipient_email):
    """
    Отправляет e-mail подписчику.
    """
    send_mail(subject, message, 'eldar00319g@gmail.com', [recipient_email])
    # logger.info(f'Письмо успешно отправлено на {recipient_email}')
    return f'Письмо отправлено на {recipient_email}'


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def post_image(self, image_id, user_id):
    """
    Задание по отправке уведомления о новом посте подписчикам.
    """
    image = Image.objects.get(id=image_id)
    user = CustomUser.objects.prefetch_related('followers').get(id=user_id)

    subject = f'Пользователь {user.username} запостил новую картинку:'
    url = image.get_absolute_url()
    message = f'Ссылка на изображение {image.title}: {settings.SITE_URL}{url}'

    for follower in user.followers.all():
        send_notification_email.delay(subject, message, follower.email)

    # logger.info(f'Уведомления успешно поставлены в очередь для подписчиков пользователя {user}')
    return f'Уведомления поставлены на очередь для изображения: {image}, id: {image.id}'


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def generate_thumbnail(self, image_url):
    """
    Генерирует мини-версию картинки.
    """
    image_path = os.path.join(settings.MEDIA_ROOT, image_url)

    image = PiLImage.open(image_path)
    image.thumbnail((150, 150))

    name, extension = os.path.splitext(image_path)
    thumbnail_path = f'{name}_thumbnail{extension}'
    image.save(thumbnail_path)

    # logger.info(f'Миниатюра успешно создана: {thumbnail_path}')
    return thumbnail_path


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def generate_image_tags(self, image_id, image_url):
    """
    Генерирует теги для изображения
    """
    tags = predict_tags(image_url)
    image = Image.objects.get(id=image_id)
    for tag in tags:
        image.tags.add(tag)
    return tags


@signals.task_failure.connect
def task_failure_handler(sender, task_id, exception, args, kwargs, traceback, einfo, **extras):
    """Обрабатывает ошибки в задачах Celery."""
    logger.error(f"Ошибка в задаче {sender.name} (ID: {task_id}): {exception}")

    # Если ошибка - CustomUser.DoesNotExist, не повторяем задачу
    if isinstance(exception, CustomUser.DoesNotExist):
        return

    # Повторяем задачу, если лимит не исчерпан
    try:
        sender.retry(exc=exception)
        logger.info(f"Повтор задачи {sender.name} (ID: {task_id}) из-за ошибки: {exception}")
    except MaxRetriesExceededError:
        logger.error(f"Достигнут лимит повторов для задачи {sender.name} (ID: {task_id})")


import torch
import torchvision.transforms as transforms
from torchvision import models
import requests


def predict_tags(image_url):
    """
    Функция для предсказания тегов
    Возвращает список наиболее подходящих тегов
    """
    image_path = os.path.join(settings.MEDIA_ROOT, image_url)

    #  Выбираем модель
    model = models.efficientnet_b4(weights=models.EfficientNet_B4_Weights.IMAGENET1K_V1)
    model.eval()  # Переключаем в режим оценки

    # Предобработка изображения
    transform = transforms.Compose([
        transforms.Resize((380, 380)),
        transforms.AutoAugment(transforms.AutoAugmentPolicy.IMAGENET),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # Загружаем изображение
    image = PiLImage.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0)

    # Запуск предсказания
    with torch.no_grad():
        outputs = model(image)

    # Получаем топ-5
    top_count = 5
    probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
    top_probs, top_catids = torch.topk(probabilities, top_count)

    # Загружаем список классов ImageNet
    labels_path = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
    labels = requests.get(labels_path).text.splitlines()

    threshold = 0.08
    tags = [labels[top_catids[i]] for i in range(top_count) if top_probs[i] > threshold]

    if not tags:
        max_index = top_probs.index(max(top_probs))
        tags = [labels[top_catids[max_index]]]

    return tags