"""Configuration Django du projet Kora.

Un seul module de réglages, alimenté par variables d'environnement.
Aucune configuration métier ne doit être ajoutée ailleurs (voir docs/14-conventions-de-code.md §8).
"""
from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name: str, default: str | None = None) -> str | None:
    """Lit une variable d'environnement.

    Args:
        name: Nom de la variable.
        default: Valeur retournée si la variable est absente.

    Returns:
        La valeur de la variable, ou ``default``.

    Example:
        >>> env("DJANGO_DEBUG", "1")
        '1'
    """
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    """Convertit une variable d'environnement en booléen.

    Args:
        name: Nom de la variable.
        default: Valeur si la variable est absente.

    Returns:
        ``True`` si la valeur est ``1``, ``true``, ``yes`` ou ``on``.
    """
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    """Découpe une liste séparée par des virgules.

    Args:
        name: Nom de la variable.
        default: Valeur par défaut (chaîne vide).

    Returns:
        La liste des éléments non vides, sans espaces superflus.
    """
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# --------------------------------------------------------------------- sécurité
DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

# Clé de chiffrement des secrets de management (AES-256-GCM).
# En développement seulement, une clé est dérivée de SECRET_KEY pour éviter toute
# configuration supplémentaire ; en production la variable est obligatoire.
SECRET_ENCRYPTION_KEY = env("SECRET_ENCRYPTION_KEY") or base64.urlsafe_b64encode(
    hashlib.sha256(SECRET_KEY.encode()).digest()
).decode()
SECRET_KEY_VERSION = int(env("SECRET_KEY_VERSION", "1") or "1")

# --------------------------------------------------------------------- applications
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.tenants",
    "apps.accounts",
    "apps.network",
    "apps.mikrotik",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.tenancy.TenantMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

# --------------------------------------------------------------------- base de données
if env("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB"),
            "USER": env("POSTGRES_USER", "kora"),
            "PASSWORD": env("POSTGRES_PASSWORD", ""),
            "HOST": env("POSTGRES_HOST", "127.0.0.1"),
            "PORT": env("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": Path(env("SQLITE_PATH", str(BASE_DIR / "db.sqlite3"))),
        }
    }

# --------------------------------------------------------------------- authentification
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.api.pagination.StandardPagination",
    "PAGE_SIZE": 50,
    "EXCEPTION_HANDLER": "core.api.exceptions.api_exception_handler",
}

# --------------------------------------------------------------------- international
LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Ouagadougou"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------- workers
CELERY_BROKER_URL = env("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", "")
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", DEBUG)
CELERY_TASK_TIME_LIMIT = 120
CELERY_TASK_SOFT_TIME_LIMIT = 90
CELERY_TASK_SERIALIZER = "json"

# --------------------------------------------------------------------- connecteur MikroTik
MIKROTIK_DEFAULT_TRANSPORT = env("MIKROTIK_DEFAULT_TRANSPORT", "rest")
MIKROTIK_TIMEOUT_SECONDS = int(env("MIKROTIK_TIMEOUT_SECONDS", "10") or "10")
MIKROTIK_WIREGUARD_ENDPOINT = env("MIKROTIK_WIREGUARD_ENDPOINT", "vpn.kora.bf")
MIKROTIK_MANAGEMENT_NETWORK = env("MIKROTIK_MANAGEMENT_NETWORK", "10.66.0.0/24")
MIKROTIK_FAKE_MODE = env_bool("MIKROTIK_FAKE_MODE", True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "apps.mikrotik": {"level": "DEBUG" if DEBUG else "INFO", "propagate": True},
    },
}
