import string

from django.core.mail import EmailMultiAlternatives

from django.conf import settings
from emailService.celery import app


@app.task(name='send_email')
def send_email(html_message: string, text_message: string, subject: string, to: list):
    mail = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=settings.EMAIL_HOST_USER,
        to=to)
    mail.attach_alternative(html_message, "text/html")
    mail.send()
