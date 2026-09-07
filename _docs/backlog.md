# Chore Manager — Backlog

Stack: Python 3.11+, `django~=5.1` (ORM, migrations, settings, admin), a
hand-rolled sync Telegram Bot API client over `httpx~=0.27` (long-polling via
`getUpdates` — no `python-telegram-bot`), `django-environ~=0.11` for config,
SQLite (single file `chore.db`), `ruff`, `pytest` + `pytest-django`.
Entry point: `python manage.py run_bot`. Long-polling.

There is no job queue. Scheduled behaviour (reminders, template spawning) is
driven by timestamp columns on the models (`next_reminder_at`, `next_due_at`),
serviced on every pass of the `run_bot` loop — so there is nothing to rebuild on
startup.

Each task below is sized for one session and written to be handed off without
reading the others. Later tasks assume earlier ones are merged (models exist in
`chores/models.py`, the loop is `chores/management/commands/run_bot.py`) but do
not require their task notes.

## 1. Project skeleton with a passing test
Goal: An installable, lintable Django project with `pytest` green on an empty suite.
Description: Create `pyproject.toml` (project metadata, deps listed above, `ruff`
config, and `[tool.pytest.ini_options]` with `DJANGO_SETTINGS_MODULE = "config.settings"`),
`manage.py`, the `config/` project package (`settings.py`, `urls.py` with only the
admin route, `wsgi.py`), the `chores/` app package (`__init__.py`, `apps.py`, empty
`models.py`, `migrations/__init__.py`), a `tests/` dir, and `.env.example`. Add one
trivial test (`tests/test_smoke.py`) asserting `import chores` works, and confirm
`ruff check`, `python manage.py check`, and `pytest` all pass.

## 2. Configuration module
Goal: Load settings from environment / `.env` with sane defaults.
Description: In `config/settings.py`, use `django-environ` to read `BOT_TOKEN`,
`GROUP_CHAT_ID`, `DB_PATH` (default `chore.db`), `REMINDER_1_DELAY` (default 4h),
`REMINDER_2_DELAY` (default 20h), `LOG_RETENTION_DAYS` (default 14), plus Django's
`SECRET_KEY` and `DEBUG`. `.env` is read once at settings import. Wire `DATABASES`
to the SQLite file at `DB_PATH`. Fill `.env.example`. Test that values load from a
supplied env mapping (construct `environ.Env` with a dict, or use
`override_settings`) and that defaults apply when unset.

## 3. Database layer and models
Goal: Django models for the core tables, with a committed initial migration.
Description: Add the four models to `chores/models.py`: `Person` (`tg_user_id`,
`display_name`), `Template` (`title`, `interval_days`, `effort`, `active`,
`last_spawned_at`, `next_due_at`), `Task` (`title`, `effort`, `source`,
`template` FK, `assignee` FK to `Person`, `state`, `created_at`, `due_at`,
`done_at`, `reminder_level`, `next_reminder_at`), `CompletionLog` (`task` FK,
`person` FK, `effort`, `completed_at`). Run `makemigrations` and commit
`chores/migrations/0001_initial.py`. Register all four in `chores/admin.py` so the
pool is viewable in Django admin. Test: with `@pytest.mark.django_db`, create and
round-trip one row of each model.

## 4. Completion logging and pruning helper
Goal: Record a completion and keep the log bounded to the retention window.
Description: In `chores/history.py`, add `record_completion(task, person)` that
creates a `CompletionLog` row and deletes rows older than `LOG_RETENTION_DAYS`
(`CompletionLog.objects.filter(completed_at__lt=cutoff).delete()`). Pure ORM
logic, no Telegram. Test with `@pytest.mark.django_db` and seeded rows spanning
old and recent dates: recent rows survive, old rows are pruned, the new row is
present.

## 5. Auto-assignment fairness function
Goal: Decide which of the two people a new task goes to.
Description: In `chores/fairness.py`, add a pure function taking plain data
(recent completion records with effort + timestamp, currently-open tasks per
person, the list of people) and returning the chosen assignee. Rule: lower
recent-load score wins, where score = decayed sum of completed effort over 14 days
+ effort of open assigned tasks; tie-break by least-recent completion. No Django
or bot imports. Test balanced history (alternates), skewed history (goes to
lighter person), and the tie-break.

## 6. Bot bootstrap: long-poll loop, /help, /start
Goal: The bot starts, long-polls, and answers `/help` and `/start`.
Description: Add `chores/telegram/client.py` (a thin sync client over the Bot API:
`get_updates(offset, timeout)`, `send_message`, `answer_callback_query`), 
`chores/telegram/dispatch.py` (routes an update dict to a handler by command or
`callback_query` data), `chores/texts.py` for message strings, and
`chores/management/commands/run_bot.py` — an offset-tracked `getUpdates` loop that
dispatches updates. Register `/help` (static text) and `/start` (upserts a
`Person` from the sender). Document manual verification (BotFather throwaway
token, test group). Test that `dispatch` routes `/help` and `/start` update dicts
to the right handler and that `/start` upserts a `Person` (mock
`client.send_message`, `@pytest.mark.django_db`).

## 7. Manual task commands: add, pool, mine
Goal: Create and view tasks from chat.
Description: Add `chores/handlers/tasks.py` with `/add <title> [~effort]` (creates
a `Task`, assigns via `fairness`, replies with the assignee and an inline "Done"
button — an `inline_keyboard` with `callback_data`), `/pool` (all open tasks with
assignee), and `/mine` (caller's open tasks). Wire them into `dispatch`. Test the
handler logic with fake `update` dicts, a mocked client, and
`@pytest.mark.django_db`.

## 8. Completion commands: done, skip, snooze
Goal: Close out tasks from chat.
Description: Add `/done <id>` plus a "Done" callback handler (set `state=done`,
`done_at`, call `record_completion`, clear the task's `next_reminder_at`),
`/skip <id>` (set `state=skipped`, no log entry), and `/snooze <id> <hours>` plus
a "Snooze" callback (push `next_reminder_at`). Wire handlers into `dispatch`. Test
each transition with `@pytest.mark.django_db`.

## 9. Escalating reminders
Goal: Nudge the assignee when a task sits open, harder the second time.
Description: Add `chores/reminders.py` with a pure state function
`(reminder_level, ...) -> (new_level, next_reminder_at, message)`: 0→1 gentle
@mention of the assignee; 1→2 stronger message that also @mentions the other
person; stop re-arming at level 2, otherwise re-arm at `now + REMINDER_2_DELAY`.
Add `service_due_reminders(client, now)` that scans open `Task`s with
`next_reminder_at <= now`, applies the transition, sends the message, and saves.
Set `next_reminder_at = now + REMINDER_1_DELAY` when a task is created/assigned.
The `run_bot` loop calls `service_due_reminders` each pass — there is no job
queue and nothing to rebuild on startup. Test the level transitions as a pure
function and `service_due_reminders` against a seeded DB.

## 10. Recurring templates
Goal: Templates auto-populate the pool on their interval.
Description: Add template commands (`/templates` list, `/template_add <title>
every <n> days [~effort]`, `/template_off <id>`) in `chores/handlers/templates.py`
and `spawn_due_templates(client, now)` in `chores/scheduler.py` that, for each
active template with `now >= next_due_at`, creates a `Task`, assigns via
`fairness`, sets its first `next_reminder_at`, advances
`next_due_at += interval_days`, and announces it. The `run_bot` loop calls
`spawn_due_templates` each pass — nothing to rebuild on startup. Test the
spawn/advance logic against a seeded DB.

## 11. Run and deploy documentation
Goal: Someone can stand the bot up from a clean checkout.
Description: Write `README.md`: create a bot via @BotFather, get the group chat
id, copy `.env.example` to `.env`, install with `uv sync`, run
`python manage.py migrate`, optionally `python manage.py createsuperuser` and
`python manage.py runserver` for the admin pool view, then `python manage.py
run_bot`. Add a sample `systemd` unit (running `manage.py run_bot`) and a
`Dockerfile` as optional deployment paths (no app code changes).
