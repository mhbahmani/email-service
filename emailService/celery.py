from __future__ import absolute_import, unicode_literals
import os
from logging.config import dictConfig

from django.conf import settings
from celery import Celery
from celery.signals import setup_logging


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emailService.settings')

app = Celery(main='emailService')
app.config_from_object('django.conf:settings')


# @setup_logging.connect
# def config_loggers(*args, **kwags):
#     dictConfig(settings.LOGGING)


@app.task(name='fuckin-test')
def test1():
    print('test!')


app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)