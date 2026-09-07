"""Route a raw Telegram update dict to a handler.

Handlers register themselves via :func:`command` / :func:`callback` decorators.
``run_bot`` imports :mod:`chores.handlers` once at startup so the registry is
populated before :func:`dispatch` is called.
"""

_COMMANDS = {}
_CALLBACKS = {}


def command(name):
    """Register a handler for ``/name``."""

    def register(fn):
        _COMMANDS[name] = fn
        return fn

    return register


def callback(key):
    """Register a handler for ``callback_query`` data starting ``key:``."""

    def register(fn):
        _CALLBACKS[key] = fn
        return fn

    return register


# --- accessors on the update dict ------------------------------------------


def message_text(update):
    return (update.get("message") or {}).get("text", "") or ""


def sender(update):
    msg = update.get("message") or update.get("callback_query") or {}
    return msg.get("from") or {}


def chat_id(update):
    if "message" in update:
        return update["message"]["chat"]["id"]
    if "callback_query" in update:
        cq = update["callback_query"]
        if cq.get("message"):
            return cq["message"]["chat"]["id"]
    return None


def command_args(update):
    """The text after the command word, stripped. ``""`` when there is none."""
    text = message_text(update)
    parts = text.split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""


def callback_data(update):
    return (update.get("callback_query") or {}).get("data", "") or ""


# --- routing --------------------------------------------------------------


def _command_name(update):
    text = message_text(update)
    if not text.startswith("/"):
        return None
    word = text.split(maxsplit=1)[0]
    return word[1:].split("@", 1)[0]  # strip leading "/" and any "@botname"


def dispatch(update, client):
    """Invoke the matching handler, or return ``None`` if nothing matches."""
    name = _command_name(update)
    if name is not None:
        handler = _COMMANDS.get(name)
        return handler(update, client) if handler else None

    if "callback_query" in update:
        key = callback_data(update).split(":", 1)[0]
        handler = _CALLBACKS.get(key)
        return handler(update, client) if handler else None

    return None
