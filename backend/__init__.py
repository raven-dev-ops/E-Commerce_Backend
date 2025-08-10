from .celery import app as celery_app
from . import db_monitoring  # noqa: F401 to ensure signal handlers load

__all__ = ("celery_app",)
