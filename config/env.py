"""Environment-backed configuration helpers for ``config.settings``.

Kept in a separate module so the parsing logic can be unit-tested without
importing Django settings (which run at import time and read the real
environment).
"""

import re
from datetime import timedelta

_DURATION_UNITS = {
    "d": "days",
    "h": "hours",
    "m": "minutes",
    "s": "seconds",
}
_DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)\s*([dhms]?)", re.IGNORECASE)


def parse_duration(value):
    """Parse a short duration string into a :class:`datetime.timedelta`.

    Accepts a bare number (seconds) or a number with a single ``d``/``h``/``m``/``s``
    suffix, e.g. ``"4h"``, ``"20h"``, ``"30m"``, ``"90"``.
    """
    text = str(value).strip().lower()
    match = _DURATION_RE.fullmatch(text)
    if not match:
        raise ValueError(f"invalid duration: {value!r}")
    amount, unit = match.group(1), match.group(2) or "s"
    return timedelta(**{_DURATION_UNITS[unit]: float(amount)})


def load_settings(env):
    """Read every project setting from an ``environ.Env`` and return a plain dict.

    ``env`` reads from ``os.environ`` by default; tests inject a mapping via
    ``env.ENVIRON = {...}``.
    """
    return {
        "SECRET_KEY": env.str(
            "SECRET_KEY", default="django-insecure-dev-key-change-me"
        ),
        "DEBUG": env.bool("DEBUG", default=True),
        "BOT_TOKEN": env.str("BOT_TOKEN", default=""),
        "GROUP_CHAT_ID": env.str("GROUP_CHAT_ID", default=""),
        "DB_PATH": env.str("DB_PATH", default="chore.db"),
        "REMINDER_1_DELAY": parse_duration(
            env.str("REMINDER_1_DELAY", default="4h")
        ),
        "REMINDER_2_DELAY": parse_duration(
            env.str("REMINDER_2_DELAY", default="20h")
        ),
        "LOG_RETENTION_DAYS": env.int("LOG_RETENTION_DAYS", default=14),
    }
