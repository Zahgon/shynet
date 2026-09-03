"""Application exceptions.

The replacements for the framework exception types Shynet's code raised and
caught.
"""


class ValidationError(Exception):
    """Raised when a model or form value fails validation."""

    def __init__(self, message, code=None, params=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.params = params

    @property
    def messages(self):
        if isinstance(self.message, (list, tuple)):
            return list(self.message)
        return [self.message]

    def __str__(self):
        return str(self.message)


class NotSupportedError(Exception):
    """Raised when the configured database backend lacks a required feature."""


class PermissionDenied(Exception):
    """Raised when the current user is not allowed to perform an action."""


class ObjectDoesNotExist(Exception):
    """Raised when a lookup for a single object finds nothing."""


class MissingObjectIdentifier(Exception):
    """Raised when a view has no primary key to look an object up with."""
