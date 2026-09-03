"""Email sending.

`send_mail` mirrors the signature of the mail helper Shynet used previously; the
backend is selected by `settings.EMAIL_BACKEND` in exactly the same way (a
console backend during development, SMTP otherwise).
"""

import sys

from flask_mail import Message

CONSOLE_BACKEND = "shynet.mail.ConsoleBackend"
SMTP_BACKEND = "shynet.mail.SmtpBackend"


def send_mail(subject, message, from_email, recipient_list, html_message=None):
    from . import settings
    from .extensions import mail

    from_email = from_email or settings.DEFAULT_FROM_EMAIL

    if settings.EMAIL_BACKEND == CONSOLE_BACKEND:
        _write_to_console(subject, message, from_email, recipient_list, html_message)
        return len(recipient_list)

    msg = Message(
        subject=subject,
        recipients=list(recipient_list),
        body=message,
        html=html_message,
        sender=from_email,
    )
    mail.send(msg)
    return len(recipient_list)


def _write_to_console(subject, message, from_email, recipient_list, html_message):
    stream = sys.stdout
    stream.write("Content-Type: text/plain; charset=\"utf-8\"\n")
    stream.write("MIME-Version: 1.0\n")
    stream.write("Content-Transfer-Encoding: 7bit\n")
    stream.write(f"Subject: {subject}\n")
    stream.write(f"From: {from_email}\n")
    stream.write("To: %s\n" % ", ".join(recipient_list))
    stream.write("\n")
    stream.write(message)
    if html_message:
        stream.write("\n")
        stream.write(html_message)
    stream.write("\n" + "-" * 79 + "\n")
    stream.flush()
