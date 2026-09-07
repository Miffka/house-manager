"""Importing this package registers every handler with the dispatcher."""

from chores.handlers import basic, completions, tasks  # noqa: F401

__all__ = ["basic", "completions", "tasks"]
