"""``/add``, ``/pool`` and ``/mine``."""

import re

from django.conf import settings
from django.utils import timezone

from chores import texts
from chores.assignment import choose_assignee
from chores.models import Person, Task, TaskSource, TaskState
from chores.telegram.dispatch import chat_id, command, command_args, sender
from chores.telegram.keyboards import task_actions

_EFFORT_RE = re.compile(r"\s*~\s*(\d+)\s*$")


def parse_title_and_effort(text):
    """``"bins ~2"`` -> ``("bins", 2)``; effort defaults to 1."""
    match = _EFFORT_RE.search(text)
    if not match:
        return text.strip(), 1
    return text[: match.start()].strip(), int(match.group(1))


@command("add")
def add_command(update, client):
    where = chat_id(update)
    raw = command_args(update)
    if not raw:
        client.send_message(where, texts.ADD_USAGE)
        return

    title, effort = parse_title_and_effort(raw)
    if not title:
        client.send_message(where, texts.ADD_USAGE)
        return

    task = Task.objects.create(
        title=title,
        effort=effort,
        source=TaskSource.MANUAL,
        state=TaskState.OPEN,
    )

    now = timezone.now()
    assignee = choose_assignee(now)
    if assignee is None:
        client.send_message(where, texts.NO_PEOPLE)
        return

    task.assignee = assignee
    task.next_reminder_at = now + settings.REMINDER_1_DELAY
    task.save(update_fields=["assignee", "next_reminder_at"])

    client.send_message(
        where, texts.task_added(task), reply_markup=task_actions(task)
    )


@command("pool")
def pool_command(update, client):
    where = chat_id(update)
    tasks = list(
        Task.objects.filter(state=TaskState.OPEN)
        .select_related("assignee")
        .order_by("id")
    )
    if not tasks:
        client.send_message(where, texts.POOL_EMPTY)
        return
    client.send_message(where, texts.pool_list(tasks))


@command("mine")
def mine_command(update, client):
    where = chat_id(update)
    tg_id = sender(update).get("id")
    person = Person.objects.filter(tg_user_id=tg_id).first()
    tasks = (
        list(
            Task.objects.filter(state=TaskState.OPEN, assignee=person).order_by("id")
        )
        if person
        else []
    )
    if not tasks:
        client.send_message(where, texts.MINE_EMPTY)
        return
    client.send_message(where, texts.mine_list(tasks))
