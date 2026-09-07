"""Recurring templates populate the pool on their interval.

``spawn_due_templates`` is called by ``run_bot`` on every loop pass. State lives
entirely in ``Template.next_due_at`` — nothing to rebuild on startup.
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from chores import texts
from chores.assignment import choose_assignee
from chores.models import Task, TaskSource, TaskState, Template
from chores.telegram.keyboards import task_actions


def spawn_due_templates(client, now=None):
    """Spawn one task per active template that is due, and advance its schedule."""
    now = now or timezone.now()
    due = Template.objects.filter(active=True, next_due_at__lte=now).order_by("id")

    for template in due:
        task = Task.objects.create(
            title=template.title,
            effort=template.effort,
            source=TaskSource.TEMPLATE,
            template=template,
            state=TaskState.OPEN,
        )

        assignee = choose_assignee(now)
        if assignee is not None:
            task.assignee = assignee
        task.next_reminder_at = now + settings.REMINDER_1_DELAY
        task.save(update_fields=["assignee", "next_reminder_at"])

        template.last_spawned_at = now
        template.next_due_at = template.next_due_at + timedelta(
            days=template.interval_days
        )
        # If the template was far overdue, don't spawn a backlog — catch up to now.
        while template.next_due_at <= now:
            template.next_due_at += timedelta(days=template.interval_days)
        template.save(update_fields=["last_spawned_at", "next_due_at"])

        if client is not None:
            client.send_message(
                settings.GROUP_CHAT_ID,
                texts.template_spawned(task),
                reply_markup=task_actions(task),
            )
