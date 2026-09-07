"""Task #4 — completion logging and pruning."""

from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from chores.history import record_completion
from chores.models import CompletionLog, Person, Task


@pytest.mark.django_db
@override_settings(LOG_RETENTION_DAYS=14)
def test_record_completion_logs_and_prunes():
    person = Person.objects.create(tg_user_id=1, display_name="Sam")
    task = Task.objects.create(title="Dishes", effort=3, assignee=person)
    now = timezone.now()

    recent = CompletionLog.objects.create(task=task, person=person, effort=1)
    CompletionLog.objects.filter(pk=recent.pk).update(
        completed_at=now - timedelta(days=3)
    )
    old = CompletionLog.objects.create(task=task, person=person, effort=1)
    CompletionLog.objects.filter(pk=old.pk).update(
        completed_at=now - timedelta(days=20)
    )

    log = record_completion(task, person)

    surviving = set(CompletionLog.objects.values_list("pk", flat=True))
    assert recent.pk in surviving
    assert old.pk not in surviving
    assert log.pk in surviving
    assert log.effort == 3
    assert log.person == person
