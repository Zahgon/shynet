"""Email address bookkeeping for accounts.

`EmailAddress` and `EmailConfirmation` carry the same data (and table names) the
account system stored previously: the set of addresses attached to a user,
which one is primary, whether each is verified, and the outstanding confirmation
keys.
"""

from secrets import token_urlsafe

from sqlalchemy import func, select

from shynet import timezone
from shynet.dbtypes import DateTimeUTC, big_integer
from shynet.extensions import db


def _default_key():
    return token_urlsafe(32)[:64]


class EmailAddress(db.Model):
    __tablename__ = "account_emailaddress"

    id = db.Column(big_integer(), primary_key=True, autoincrement=True)
    user_id = db.Column(
        big_integer(),
        db.ForeignKey("core_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = db.Column(db.String(254), nullable=False, unique=True)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    primary = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship(
        "User",
        backref=db.backref(
            "emailaddress_set",
            lazy="dynamic",
            cascade="all, delete",
            passive_deletes=True,
        ),
    )

    def __str__(self):
        return self.email

    @property
    def pk(self):
        return self.id

    @classmethod
    def lookup(cls, email):
        """Case-insensitively find an address (the `email__iexact` lookup)."""
        return db.session.scalar(
            select(cls).where(func.lower(cls.email) == (email or "").lower())
        )

    def set_as_primary(self, conditional=False):
        old_primary = db.session.scalar(
            select(EmailAddress).where(
                EmailAddress.user_id == self.user_id,
                EmailAddress.primary.is_(True),
            )
        )
        if old_primary is not None:
            if conditional:
                return False
            old_primary.primary = False
            db.session.add(old_primary)
        self.primary = True
        db.session.add(self)
        db.session.commit()
        return True


class EmailConfirmation(db.Model):
    __tablename__ = "account_emailconfirmation"

    id = db.Column(big_integer(), primary_key=True, autoincrement=True)
    email_address_id = db.Column(
        big_integer(),
        db.ForeignKey("account_emailaddress.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created = db.Column(DateTimeUTC(), nullable=False, default=timezone.now)
    sent = db.Column(DateTimeUTC(), nullable=True)
    key = db.Column(db.String(64), nullable=False, unique=True, default=_default_key)

    email_address = db.relationship(
        "EmailAddress",
        backref=db.backref(
            "emailconfirmation_set",
            lazy="dynamic",
            cascade="all, delete",
            passive_deletes=True,
        ),
    )

    def __str__(self):
        return f"confirmation for {self.email_address}"

    @property
    def pk(self):
        return self.id

    @classmethod
    def create(cls, email_address):
        confirmation = cls(email_address=email_address, key=_default_key())
        db.session.add(confirmation)
        db.session.commit()
        return confirmation

    @classmethod
    def from_key(cls, key):
        confirmation = db.session.scalar(select(cls).where(cls.key == key))
        if confirmation is None or confirmation.key_expired:
            return None
        return confirmation

    @property
    def key_expired(self):
        from shynet import settings

        expiration = self.sent or self.created
        return expiration + timezone.timedelta(
            seconds=settings.ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_SECONDS
        ) <= timezone.now()

    def confirm(self):
        if self.key_expired:
            return None
        email_address = self.email_address
        email_address.verified = True
        email_address.set_as_primary(conditional=True)
        db.session.add(email_address)
        db.session.commit()
        return email_address
