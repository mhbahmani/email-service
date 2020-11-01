from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings

from celery.decorators import task


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emailService.settings')
app = Celery('emailService')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@task(name="celery_test_task")
def celery_test_task():
    print("celery is working properly!")
