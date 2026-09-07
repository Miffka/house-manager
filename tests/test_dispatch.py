"""Task #6 — dispatch routing and /help, /start."""

from unittest.mock import MagicMock

import pytest

import chores.handlers  # noqa: F401  (registers handlers)
from chores.models import Person
from chores.telegram.dispatch import dispatch


def message_update(text, user_id=7, username="alex", update_id=1):
    return {
        "update_id": update_id,
        "message": {
            "message_id": 100,
            "text": text,
            "chat": {"id": -1000, "type": "group"},
            "from": {"id": user_id, "first_name": "Alex", "username": username},
        },
    }


def test_help_and_start_are_registered():
    from chores.telegram.dispatch import _COMMANDS

    assert set(_COMMANDS) >= {"help", "start"}


def test_dispatch_routes_command_to_its_handler(monkeypatch):
    from chores.telegram.dispatch import _COMMANDS

    seen = []
    monkeypatch.setitem(_COMMANDS, "help", lambda u, c: seen.append(u))
    dispatch(message_update("/help"), MagicMock())
    assert len(seen) == 1


def test_help_sends_static_text():
    client = MagicMock()
    dispatch(message_update("/help"), client)
    client.send_message.assert_called_once()
    args, kwargs = client.send_message.call_args
    assert "Chore Manager" in args[1]


@pytest.mark.django_db
def test_start_upserts_person():
    client = MagicMock()

    dispatch(message_update("/start", user_id=555, username="sam"), client)
    person = Person.objects.get(tg_user_id=555)
    assert person.display_name == "sam"

    # a second /start updates the display name, does not duplicate
    dispatch(message_update("/start", user_id=555, username="samwise"), client)
    assert Person.objects.filter(tg_user_id=555).count() == 1
    assert Person.objects.get(tg_user_id=555).display_name == "samwise"


@pytest.mark.django_db
def test_start_handled_via_botname_suffix():
    client = MagicMock()
    dispatch(message_update("/start@chore_bot", user_id=9, username="ann"), client)
    assert Person.objects.filter(tg_user_id=9).exists()


def test_unknown_command_is_ignored():
    client = MagicMock()
    assert dispatch(message_update("/nope"), client) is None
    client.send_message.assert_not_called()
