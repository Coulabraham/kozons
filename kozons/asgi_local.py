"""Entrée ASGI locale autonome pour le développement sans variables de shell."""

import os


os.environ["DJANGO_SETTINGS_MODULE"] = "kozons.settings.local"

from .asgi import application  # noqa: E402,F401
