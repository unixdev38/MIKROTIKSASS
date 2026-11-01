"""Configuration du projet Kora et application Celery partagée."""
from config.celery import app as celery_app

__all__ = ("celery_app",)
