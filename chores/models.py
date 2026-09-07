"""Core tables for the chore pool.

Scheduled behaviour is driven by timestamp columns on these models
(``next_reminder_at``, ``next_due_at``) rather than a job queue.
"""

from django.db import models
from django.utils import timezone


class TaskSource(models.TextChoices):
    MANUAL = "manual", "Manual"
    TEMPLATE = "template", "Template"


class TaskState(models.TextChoices):
    OPEN = "open", "Open"
    DONE = "done", "Done"
    SKIPPED = "skipped", "Skipped"


class Person(models.Model):
    tg_user_id = models.BigIntegerField(unique=True)
    display_name = models.CharField(max_length=150)

    def __str__(self):
        return self.display_name


class Template(models.Model):
    title = models.CharField(max_length=200)
    interval_days = models.PositiveIntegerField()
    effort = models.PositiveSmallIntegerField(default=1)
    active = models.BooleanField(default=True)
    last_spawned_at = models.DateTimeField(null=True, blank=True)
    next_due_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} (every {self.interval_days}d)"


class Task(models.Model):
    title = models.CharField(max_length=200)
    effort = models.PositiveSmallIntegerField(default=1)
    source = models.CharField(
        max_length=16, choices=TaskSource.choices, default=TaskSource.MANUAL
    )
    template = models.ForeignKey(
        Template,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks",
    )
    assignee = models.ForeignKey(
        Person,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks",
    )
    state = models.CharField(
        max_length=16, choices=TaskState.choices, default=TaskState.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField(null=True, blank=True)
    done_at = models.DateTimeField(null=True, blank=True)
    reminder_level = models.PositiveSmallIntegerField(default=0)
    next_reminder_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"#{self.pk} {self.title}"


class CompletionLog(models.Model):
    task = models.ForeignKey(
        Task, null=True, blank=True, on_delete=models.SET_NULL, related_name="completions"
    )
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="completions"
    )
    effort = models.PositiveSmallIntegerField(default=1)
    completed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.person} @ {self.completed_at:%Y-%m-%d}"
