"""Django settings for the Chore Manager project.

Configuration is read once, here, from the process environment / a ``.env`` file
via ``django-environ``. See ``.env.example`` for the supported keys and their
defaults. The reading logic lives in ``config.env`` so it can be unit-tested.
"""

from pathlib import Path

import environ

from config.env import load_settings

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

_cfg = load_settings(env)

# --- Project configuration (from environment / .env) -------------------------

SECRET_KEY = _cfg["SECRET_KEY"]
DEBUG = _cfg["DEBUG"]

BOT_TOKEN = _cfg["BOT_TOKEN"]
GROUP_CHAT_ID = _cfg["GROUP_CHAT_ID"]

DB_PATH = _cfg["DB_PATH"]
REMINDER_1_DELAY = _cfg["REMINDER_1_DELAY"]
REMINDER_2_DELAY = _cfg["REMINDER_2_DELAY"]
LOG_RETENTION_DAYS = _cfg["LOG_RETENTION_DAYS"]

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "chores",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database — a single SQLite file at DB_PATH (relative paths resolve to BASE_DIR).

_db_file = Path(DB_PATH)
if not _db_file.is_absolute():
    _db_file = BASE_DIR / _db_file

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": _db_file,
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = "static/"

# Default primary key field type

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
