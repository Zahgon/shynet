"""Password hashing.

Shynet's stored password hashes use the `pbkdf2_sha256$<iterations>$<salt>$<hash>`
encoding, so the algorithm is implemented here directly rather than delegating to
a library with a different format; existing password hashes keep working.
"""

import base64
import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600000
SALT_ENTROPY = 128

UNUSABLE_PASSWORD_PREFIX = "!"
UNUSABLE_PASSWORD_SUFFIX_LENGTH = 40

RANDOM_STRING_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def get_random_string(length, allowed_chars=RANDOM_STRING_CHARS):
    return "".join(secrets.choice(allowed_chars) for _ in range(length))


def salt():
    char_count = int(SALT_ENTROPY / 5.95)  # log2(len(RANDOM_STRING_CHARS))
    return get_random_string(char_count, RANDOM_STRING_CHARS)


def _pbkdf2(password, salt_value, iterations):
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt_value.encode("utf-8"), iterations
    )
    return base64.b64encode(digest).decode("ascii").strip()


def make_password(password, salt_value=None, iterations=ITERATIONS):
    if password is None:
        return make_unusable_password()
    salt_value = salt_value or salt()
    hashed = _pbkdf2(password, salt_value, iterations)
    return f"{ALGORITHM}${iterations}${salt_value}${hashed}"


def check_password(password, encoded):
    if password is None or not encoded or encoded.startswith(UNUSABLE_PASSWORD_PREFIX):
        return False
    try:
        algorithm, iterations, salt_value, _hashed = encoded.split("$", 3)
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False
    candidate = make_password(password, salt_value, int(iterations))
    return hmac.compare_digest(candidate.encode("utf-8"), encoded.encode("utf-8"))


def make_unusable_password():
    return UNUSABLE_PASSWORD_PREFIX + get_random_string(
        UNUSABLE_PASSWORD_SUFFIX_LENGTH
    )


def is_password_usable(encoded):
    return encoded is None or not encoded.startswith(UNUSABLE_PASSWORD_PREFIX)


def needs_update(encoded):
    try:
        _algorithm, iterations, _salt, _hashed = encoded.split("$", 3)
    except (AttributeError, ValueError):
        return False
    return int(iterations) != ITERATIONS
