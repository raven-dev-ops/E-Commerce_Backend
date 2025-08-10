"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

# Enable DataDog APM if available
try:  # pragma: no cover - optional dependency
    from ddtrace import patch_all  # type: ignore

    patch_all(mongoengine=False)
except Exception:  # pragma: no cover - ignore if ddtrace isn't installed
    pass

from .mongo_connection import connect_mongodb
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

application = get_wsgi_application()

connect_mongodb()
