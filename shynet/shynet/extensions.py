"""Shared extension instances.

They are created here (unbound) and initialised by `shynet.app.create_app`, so
that models, views and management commands can import them without triggering a
circular import.
"""

from flask_admin import Admin
from flask_babel import Babel
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from .csrf import CSRFProtect


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
mail = Mail()
babel = Babel()
csrf = CSRFProtect()


def make_admin(index_view=None):
    """A fresh admin site; Flask-Admin instances cannot be shared between apps."""
    return Admin(
        name="Shynet",
        template_mode="bootstrap4",
        url="/admin",
        index_view=index_view,
    )
