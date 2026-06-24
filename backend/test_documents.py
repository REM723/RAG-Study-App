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
        # reject non-pdf
        r = c.post("/documents/upload", files={"files": ("x.txt", b"hi", "text/plain")})
        assert r.status_code == 400, r.text

        # reject >5 files
        many = [("files", (f"f{i}.pdf", pdf, "application/pdf")) for i in range(6)]
        assert c.post("/documents/upload", files=many).status_code == 400

        # accept a valid pdf
        r = c.post("/documents/upload", files={"files": ("good.pdf", pdf, "application/pdf")})
        assert r.status_code == 200, r.text
        assert r.json()["uploaded"][0]["status"] == "pending"

        # reject duplicate
        r = c.post("/documents/upload", files={"files": ("good.pdf", pdf, "application/pdf")})
        assert r.status_code == 409, r.text

        # reject corrupt pdf
        r = c.post("/documents/upload", files={"files": ("bad.pdf", b"not a pdf", "application/pdf")})
        assert r.status_code == 400, r.text

        # list shows the one good doc
        assert len(c.get("/documents").json()) == 1

    print("OK")


if __name__ == "__main__":
    demo()
