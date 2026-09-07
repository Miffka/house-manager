# Chore Manager

A Telegram bot that runs a shared chore pool for a two-person household. Tasks
enter the pool from recurring templates or manual `/add`s, get auto-assigned to
whoever is "behind" on recent effort, and are nudged with escalating reminders
until they're marked done. History is kept only for the last couple of weeks —
just enough to drive the fairness decision.

Stack: Python 3.12+, Django 5.1 (ORM, migrations, settings, admin), a
hand-rolled synchronous Telegram Bot API long-poll loop over `httpx`,
`django-environ` for config, SQLite. No job queue — reminders and template
spawning are driven by timestamp columns scanned on every pass of the bot loop.

## Set up from a clean checkout

### 1. Create the bot

1. Message [@BotFather](https://t.me/BotFather), send `/newbot`, follow the
   prompts, and copy the bot **token**.
2. To let the bot read normal group messages, send BotFather `/setprivacy` →
   pick the bot → **Disable** (or add the bot to the group as an admin).

### 2. Get the group chat id

1. Create the group (or use an existing one) and add the bot.
2. Send any message in the group.
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser and read
   `result[].message.chat.id` — for groups it's a negative number.

### 3. Configure

```sh
cp .env.example .env
```

Edit `.env`:

| Key | Meaning | Default |
| --- | --- | --- |
| `SECRET_KEY` | Django secret key | dev placeholder |
| `DEBUG` | Django debug flag | `True` |
| `BOT_TOKEN` | token from BotFather | — (required) |
| `GROUP_CHAT_ID` | the group's chat id | — (required) |
| `DB_PATH` | SQLite file path | `chore.db` |
| `REMINDER_1_DELAY` | first nudge delay | `4h` |
| `REMINDER_2_DELAY` | second nudge delay | `20h` |
| `LOG_RETENTION_DAYS` | completion-history window | `14` |

Durations accept `d` / `h` / `m` / `s` suffixes, or a bare number of seconds.

### 4. Install and migrate

```sh
uv sync
uv run python manage.py migrate
```

### 5. (Optional) admin pool view

```sh
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Then open <http://127.0.0.1:8000/admin/> to browse people, templates, tasks and
the completion log.

### 6. Run the bot

```sh
uv run python manage.py run_bot
```

It long-polls `getUpdates`, dispatches commands, and on every pass spawns any
due templates and fires any due reminders. Stop it with Ctrl-C.

## Commands

| Command | What it does |
| --- | --- |
| `/start` | register yourself with the bot |
| `/add <title> [~effort]` | add a task; it's auto-assigned and gets a Done/Snooze button |
| `/pool` | list every open task |
| `/mine` | list your open tasks |
| `/done <id>` | mark done, log the completion, clear its reminder |
| `/skip <id>` | drop a task without logging it |
| `/snooze <id> <hours>` | push the next reminder back |
| `/templates` | list recurring templates |
| `/template_add <title> every <n> days [~effort]` | add a template |
| `/template_off <id>` | deactivate a template |
| `/help` | the command list |

## Development

```sh
uv run pytest          # the whole suite
uv run ruff check      # lint
uv run python manage.py check
```

## Deployment

Both paths below run the same `manage.py run_bot` process and need no app
changes. One long-running process is all the bot is.

### systemd

Copy [`deploy/chore-bot.service`](deploy/chore-bot.service), adjust the paths
and user, then:

```sh
sudo cp deploy/chore-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now chore-bot
journalctl -u chore-bot -f
```

### Docker

```sh
docker build -t chore-bot .
docker run --rm --env-file .env -v "$PWD/data:/data" -e DB_PATH=/data/chore.db chore-bot
```

The image runs `migrate` then `run_bot` on start. Mount a volume for the SQLite
file so the pool and history survive restarts.
