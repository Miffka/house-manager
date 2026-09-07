"""Glue between the pure :mod:`chores.fairness` scorer and the ORM."""

from django.utils import timezone

from chores import fairness
from chores.models import CompletionLog, Person, Task, TaskState


def _completion_records():
    return [
        fairness.CompletionRecord(
            person=row.person_id,
            effort=row.effort,
            completed_at=row.completed_at,
        )
        for row in CompletionLog.objects.all()
    ]


def _open_assigned_effort():
    return list(
        Task.objects.filter(state=TaskState.OPEN, assignee__isnull=False).values_list(
            "assignee_id", "effort"
        )
    )


def choose_assignee(now=None):
    """Return the :class:`Person` the next task should go to, or ``None``.

    ``None`` only when there are no people registered yet.
    """
    now = now or timezone.now()
    people = list(Person.objects.order_by("id"))
    if not people:
        return None

    chosen_id = fairness.choose_assignee(
        [p.id for p in people],
        _completion_records(),
        _open_assigned_effort(),
        now,
    )
    return next(p for p in people if p.id == chosen_id)
