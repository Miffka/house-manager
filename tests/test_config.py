"""Task #2 — configuration module."""

from datetime import timedelta

import environ
import pytest

from config.env import load_settings, parse_duration


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("4h", timedelta(hours=4)),
        ("20h", timedelta(hours=20)),
        ("30m", timedelta(minutes=30)),
        ("45s", timedelta(seconds=45)),
        ("2d", timedelta(days=2)),
        ("90", timedelta(seconds=90)),
        ("1.5h", timedelta(hours=1, minutes=30)),
    ],
)
def test_parse_duration(text, expected):
    assert parse_duration(text) == expected


def test_parse_duration_rejects_garbage():
    with pytest.raises(ValueError):
        parse_duration("later")


def test_values_load_from_supplied_env_mapping():
    env = environ.Env()
    env.ENVIRON = {
        "SECRET_KEY": "s3cr3t",
        "DEBUG": "False",
        "BOT_TOKEN": "123:abc",
        "GROUP_CHAT_ID": "-1001234567890",
        "DB_PATH": "/data/chore.db",
        "REMINDER_1_DELAY": "1h",
        "REMINDER_2_DELAY": "2h",
        "LOG_RETENTION_DAYS": "7",
    }

    cfg = load_settings(env)

    assert cfg["SECRET_KEY"] == "s3cr3t"
    assert cfg["DEBUG"] is False
    assert cfg["BOT_TOKEN"] == "123:abc"
    assert cfg["GROUP_CHAT_ID"] == "-1001234567890"
    assert cfg["DB_PATH"] == "/data/chore.db"
    assert cfg["REMINDER_1_DELAY"] == timedelta(hours=1)
    assert cfg["REMINDER_2_DELAY"] == timedelta(hours=2)
    assert cfg["LOG_RETENTION_DAYS"] == 7


def test_defaults_apply_when_unset():
    env = environ.Env()
    env.ENVIRON = {}

    cfg = load_settings(env)

    assert cfg["DEBUG"] is True
    assert cfg["BOT_TOKEN"] == ""
    assert cfg["GROUP_CHAT_ID"] == ""
    assert cfg["DB_PATH"] == "chore.db"
    assert cfg["REMINDER_1_DELAY"] == timedelta(hours=4)
    assert cfg["REMINDER_2_DELAY"] == timedelta(hours=20)
    assert cfg["LOG_RETENTION_DAYS"] == 14


def test_settings_module_exposes_parsed_values():
    from django.conf import settings

    assert isinstance(settings.REMINDER_1_DELAY, timedelta)
    assert isinstance(settings.REMINDER_2_DELAY, timedelta)
    assert isinstance(settings.LOG_RETENTION_DAYS, int)
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
