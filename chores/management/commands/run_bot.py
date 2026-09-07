"""``python manage.py run_bot`` — the Telegram long-polling loop.

Manual verification
-------------------
1. Talk to @BotFather, ``/newbot``, and copy the throwaway token.
2. Create a test group, add the bot, and (for group privacy) either disable
   privacy mode via BotFather or make the bot an admin.
3. Get the chat id: send a message in the group, then open
   ``https://api.telegram.org/bot<TOKEN>/getUpdates`` and read ``chat.id``.
4. Put ``BOT_TOKEN`` and ``GROUP_CHAT_ID`` in ``.env``, run
   ``python manage.py migrate`` then ``python manage.py run_bot``.
5. In the group: ``/start`` should register you, ``/help`` should print the
   command list.

There is no job queue: reminder and template timestamps are serviced on every
pass of this loop, so nothing needs rebuilding on startup.
"""

import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

POLL_TIMEOUT = 30
ERROR_BACKOFF = 3


class Command(BaseCommand):
    help = "Run the Telegram bot (long-polling getUpdates loop)."

    def handle(self, *args, **options):
        from chores import handlers  # noqa: F401  (populates the dispatch registry)
        from chores.telegram.client import TelegramClient
        from chores.telegram.dispatch import dispatch

        if not settings.BOT_TOKEN:
            raise CommandError("BOT_TOKEN is not set — see .env.example")

        client = TelegramClient(settings.BOT_TOKEN)
        offset = None
        self.stdout.write(self.style.SUCCESS("run_bot: long-polling for updates…"))

        try:
            while True:
                self._service_timers(client)
                try:
                    updates = client.get_updates(offset=offset, timeout=POLL_TIMEOUT)
                except Exception as exc:  # noqa: BLE001 — keep the loop alive
                    self.stderr.write(f"getUpdates failed: {exc!r}")
                    time.sleep(ERROR_BACKOFF)
                    continue

                for update in updates or []:
                    offset = update["update_id"] + 1
                    try:
                        dispatch(update, client)
                    except Exception as exc:  # noqa: BLE001 — one bad update mustn't stop the bot
                        uid = update.get("update_id")
                        self.stderr.write(f"handler error on update {uid}: {exc!r}")
        except KeyboardInterrupt:
            self.stdout.write("\nrun_bot: stopping.")
        finally:
            client.close()

    def _service_timers(self, client):
        """Hook for the reminder/template scans (wired up in later tasks)."""
        now = timezone.now()
        try:
            from chores.scheduler import spawn_due_templates

            spawn_due_templates(client, now)
        except ImportError:
            pass
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(f"spawn_due_templates failed: {exc!r}")
        try:
            from chores.reminders import service_due_reminders

            service_due_reminders(client, now)
        except ImportError:
            pass
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(f"service_due_reminders failed: {exc!r}")
