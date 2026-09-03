"""Logging helpers.

The handlers and filters referenced by `shynet.settings.LOGGING`.
"""

import logging


class RequireDebugTrue(logging.Filter):
    def filter(self, record):
        from . import settings

        return settings.DEBUG


class AdminEmailHandler(logging.Handler):
    """Mails `settings.ADMINS` when an ERROR-level record is emitted."""

    def emit(self, record):
        try:
            from .mail import send_mail
            from . import settings

            subject = f"{record.levelname}: {record.getMessage()}"[:989]
            message = self.format(record)
            recipients = self._admin_emails()
            if not recipients:
                return
            send_mail(subject, message, settings.SERVER_EMAIL, recipients)
        except Exception:  # pragma: no cover - never let logging break the app
            self.handleError(record)

    def _admin_emails(self):
        from . import settings

        return [email for _name, email in settings.ADMINS]


def configure(config):
    """Apply the `LOGGING` dict via `logging.config.dictConfig`."""
    import logging.config

    logging.config.dictConfig(config)
