"""Self-check for the generic admin CRUD. Run: python -m backend.test_admin (no network)."""
import os
import tempfile


def demo():
    from . import config
    tmp = tempfile.mkdtemp()
    config.DB_PATH = os.path.join(tmp, "t.db")
    config.ARTIFACTS_DIR = __import__("pathlib").Path(tmp) / "Artifacts"
    config.ARTIFACTS_DIR.mkdir()

    from fastapi.testclient import TestClient
    from .main import app

    H = {"X-Admin-Password": config.ADMIN_PASSWORD}

    with TestClient(app) as c:
        # admin auth: missing/wrong password -> 401
        assert c.get("/admin/users").status_code == 401
        assert c.get("/admin/users", headers={"X-Admin-Password": "nope"}).status_code == 401
        assert c.get("/admin/_check", headers=H).json()["ok"] is True

        # unknown entity -> 404
        assert c.get("/admin/nope", headers=H).status_code == 404

        # create a user
        r = c.post("/admin/users", headers=H, json={"name": "Ryan", "email": "r@x.com", "role": "student"})
        assert r.status_code == 200, r.text
        uid = r.json()["id"]

        # duplicate email -> 400 (unique constraint)
        assert c.post("/admin/users", headers=H, json={"name": "Dup", "email": "r@x.com"}).status_code == 400

        # int coercion: file_size sent as string lands as int
        r = c.post("/admin/documents", headers=H, json={"user_id": str(uid), "filename": "a.pdf", "file_size": "123"})
        assert r.status_code == 200 and r.json()["file_size"] == 123, r.text

        # JSON column round-trips
        r = c.post("/admin/rubrics", headers=H, json={"question_id": 1, "scoring_points": ["p1", "p2"], "max_marks": 2})
        assert r.json()["scoring_points"] == ["p1", "p2"]

        # list + delete
        assert len(c.get("/admin/users", headers=H).json()) == 1
        assert c.delete(f"/admin/users/{uid}", headers=H).status_code == 200
        assert len(c.get("/admin/users", headers=H).json()) == 0

    print("OK")


if __name__ == "__main__":
    demo()
