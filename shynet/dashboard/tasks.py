import html2text

from shynet import settings
from shynet.celery import app as celery_app
from shynet.mail import send_mail


@celery_app.task
def send_email(to: [str], subject: str, content: str, from_email: str = None):
    text_content = html2text.html2text(content)
    send_mail(
        subject,
        text_content,
        from_email or settings.DEFAULT_FROM_EMAIL,
        to,
        html_message=content,
    )
