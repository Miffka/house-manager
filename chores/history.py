"""Completion logging, bounded to the retention window.

Pure ORM logic — no Telegram.
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import CompletionLog


def record_completion(task, person):
    """Log ``person`` completing ``task`` and prune entries past the window.

    Returns the freshly created :class:`~chores.models.CompletionLog`.
    """
    now = timezone.now()
    log = CompletionLog.objects.create(
        task=task,
        person=person,
        effort=task.effort,
        completed_at=now,
    )
    cutoff = now - timedelta(days=settings.LOG_RETENTION_DAYS)
    CompletionLog.objects.filter(completed_at__lt=cutoff).delete()
    return log
