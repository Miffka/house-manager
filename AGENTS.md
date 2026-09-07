Commands

- `uv sync` - install dependencies
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_smoke.py` - one test file
- `uv run python manage.py migrate` - apply database migrations
- `uv run python manage.py run_bot` - start the bot (long-polling)

Rules

- Dependencies are added in `pyproject.toml`. Do not add one without asking

Documents

- `_docs/process.md` - how work is organized
- `_docs/plan.md` - project scope
- `_docs/tasks.md` - the backlog
