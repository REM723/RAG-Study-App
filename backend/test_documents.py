"""Smoke check for upload validation. Run: python -m backend.test_documents
Hits no external APIs (upload/list only)."""
import io

from pypdf import PdfWriter


def _pdf_bytes():
    w = PdfWriter()
    w.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def demo():
    import tempfile, os
    # isolate DB + Artifacts so the test never touches real data
    from . import config
    tmp = tempfile.mkdtemp()
    config.DB_PATH = os.path.join(tmp, "t.db")
    config.ARTIFACTS_DIR = __import__("pathlib").Path(tmp) / "Artifacts"
    config.ARTIFACTS_DIR.mkdir()

    from fastapi.testclient import TestClient
    from .main import app

    pdf = _pdf_bytes()
    with TestClient(app) as c:
        uid = {"user_id": "1"}
        # reject non-pdf
        r = c.post("/documents/upload", files={"files": ("x.txt", b"hi", "text/plain")}, data=uid)
        assert r.status_code == 400, r.text

        # reject >5 files
        many = [("files", (f"f{i}.pdf", pdf, "application/pdf")) for i in range(6)]
        assert c.post("/documents/upload", files=many, data=uid).status_code == 400

        # accept a valid pdf
        r = c.post("/documents/upload", files={"files": ("good.pdf", pdf, "application/pdf")}, data=uid)
        assert r.status_code == 200, r.text
        assert r.json()["uploaded"][0]["status"] == "pending"

        # same filename can be re-uploaded — auto-suffixed, kept as a distinct copy
        r = c.post("/documents/upload", files={"files": ("good.pdf", pdf, "application/pdf")}, data=uid)
        assert r.status_code == 200, r.text
        assert r.json()["uploaded"][0]["filename"] == "good (1).pdf", r.text

        # a DIFFERENT user can also upload the same filename
        r = c.post("/documents/upload", files={"files": ("good.pdf", pdf, "application/pdf")}, data={"user_id": "2"})
        assert r.status_code == 200, r.text

        # reject corrupt pdf
        r = c.post("/documents/upload", files={"files": ("bad.pdf", b"not a pdf", "application/pdf")}, data=uid)
        assert r.status_code == 400, r.text

        # list is scoped per user (user 1 has good.pdf + good (1).pdf)
        assert len(c.get("/documents?user_id=1").json()) == 2
        assert len(c.get("/documents?user_id=2").json()) == 1

    print("OK")


if __name__ == "__main__":
    demo()
