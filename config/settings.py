"""
Django settings for config project.
"""

import os
import re
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "unsafe-development-key"
    else:
        raise RuntimeError("DJANGO_SECRET_KEY is required")

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

CSRF_TRUSTED_ORIGINS: list[str] = []

# The fallback preserves the existing deployment until its generic settings are set.
app_host = os.getenv("APP_HOST") or os.getenv("RENDER_EXTERNAL_HOSTNAME")
app_origin = os.getenv("APP_ORIGIN")
APP_ORIGIN = app_origin or (f"https://{app_host}" if app_host else "")

if APP_ORIGIN:
    parsed_app_origin = urlparse(APP_ORIGIN)
    if not parsed_app_origin.scheme or not parsed_app_origin.netloc:
        raise RuntimeError("APP_ORIGIN must be an absolute origin")
    if not DEBUG and parsed_app_origin.scheme != "https":
        raise RuntimeError("APP_ORIGIN must use HTTPS when DJANGO_DEBUG is false")

if app_host:
    ALLOWED_HOSTS.append(app_host)

if app_origin:
    CSRF_TRUSTED_ORIGINS.append(app_origin)
elif app_host:
    CSRF_TRUSTED_ORIGINS.append(f"https://{app_host}")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.accounts",
    "apps.core",
    "apps.events",
    "apps.people",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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


USE_SQLITE = os.getenv("USE_SQLITE", "False").lower() == "true"

if USE_SQLITE:
    if not DEBUG:
        raise RuntimeError("USE_SQLITE is only allowed when DJANGO_DEBUG is true")

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    database_environment = {
        "PGDATABASE": os.getenv("PGDATABASE"),
        "PGUSER": os.getenv("PGUSER"),
        "PGPASSWORD": os.getenv("PGPASSWORD"),
        "PGHOST": os.getenv("PGHOST"),
        "PGPORT": os.getenv("PGPORT", "5432"),
    }
    missing_database_components = [
        name for name, value in database_environment.items() if not value
    ]
    if missing_database_components:
        missing = ", ".join(missing_database_components)
        raise RuntimeError(
            f"{missing} is required unless USE_SQLITE is true"
        )

    database_components = {
        "NAME": database_environment["PGDATABASE"],
        "USER": database_environment["PGUSER"],
        "PASSWORD": database_environment["PGPASSWORD"],
        "HOST": database_environment["PGHOST"],
        "PORT": database_environment["PGPORT"],
    }

    database_connection_mode = os.getenv(
        "POLSK_DATABASE_CONNECTION_MODE", "pooled"
    )
    if database_connection_mode not in {"pooled", "direct"}:
        raise RuntimeError(
            "POLSK_DATABASE_CONNECTION_MODE must be either pooled or direct"
        )

    database_host = database_components["HOST"]
    if database_host.endswith(".neon.tech"):
        endpoint, _, suffix = database_host.partition(".")
        if endpoint.endswith("-pooler"):
            raise RuntimeError("PGHOST must be the direct Neon hostname without -pooler")
        if database_connection_mode == "pooled":
            database_components["HOST"] = f"{endpoint}-pooler.{suffix}"

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            **database_components,
            "CONN_MAX_AGE": 0,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {
                "sslmode": os.getenv("PGSSLMODE", "require"),
                "channel_binding": os.getenv("PGCHANNELBINDING", "require"),
                "prepare_threshold": None,
            },
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "da"
TIME_ZONE = "Europe/Copenhagen"

USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

LOGIN_URL = "core:login"
LOGIN_REDIRECT_URL = "core:home"
AUTH_USER_MODEL = "accounts.User"

STARTIAPP_BRAND_NAME = os.getenv("STARTIAPP_BRAND_NAME", "")
STARTIAPP_API_KEY = os.getenv("STARTIAPP_API_KEY", "")
STARTIAPP_ENVIRONMENT_TAG = os.getenv("STARTIAPP_ENVIRONMENT_TAG", "development")

if STARTIAPP_BRAND_NAME and not re.fullmatch(r"[a-z0-9-]+", STARTIAPP_BRAND_NAME):
    raise RuntimeError("STARTIAPP_BRAND_NAME must contain lowercase letters, digits, and hyphens")

if not re.fullmatch(r"[a-z0-9-]+", STARTIAPP_ENVIRONMENT_TAG):
    raise RuntimeError("STARTIAPP_ENVIRONMENT_TAG must contain lowercase letters, digits, and hyphens")

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "apps": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SECURE_HSTS_SECONDS = 31_536_000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"
