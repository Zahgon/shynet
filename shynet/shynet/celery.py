from celery import Celery

from . import settings

app = Celery("shynet")

app.conf.update(
    broker_url=settings.CELERY_BROKER_URL,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    redis_socket_timeout=settings.CELERY_REDIS_SOCKET_TIMEOUT,
)

app.autodiscover_tasks(settings.INSTALLED_APPS)

_flask_app = None


def get_flask_app():
    """The Flask app tasks run inside; reuses the active one when there is one."""
    global _flask_app
    from flask import current_app, has_app_context

    if has_app_context():
        return current_app._get_current_object()
    if _flask_app is None:
        from .app import create_app

        _flask_app = create_app()
    return _flask_app


class FlaskTask(app.Task):
    def __call__(self, *args, **kwargs):
        with get_flask_app().app_context():
            return self.run(*args, **kwargs)


app.Task = FlaskTask
