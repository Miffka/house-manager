"""User-facing message strings for the bot."""

HELP = (
    "Chore Manager — shared to-do pool for the two of us.\n"
    "\n"
    "/start — register yourself with the bot\n"
    "/add <title> [~effort] — add a task (auto-assigned)\n"
    "/pool — every open task\n"
    "/mine — your open tasks\n"
    "/done <id> — mark a task done\n"
    "/skip <id> — drop a task without logging it\n"
    "/snooze <id> <hours> — push a task's next reminder back\n"
    "/templates — list recurring templates\n"
    "/template_add <title> every <n> days [~effort] — add a template\n"
    "/template_off <id> — deactivate a template\n"
    "/help — this message\n"
)

START_REGISTERED = "You're registered as {name}. Send /help to see what I can do."

ADD_USAGE = "Usage: /add <title> [~effort]   e.g. /add take out the bins ~2"
NEED_ID = "Usage: /{command} <task id>"
SNOOZE_USAGE = "Usage: /snooze <task id> <hours>"
TEMPLATE_ADD_USAGE = (
    "Usage: /template_add <title> every <n> days [~effort]\n"
    "e.g. /template_add vacuum every 5 days ~2"
)

NO_PEOPLE = "Nobody has run /start yet — I can't assign this."
TASK_NOT_FOUND = "No task #{task_id}."
TEMPLATE_NOT_FOUND = "No template #{template_id}."
POOL_EMPTY = "The pool is empty. 🎉"
MINE_EMPTY = "You have no open tasks. 🎉"
NO_TEMPLATES = "No templates yet. Add one with /template_add."


def task_added(task):
    who = task.assignee.display_name if task.assignee else "nobody"
    return f"Added #{task.id}: {task.title} (effort {task.effort}) → {who}"


def task_line(task):
    who = task.assignee.display_name if task.assignee else "unassigned"
    return f"#{task.id} {task.title} (effort {task.effort}) — {who}"


def pool_list(tasks):
    return "Open tasks:\n" + "\n".join(task_line(t) for t in tasks)


def mine_list(tasks):
    return "Your open tasks:\n" + "\n".join(task_line(t) for t in tasks)


def task_done(task):
    return f"Done: #{task.id} {task.title}. Logged. ✅"


def task_skipped(task):
    return f"Skipped #{task.id} {task.title}. Not logged."


def task_snoozed(task, hours):
    return f"Snoozed #{task.id} for {hours}h."


def template_line(template):
    state = "on" if template.active else "off"
    return (
        f"#{template.id} {template.title} — every {template.interval_days}d, "
        f"effort {template.effort} [{state}]"
    )


def template_list(templates):
    return "Templates:\n" + "\n".join(template_line(t) for t in templates)


def template_added(template):
    return (
        f"Template #{template.id}: {template.title} every "
        f"{template.interval_days} days (effort {template.effort})."
    )


def template_off(template):
    return f"Template #{template.id} deactivated."


def template_spawned(task):
    who = task.assignee.display_name if task.assignee else "nobody"
    return f"Recurring: #{task.id} {task.title} → {who}"


def mention(person):
    """An HTML mention link for a Person-like object (needs a parse_mode of HTML)."""
    from html import escape

    return f'<a href="tg://user?id={person.tg_user_id}">{escape(person.display_name)}</a>'


def reminder_gentle(assignee_mention, task_id, task_title):
    return f"{assignee_mention}, don't forget: #{task_id} {task_title}."


def reminder_strong(assignee_mention, other_mention, task_id, task_title):
    tail = f" {other_mention}, nudge them?" if other_mention else ""
    return (
        f"{assignee_mention}, #{task_id} {task_title} is still open and overdue.{tail}"
    )
