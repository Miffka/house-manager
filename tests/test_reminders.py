"""Task #9 — escalating reminders."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from django.test import override_settings
from django.utils import timezone

import chores.handlers  # noqa: F401
from chores.models import Person, Task, TaskState
from chores.reminders import advance_reminder, service_due_reminders

NOW = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
DELAY_2 = timedelta(hours=20)


def test_level_0_gentle_and_rearm():
    level, next_at, message = advance_reminder(
        0, "@alex", "@sam", 3, "dishes", NOW, DELAY_2
    )
    assert level == 1
    assert next_at == NOW + DELAY_2
    assert "@alex" in message
    assert "@sam" not in message


def test_level_1_strong_mentions_other_and_stops():
    level, next_at, message = advance_reminder(
        1, "@alex", "@sam", 3, "dishes", NOW, DELAY_2
    )
    assert level == 2
    assert next_at is None
    assert "@alex" in message and "@sam" in message


def test_level_1_without_other_person():
    level, next_at, message = advance_reminder(
        1, "@alex", None, 3, "dishes", NOW, DELAY_2
    )
    assert level == 2
    assert "nudge them" not in message


def test_level_2_is_terminal():
    assert advance_reminder(2, "@a", "@b", 3, "x", NOW, DELAY_2) == (2, None, None)


@pytest.mark.django_db
@override_settings(REMINDER_2_DELAY=DELAY_2, GROUP_CHAT_ID="-100")
def test_service_due_reminders_fires_and_escalates():
    alex = Person.objects.create(tg_user_id=1, display_name="alex")
    Person.objects.create(tg_user_id=2, display_name="sam")
    now = timezone.now()

    task = Task.objects.create(
        title="dishes",
        assignee=alex,
        state=TaskState.OPEN,
        reminder_level=0,
        next_reminder_at=now - timedelta(minutes=1),
    )
    not_due = Task.objects.create(
        title="later",
        assignee=alex,
        state=TaskState.OPEN,
        next_reminder_at=now + timedelta(hours=5),
    )
    client = MagicMock()

    service_due_reminders(client, now)

    task.refresh_from_db()
    assert task.reminder_level == 1
    assert task.next_reminder_at == now + DELAY_2
    client.send_message.assert_called_once()
    assert client.send_message.call_args.kwargs["parse_mode"] == "HTML"

    not_due.refresh_from_db()
    assert not_due.reminder_level == 0

    # task is due again exactly at its re-armed time -> level 2, no re-arm
    service_due_reminders(client, now + DELAY_2)
    task.refresh_from_db()
    assert task.reminder_level == 2
    assert task.next_reminder_at is None


@pytest.mark.django_db
@override_settings(REMINDER_2_DELAY=DELAY_2, GROUP_CHAT_ID="-100")
def test_service_ignores_done_tasks():
    alex = Person.objects.create(tg_user_id=1, display_name="alex")
    now = timezone.now()
    Task.objects.create(
        title="closed",
        assignee=alex,
        state=TaskState.DONE,
        next_reminder_at=now - timedelta(hours=1),
    )
    client = MagicMock()
    service_due_reminders(client, now)
    client.send_message.assert_not_called()
