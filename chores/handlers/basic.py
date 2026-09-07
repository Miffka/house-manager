"""``/help`` and ``/start`` handlers."""

from chores import texts
from chores.models import Person
from chores.telegram.dispatch import chat_id, command, sender


def _display_name(from_user):
    return (
        from_user.get("username")
        or from_user.get("first_name")
        or str(from_user.get("id"))
    )


@command("help")
def help_command(update, client):
    client.send_message(chat_id(update), texts.HELP)


@command("start")
def start_command(update, client):
    from_user = sender(update)
    name = _display_name(from_user)
    person, _ = Person.objects.update_or_create(
        tg_user_id=from_user["id"],
        defaults={"display_name": name},
    )
    client.send_message(
        chat_id(update), texts.START_REGISTERED.format(name=person.display_name)
    )
