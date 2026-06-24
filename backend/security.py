"""Password hashing with the stdlib — no bcrypt/passlib dependency.
PBKDF2-HMAC-SHA256, per-user salt, stored as "salt$hash" (hex)."""
import hashlib
import secrets

_ITER = 200_000


def hash_password(pw: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), _ITER).hex()
    return f"{salt}${h}"


def verify_password(pw: str, stored: str) -> bool:
    if not stored or "$" not in stored:
        return False
    salt, h = stored.split("$", 1)
    test = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), _ITER).hex()
    return secrets.compare_digest(test, h)
