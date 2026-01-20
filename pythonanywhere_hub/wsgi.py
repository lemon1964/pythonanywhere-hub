# pythonanywhere-hub/pythonanywhere_hub/wsgi.py
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pythonanywhere_hub.settings")

application = get_wsgi_application()
