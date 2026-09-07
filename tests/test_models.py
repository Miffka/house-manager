"""Task #3 — models round-trip."""

from datetime import timedelta

import pytest
from django.utils import timezone

from chores.models import CompletionLog, Person, Task, TaskSource, TaskState, Template


@pytest.mark.django_db
def test_models_round_trip():
    person = Person.objects.create(tg_user_id=42, display_name="Alex")

    template = Template.objects.create(
        title="Vacuum",
        interval_days=5,
        effort=2,
        next_due_at=timezone.now() + timedelta(days=5),
    )

    task = Task.objects.create(
        title="Vacuum the hallway",
        effort=2,
        source=TaskSource.TEMPLATE,
        template=template,
        assignee=person,
        due_at=timezone.now() + timedelta(days=1),
    )

    log = CompletionLog.objects.create(task=task, person=person, effort=2)

    assert Person.objects.get(pk=person.pk).display_name == "Alex"
    assert Template.objects.get(pk=template.pk).interval_days == 5
    reloaded = Task.objects.get(pk=task.pk)
    assert reloaded.state == TaskState.OPEN
    assert reloaded.reminder_level == 0
    assert reloaded.template == template
    assert reloaded.assignee == person
    assert CompletionLog.objects.get(pk=log.pk).task == task
