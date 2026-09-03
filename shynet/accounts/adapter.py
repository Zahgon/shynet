"""Account adapter.

The single place that decides whether public sign-ups are allowed, renders the
account emails and dispatches them. `DashboardConfig`/`AccountsConfig.ready()`
patches `is_open_for_signup` when `ACCOUNT_SIGNUPS_ENABLED` is off, exactly as
before.
"""

from flask import render_template, request

from shynet import settings
from shynet.mail import send_mail


class DefaultAccountAdapter:
    def is_open_for_signup(self, request):
        return True

    def get_email_subject(self, template_name, context):
        subject = render_template(template_name, **context)
        subject = " ".join(subject.splitlines()).strip()
        return settings.ACCOUNT_EMAIL_SUBJECT_PREFIX + subject

    def send_mail(self, template_prefix, email, context):
        subject = self.get_email_subject(f"{template_prefix}_subject.txt", context)
        body = render_template(f"{template_prefix}_message.txt", **context)
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email])


_adapter = None


def get_adapter():
    global _adapter
    if _adapter is None:
        _adapter = DefaultAccountAdapter()
    return _adapter


def is_open_for_signup():
    return get_adapter().is_open_for_signup(request)


def user_display(user):
    return settings.ACCOUNT_USER_DISPLAY(user)
