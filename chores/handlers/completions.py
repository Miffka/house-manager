"""``/done``, ``/skip``, ``/snooze`` and their inline-button callbacks."""

from datetime import timedelta

from django.utils import timezone

from chores import texts
from chores.history import record_completion
from chores.models import Person, Task, TaskState
from chores.telegram.dispatch import (
    callback,
    callback_data,
    chat_id,
    command,
    command_args,
    sender,
)


def _person_for(update):
    from_user = sender(update)
    person, _ = Person.objects.get_or_create(
        tg_user_id=from_user["id"],
        defaults={
            "display_name": from_user.get("username")
            or from_user.get("first_name")
            or str(from_user["id"])
        },
    )
    return person


def _int_arg(raw):
    try:
        return int(raw.strip())
    except (TypeError, ValueError):
        return None


def _load_task(task_id):
    return Task.objects.filter(pk=task_id).first() if task_id is not None else None


def _ack(client, update):
    cq = update.get("callback_query")
    if cq:
        client.answer_callback_query(cq["id"])


# --- done ---------------------------------------------------------------


def _complete(task, person):
    task.state = TaskState.DONE
    task.done_at = timezone.now()
    task.next_reminder_at = None
    task.save(update_fields=["state", "done_at", "next_reminder_at"])
    record_completion(task, person)


@command("done")
def done_command(update, client):
    where = chat_id(update)
    task = _load_task(_int_arg(command_args(update)))
    if task is None:
        client.send_message(where, texts.NEED_ID.format(command="done"))
        return
    _complete(task, _person_for(update))
    client.send_message(where, texts.task_done(task))


@callback("done")
def done_callback(update, client):
    _, _, task_id = callback_data(update).partition(":")
    task = _load_task(_int_arg(task_id))
    _ack(client, update)
    if task is None:
        return
    if task.state != TaskState.DONE:
        _complete(task, _person_for(update))
    client.send_message(chat_id(update), texts.task_done(task))


# --- skip -------------------------------------------------------------


@command("skip")
def skip_command(update, client):
    where = chat_id(update)
    task = _load_task(_int_arg(command_args(update)))
    if task is None:
        client.send_message(where, texts.NEED_ID.format(command="skip"))
        return
    task.state = TaskState.SKIPPED
    task.next_reminder_at = None
    task.save(update_fields=["state", "next_reminder_at"])
    client.send_message(where, texts.task_skipped(task))


# --- snooze ---------------------------------------------------------


def _snooze(task, hours):
    task.next_reminder_at = timezone.now() + timedelta(hours=hours)
    task.save(update_fields=["next_reminder_at"])


@command("snooze")
def snooze_command(update, client):
    where = chat_id(update)
    parts = command_args(update).split()
    if len(parts) != 2:
        client.send_message(where, texts.SNOOZE_USAGE)
        return
    task = _load_task(_int_arg(parts[0]))
    hours = _int_arg(parts[1])
    if task is None or hours is None or hours <= 0:
        client.send_message(where, texts.SNOOZE_USAGE)
        return
    _snooze(task, hours)
    client.send_message(where, texts.task_snoozed(task, hours))


@callback("snooze")
def snooze_callback(update, client):
    parts = callback_data(update).split(":")
    _ack(client, update)
    if len(parts) != 3:
        return
    task = _load_task(_int_arg(parts[1]))
    hours = _int_arg(parts[2])
    if task is None or hours is None:
        return
    _snooze(task, hours)
    client.send_message(chat_id(update), texts.task_snoozed(task, hours))
