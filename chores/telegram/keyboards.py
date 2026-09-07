"""Inline keyboard builders."""

SNOOZE_HOURS = 3


def task_actions(task):
    """A "Done" / "Snooze" inline keyboard for an open task."""
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Done", "callback_data": f"done:{task.id}"},
                {
                    "text": f"💤 Snooze {SNOOZE_HOURS}h",
                    "callback_data": f"snooze:{task.id}:{SNOOZE_HOURS}",
                },
            ]
        ]
    }
