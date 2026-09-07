"""Escalating reminders for open tasks.

The level transition is a pure function; :func:`service_due_reminders` is the
ORM-driven scan that ``run_bot`` calls on every loop pass. There is no job
queue — a task's ``next_reminder_at`` column is the only state.
"""

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from chores import texts
from chores.models import Person, Task, TaskState

MAX_LEVEL = 2


def advance_reminder(
    level, assignee_mention, other_mention, task_id, task_title, now, reminder_2_delay
):
    """``(level, ...) -> (new_level, next_reminder_at, message)``.

    * level 0 → 1: gentle nudge, re-armed at ``now + reminder_2_delay``.
    * level 1 → 2: stronger nudge that also mentions the other person, not re-armed.
    * level 2 (or higher): nothing to do.
    """
    if level >= MAX_LEVEL:
        return MAX_LEVEL, None, None
    if level <= 0:
        message = texts.reminder_gentle(assignee_mention, task_id, task_title)
        return 1, now + reminder_2_delay, message
    message = texts.reminder_strong(
        assignee_mention, other_mention, task_id, task_title
    )
    return 2, None, message


def service_due_reminders(client, now=None):
    """Fire every open task whose reminder is due, and re-arm or stop it."""
    now = now or timezone.now()
    people = list(Person.objects.all())

    due = (
        Task.objects.filter(state=TaskState.OPEN)
        .filter(Q(next_reminder_at__isnull=False) & Q(next_reminder_at__lte=now))
        .select_related("assignee")
        .order_by("id")
    )

    for task in due:
        assignee = task.assignee
        if assignee is None:
            task.next_reminder_at = None
            task.save(update_fields=["next_reminder_at"])
            continue

        other = next((p for p in people if p.id != assignee.id), None)
        new_level, next_at, message = advance_reminder(
            task.reminder_level,
            texts.mention(assignee),
            texts.mention(other) if other is not None else None,
            task.id,
            task.title,
            now,
            settings.REMINDER_2_DELAY,
        )
        task.reminder_level = new_level
        task.next_reminder_at = next_at
        task.save(update_fields=["reminder_level", "next_reminder_at"])

        if message and client is not None:
            client.send_message(
                settings.GROUP_CHAT_ID, message, parse_mode="HTML"
            )
