import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('open_knowledge_chat')

# Read configuration from Django settings, using the CELERY_ namespace.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks.py modules in installed apps.
app.autodiscover_tasks()
