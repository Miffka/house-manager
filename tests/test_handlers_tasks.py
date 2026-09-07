"""Task #7 — /add, /pool, /mine."""

from unittest.mock import MagicMock

import pytest

import chores.handlers  # noqa: F401
from chores.handlers.tasks import parse_title_and_effort
from chores.models import Person, Task, TaskSource, TaskState
from chores.telegram.dispatch import dispatch


def msg(text, user_id=1, username="alex"):
    return {
        "update_id": 1,
        "message": {
            "text": text,
            "chat": {"id": -1000, "type": "group"},
            "from": {"id": user_id, "first_name": "Alex", "username": username},
        },
    }


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("take out bins", ("take out bins", 1)),
        ("take out bins ~2", ("take out bins", 2)),
        ("mow ~ 3", ("mow", 3)),
        ("weird~name ~4", ("weird~name", 4)),
    ],
)
def test_parse_title_and_effort(text, expected):
    assert parse_title_and_effort(text) == expected


@pytest.mark.django_db
def test_add_creates_and_assigns_with_button():
    Person.objects.create(tg_user_id=1, display_name="alex")
    Person.objects.create(tg_user_id=2, display_name="sam")
    client = MagicMock()

    dispatch(msg("/add wash the car ~2"), client)

    task = Task.objects.get()
    assert task.title == "wash the car"
    assert task.effort == 2
    assert task.source == TaskSource.MANUAL
    assert task.assignee is not None
    assert task.next_reminder_at is not None

    _, kwargs = client.send_message.call_args
    buttons = kwargs["reply_markup"]["inline_keyboard"][0]
    assert buttons[0]["callback_data"] == f"done:{task.id}"


@pytest.mark.django_db
def test_add_without_people_reports_and_keeps_task_unassigned():
    client = MagicMock()
    dispatch(msg("/add lonely task"), client)
    assert Task.objects.get().assignee is None
    assert "Nobody has run /start" in client.send_message.call_args[0][1]


@pytest.mark.django_db
def test_add_usage_when_no_args():
    client = MagicMock()
    dispatch(msg("/add"), client)
    assert not Task.objects.exists()
    assert "Usage" in client.send_message.call_args[0][1]


@pytest.mark.django_db
def test_pool_lists_open_tasks_only():
    p = Person.objects.create(tg_user_id=1, display_name="alex")
    Task.objects.create(title="open one", assignee=p, state=TaskState.OPEN)
    Task.objects.create(title="closed one", assignee=p, state=TaskState.DONE)
    client = MagicMock()

    dispatch(msg("/pool"), client)
    body = client.send_message.call_args[0][1]
    assert "open one" in body
    assert "closed one" not in body


@pytest.mark.django_db
def test_mine_only_returns_callers_tasks():
    alex = Person.objects.create(tg_user_id=1, display_name="alex")
    sam = Person.objects.create(tg_user_id=2, display_name="sam")
    Task.objects.create(title="alex task", assignee=alex, state=TaskState.OPEN)
    Task.objects.create(title="sam task", assignee=sam, state=TaskState.OPEN)
    client = MagicMock()

    dispatch(msg("/mine", user_id=1), client)
    body = client.send_message.call_args[0][1]
    assert "alex task" in body
    assert "sam task" not in body


@pytest.mark.django_db
def test_mine_empty_for_unknown_sender():
    client = MagicMock()
    dispatch(msg("/mine", user_id=999), client)
    assert "no open tasks" in client.send_message.call_args[0][1].lower()
