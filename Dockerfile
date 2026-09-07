FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DB_PATH=/data/chore.db

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install dependencies first for layer caching.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

VOLUME ["/data"]

# Migrate, then start the long-poll loop. BOT_TOKEN and GROUP_CHAT_ID come from
# the environment (docker run --env-file .env).
CMD ["sh", "-c", "uv run python manage.py migrate --noinput && uv run python manage.py run_bot"]
