"""Task #8 — /done, /skip, /snooze and callbacks."""

from unittest.mock import MagicMock

import pytest
from django.utils import timezone

import chores.handlers  # noqa: F401
from chores.models import CompletionLog, Person, Task, TaskState
from chores.telegram.dispatch import dispatch


def cmd(text, user_id=1):
    return {
        "update_id": 1,
        "message": {
            "text": text,
            "chat": {"id": -1000, "type": "group"},
            "from": {"id": user_id, "first_name": "Alex", "username": "alex"},
        },
    }


def cb(data, user_id=1):
    return {
        "update_id": 1,
        "callback_query": {
            "id": "cbq1",
            "data": data,
            "from": {"id": user_id, "first_name": "Alex", "username": "alex"},
            "message": {"chat": {"id": -1000, "type": "group"}},
        },
    }


@pytest.fixture
def person(db):
    return Person.objects.create(tg_user_id=1, display_name="alex")


@pytest.fixture
def open_task(person):
    return Task.objects.create(
        title="dishes",
        effort=2,
        assignee=person,
        state=TaskState.OPEN,
        next_reminder_at=timezone.now(),
    )


@pytest.mark.django_db
def test_done_command_closes_and_logs(open_task, person):
    client = MagicMock()
    dispatch(cmd(f"/done {open_task.id}"), client)

    open_task.refresh_from_db()
    assert open_task.state == TaskState.DONE
    assert open_task.done_at is not None
    assert open_task.next_reminder_at is None
    assert CompletionLog.objects.filter(task=open_task, person=person).count() == 1


@pytest.mark.django_db
def test_done_callback_closes_and_acks(open_task):
    client = MagicMock()
    dispatch(cb(f"done:{open_task.id}"), client)

    open_task.refresh_from_db()
    assert open_task.state == TaskState.DONE
    client.answer_callback_query.assert_called_once_with("cbq1")


@pytest.mark.django_db
def test_done_callback_is_idempotent(open_task, person):
    client = MagicMock()
    dispatch(cb(f"done:{open_task.id}"), client)
    dispatch(cb(f"done:{open_task.id}"), client)
    assert CompletionLog.objects.filter(task=open_task).count() == 1


@pytest.mark.django_db
def test_done_unknown_id(person):
    client = MagicMock()
    dispatch(cmd("/done 999"), client)
    assert not CompletionLog.objects.exists()
    assert "Usage" in client.send_message.call_args[0][1]


@pytest.mark.django_db
def test_skip_sets_state_without_logging(open_task):
    client = MagicMock()
    dispatch(cmd(f"/skip {open_task.id}"), client)

    open_task.refresh_from_db()
    assert open_task.state == TaskState.SKIPPED
    assert open_task.next_reminder_at is None
    assert not CompletionLog.objects.exists()


@pytest.mark.django_db
def test_snooze_command_pushes_reminder(open_task):
    before = timezone.now()
    client = MagicMock()
    dispatch(cmd(f"/snooze {open_task.id} 5"), client)

    open_task.refresh_from_db()
    delta = open_task.next_reminder_at - before
    assert timedelta_hours(delta) == pytest.approx(5, abs=0.05)


@pytest.mark.django_db
def test_snooze_callback_pushes_reminder(open_task):
    client = MagicMock()
    dispatch(cb(f"snooze:{open_task.id}:3"), client)
    open_task.refresh_from_db()
    assert open_task.next_reminder_at > timezone.now()
    client.answer_callback_query.assert_called_once_with("cbq1")


@pytest.mark.django_db
def test_snooze_bad_args(open_task):
    client = MagicMock()
    dispatch(cmd(f"/snooze {open_task.id}"), client)
    assert "Usage" in client.send_message.call_args[0][1]


def timedelta_hours(delta):
    return delta.total_seconds() / 3600
