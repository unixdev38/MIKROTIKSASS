"""Application Celery unique du projet.

Les workers sont lancés séparément de l'API :
    celery -A config worker -Q provisioning,collecte -l info
"""
from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("kora")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, name="kora.debug_ping")
def debug_ping(self: object) -> str:
    """Tâche de diagnostic : confirme que le worker répond.

    Returns:
        La chaîne ``"pong"``.
    """
    return "pong"
