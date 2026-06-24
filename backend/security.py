"""Password hashing (stdlib PBKDF2) + at-rest file encryption (Fernet/AES)."""
import hashlib
import secrets

from cryptography.fernet import Fernet

from . import config

_ITER = 200_000

_fernet = None


def _f():
    global _fernet
    if _fernet is None:
        _fernet = Fernet(config.file_key())
    return _fernet


def encrypt_bytes(data: bytes) -> bytes:
    """Encrypt file bytes for storage at rest (authenticated AES)."""
    return _f().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    """Decrypt bytes previously produced by encrypt_bytes. Raises on tampering."""
    return _f().decrypt(token)


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
