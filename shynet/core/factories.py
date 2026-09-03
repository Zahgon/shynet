import factory
from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy import select

from shynet.extensions import db

from .models import Service, User


class UserFactory(SQLAlchemyModelFactory):
    username = factory.Faker("user_name")
    email = factory.Faker("email")
    first_name = factory.Faker("name")

    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # `username` is unique; reuse an existing user like get_or_create did.
        password = kwargs.pop("password", None) or factory.Faker(
            "password",
            length=42,
            special_chars=True,
            digits=True,
            upper_case=True,
            lower_case=True,
        ).evaluate(None, None, extra={"locale": None})

        existing = db.session.scalar(
            select(model_class).where(model_class.username == kwargs["username"])
        )
        if existing is not None:
            return existing

        instance = model_class(*args, **kwargs)
        instance.set_password(password)
        db.session.add(instance)
        db.session.commit()
        return instance


class ServiceFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Service
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("company")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        instance = model_class(*args, **kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance
