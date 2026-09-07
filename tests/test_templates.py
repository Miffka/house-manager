"""Task #10 — recurring templates."""

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from django.test import override_settings
from django.utils import timezone

import chores.handlers  # noqa: F401
from chores.handlers.templates import parse_template_add
from chores.models import Person, Task, TaskSource, TaskState, Template
from chores.scheduler import spawn_due_templates
from chores.telegram.dispatch import dispatch

DELAY_1 = timedelta(hours=4)


def cmd(text, user_id=1):
    return {
        "update_id": 1,
        "message": {
            "text": text,
            "chat": {"id": -1000, "type": "group"},
            "from": {"id": user_id, "first_name": "Alex", "username": "alex"},
        },
    }


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("vacuum every 5 days", ("vacuum", 5, 1)),
        ("vacuum every 5 days ~2", ("vacuum", 5, 2)),
        ("water the plants every 1 day", ("water the plants", 1, 1)),
        ("mop every 0 days", None),
        ("nonsense", None),
    ],
)
def test_parse_template_add(text, expected):
    assert parse_template_add(text) == expected


@pytest.mark.django_db
def test_template_add_and_list_and_off():
    client = MagicMock()
    dispatch(cmd("/template_add vacuum every 5 days ~2"), client)

    template = Template.objects.get()
    assert template.interval_days == 5
    assert template.effort == 2
    assert template.active is True

    dispatch(cmd("/templates"), client)
    assert "vacuum" in client.send_message.call_args[0][1]

    dispatch(cmd(f"/template_off {template.id}"), client)
    template.refresh_from_db()
    assert template.active is False


@pytest.mark.django_db
@override_settings(REMINDER_1_DELAY=DELAY_1, GROUP_CHAT_ID="-100")
def test_spawn_due_templates_creates_assigns_and_advances():
    Person.objects.create(tg_user_id=1, display_name="alex")
    Person.objects.create(tg_user_id=2, display_name="sam")
    now = timezone.now()

    template = Template.objects.create(
        title="vacuum",
        interval_days=5,
        effort=2,
        active=True,
        next_due_at=now - timedelta(minutes=1),
    )
    client = MagicMock()

    spawn_due_templates(client, now)

    task = Task.objects.get()
    assert task.source == TaskSource.TEMPLATE
    assert task.template_id == template.id
    assert task.state == TaskState.OPEN
    assert task.assignee is not None
    assert task.next_reminder_at == now + DELAY_1

    template.refresh_from_db()
    assert template.last_spawned_at == now
    assert template.next_due_at == now - timedelta(minutes=1) + timedelta(days=5)
    client.send_message.assert_called_once()


@pytest.mark.django_db
@override_settings(REMINDER_1_DELAY=DELAY_1, GROUP_CHAT_ID="-100")
def test_spawn_skips_inactive_and_not_due():
    now = timezone.now()
    Template.objects.create(
        title="off one", interval_days=3, active=False, next_due_at=now - timedelta(days=1)
    )
    Template.objects.create(
        title="future one", interval_days=3, active=True, next_due_at=now + timedelta(days=1)
    )
    client = MagicMock()

    spawn_due_templates(client, now)
    assert not Task.objects.exists()


@pytest.mark.django_db
@override_settings(REMINDER_1_DELAY=DELAY_1, GROUP_CHAT_ID="-100")
def test_far_overdue_template_does_not_backlog():
    now = timezone.now()
    template = Template.objects.create(
        title="old", interval_days=2, active=True, next_due_at=now - timedelta(days=9)
    )
    client = MagicMock()

    spawn_due_templates(client, now)

    assert Task.objects.count() == 1
    template.refresh_from_db()
    assert template.next_due_at > now
