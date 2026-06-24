"""Self-check for password hashing. Run: python -m backend.test_security (no network)."""
from .security import hash_password, verify_password, encrypt_bytes, decrypt_bytes


def demo():
    h = hash_password("hunter2")
    assert h != "hunter2" and "$" in h          # never store plaintext; salted
    assert verify_password("hunter2", h)         # correct password verifies
    assert not verify_password("wrong", h)       # wrong password fails
    assert hash_password("hunter2") != h         # per-call salt -> different hash
    assert not verify_password("x", "")          # empty/garbage stored -> False

    # file encryption at rest
    blob = b"%PDF-1.4 secret student content"
    enc = encrypt_bytes(blob)
    assert enc != blob                            # ciphertext != plaintext on disk
    assert decrypt_bytes(enc) == blob             # round-trips
    try:
        decrypt_bytes(enc[:-1] + b"x")            # tampered -> raises
        assert False, "tamper should raise"
    except Exception:
        pass
    print("OK")


if __name__ == "__main__":
    demo()
