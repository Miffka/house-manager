"""``/templates``, ``/template_add``, ``/template_off``."""

import re

from django.utils import timezone

from chores import texts
from chores.models import Template
from chores.telegram.dispatch import chat_id, command, command_args

_ADD_RE = re.compile(
    r"^(?P<title>.+?)\s+every\s+(?P<n>\d+)\s+days?(?:\s*~\s*(?P<effort>\d+))?\s*$",
    re.IGNORECASE,
)


def parse_template_add(text):
    """``"vacuum every 5 days ~2"`` -> ``("vacuum", 5, 2)`` or ``None``."""
    match = _ADD_RE.match(text.strip())
    if not match:
        return None
    interval = int(match.group("n"))
    if interval < 1:
        return None
    effort = int(match.group("effort")) if match.group("effort") else 1
    return match.group("title").strip(), interval, effort


def _int_arg(raw):
    try:
        return int(raw.strip())
    except (TypeError, ValueError):
        return None


@command("templates")
def templates_command(update, client):
    where = chat_id(update)
    templates = list(Template.objects.order_by("id"))
    if not templates:
        client.send_message(where, texts.NO_TEMPLATES)
        return
    client.send_message(where, texts.template_list(templates))


@command("template_add")
def template_add_command(update, client):
    where = chat_id(update)
    parsed = parse_template_add(command_args(update))
    if parsed is None:
        client.send_message(where, texts.TEMPLATE_ADD_USAGE)
        return
    title, interval, effort = parsed
    template = Template.objects.create(
        title=title,
        interval_days=interval,
        effort=effort,
        active=True,
        next_due_at=timezone.now(),
    )
    client.send_message(where, texts.template_added(template))


@command("template_off")
def template_off_command(update, client):
    where = chat_id(update)
    template_id = _int_arg(command_args(update))
    template = (
        Template.objects.filter(pk=template_id).first()
        if template_id is not None
        else None
    )
    if template is None:
        client.send_message(
            where, texts.TEMPLATE_NOT_FOUND.format(template_id=template_id)
        )
        return
    template.active = False
    template.save(update_fields=["active"])
    client.send_message(where, texts.template_off(template))
