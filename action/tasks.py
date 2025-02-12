import os
import logging
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from celery import shared_task, signals
from .models import Action
from datetime import timedelta
from django.utils.timezone import now

logger = logging.getLogger(__name__)

@shared_task
def delete_old_action():
    """Удаляет старые действия"""
    one_week_ago = now() - timedelta(weeks=1)
    deleted_count, _ = Action.objects.filter(created__lt=one_week_ago).delete()
    return (f"Удалено {deleted_count} старых действий")
