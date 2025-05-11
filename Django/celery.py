from __future__ import absolute_import, unicode_literals
import os
from celery import Celery, shared_task
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django.settings')

app = Celery('instagramautomation')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    'fetch-and-execute-tasks-every-day-at-3pm': {
        'task': 'tasks.update_json',
        'schedule': 6000.0,
    },
    'fetch-and-execute-tasks-every-5-minutes': {
        'task': 'tasks.auto_posting',
        'schedule': 60.0,  # 300 seconds == 5 minutes
    },
}