"""Auto-assignment fairness.

A pure function that decides which person a new task goes to, given plain data.
No Django or bot imports.

Inputs
------
people
    An ordered list of person keys (any hashable, e.g. a primary key). The
    order is the final tie-breaker so the result is deterministic.
completions
    Iterable of :class:`CompletionRecord` — recent completed work.
open_tasks
    Iterable of ``(person_key, effort)`` for currently-open assigned tasks.
now
    The reference time (``datetime``); completion ages are measured from it.

Rule
----
The person with the lower *recent-load score* wins, where the score is the
decayed sum of completed effort over ``window_days`` plus the effort of their
open assigned tasks. Ties break toward the least-recent completion (someone who
has never completed anything sorts first).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

WINDOW_DAYS = 14


@dataclass(frozen=True)
class CompletionRecord:
    person: object
    effort: float
    completed_at: datetime


def _decayed_completion_score(person_key, completions, now, window):
    total = 0.0
    for rec in completions:
        if rec.person != person_key:
            continue
        age = now - rec.completed_at
        if age < timedelta(0):
            age = timedelta(0)
        if age >= window:
            continue
        weight = 1.0 - (age / window)  # linear decay: 1.0 now → 0.0 at the edge
        total += rec.effort * weight
    return total


def _open_effort(person_key, open_tasks):
    return sum(effort for pk, effort in open_tasks if pk == person_key)


def _last_completion(person_key, completions):
    times = [r.completed_at for r in completions if r.person == person_key]
    return max(times) if times else None


def recent_load_score(person_key, completions, open_tasks, now, window_days=WINDOW_DAYS):
    window = timedelta(days=window_days)
    return _decayed_completion_score(
        person_key, completions, now, window
    ) + _open_effort(person_key, open_tasks)


def choose_assignee(people, completions, open_tasks, now, window_days=WINDOW_DAYS):
    """Return the key of the person the next task should go to."""
    completions = list(completions)
    open_tasks = list(open_tasks)

    best_key = None
    best_sort = None
    for index, person_key in enumerate(people):
        score = recent_load_score(
            person_key, completions, open_tasks, now, window_days
        )
        last = _last_completion(person_key, completions)
        # None (never completed) must sort before any real timestamp.
        last_rank = last.timestamp() if last is not None else float("-inf")
        sort_key = (score, last_rank, index)
        if best_sort is None or sort_key < best_sort:
            best_sort = sort_key
            best_key = person_key
    return best_key
