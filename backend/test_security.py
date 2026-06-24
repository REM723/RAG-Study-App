"""Self-check for password hashing. Run: python -m backend.test_security (no network)."""
from .security import hash_password, verify_password


def demo():
    h = hash_password("hunter2")
    assert h != "hunter2" and "$" in h          # never store plaintext; salted
    assert verify_password("hunter2", h)         # correct password verifies
    assert not verify_password("wrong", h)       # wrong password fails
    assert hash_password("hunter2") != h         # per-call salt -> different hash
    assert not verify_password("x", "")          # empty/garbage stored -> False
    print("OK")


if __name__ == "__main__":
    demo()
