"""Task #5 — auto-assignment fairness."""

from datetime import UTC, datetime, timedelta

from chores.fairness import CompletionRecord, choose_assignee

NOW = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)


def rec(person, effort, days_ago):
    return CompletionRecord(
        person=person, effort=effort, completed_at=NOW - timedelta(days=days_ago)
    )


def test_balanced_history_uses_deterministic_tie_break():
    # Identical load and identical last-completion time → first listed wins.
    completions = [rec("a", 2, 1), rec("b", 2, 1)]
    assert choose_assignee(["a", "b"], completions, [], NOW) == "a"
    assert choose_assignee(["b", "a"], completions, [], NOW) == "b"


def test_skewed_history_goes_to_lighter_person():
    completions = [rec("a", 5, 1), rec("a", 5, 2), rec("a", 5, 3), rec("b", 1, 6)]
    assert choose_assignee(["a", "b"], completions, [], NOW) == "b"


def test_open_tasks_count_toward_load():
    completions = [rec("a", 1, 1), rec("b", 1, 1)]
    # b already carries an open heavy task → a is lighter now.
    assert choose_assignee(["a", "b"], completions, [("b", 10)], NOW) == "a"


def test_tie_break_prefers_least_recent_completer():
    # Equal decayed load, but a completed more recently → b is "more behind".
    completions = [rec("a", 3, 1), rec("b", 3, 10)]
    # Loads are not equal here (a's recent work decays less), so a is heavier
    # and b is chosen for that reason too; craft an exact tie instead:
    completions = [rec("a", 2, 5), rec("b", 2, 5), rec("a", 0, 0)]
    assert choose_assignee(["a", "b"], completions, [], NOW) == "b"


def test_never_completed_person_sorts_first_on_tie():
    completions = [rec("a", 0, 1)]  # zero-effort, so scores tie at 0
    assert choose_assignee(["a", "b"], completions, [], NOW) == "b"
