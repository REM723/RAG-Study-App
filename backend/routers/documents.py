import io
import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from pypdf import PdfReader
from sqlalchemy.orm import Session

from .. import config, rag
from ..db import Document, SessionLocal, get_db
from ..schemas import DocumentOut, IngestStatus, UploadResult

log = logging.getLogger("rag")
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResult)
def upload(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    if not 1 <= len(files) <= config.MAX_FILES:
        raise HTTPException(400, f"Upload 1-{config.MAX_FILES} PDF files (got {len(files)})")

    # ponytail: fail-fast per file; earlier files in a failing batch stay saved (re-uploadable)
    out = []
    for f in files:
        name = Path(f.filename or "").name
        if not name.lower().endswith(".pdf"):
            raise HTTPException(400, f"{name or 'file'}: not a PDF")

        data = f.file.read()
        if len(data) > config.MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(400, f"{name}: exceeds {config.MAX_UPLOAD_MB}MB")

        dest = config.ARTIFACTS_DIR / name
        if dest.exists() or db.query(Document).filter_by(filename=name).first():
            raise HTTPException(409, f"{name}: already uploaded")

        try:
            if len(PdfReader(io.BytesIO(data)).pages) == 0:
                raise ValueError("no pages")
        except Exception:
            raise HTTPException(400, f"{name}: unreadable or corrupt PDF")

        dest.write_bytes(data)
        doc = Document(filename=name, status="pending")
        db.add(doc)
        db.commit()
        db.refresh(doc)
        out.append(DocumentOut.model_validate(doc))

    return {"uploaded": out}


def _run_ingest():
    """Background: rebuild FAISS, update per-document status."""
    db = SessionLocal()
    try:
        per_file = rag.rebuild_index()
        for d in db.query(Document).all():
            n = per_file.get(d.filename)
            if n:
                d.status, d.chunks, d.error = "completed", n, None
            else:
                d.status, d.error = "failed", "No chunks extracted"
        db.commit()
    except Exception as e:
        log.exception("Ingest failed")
        for d in db.query(Document).filter_by(status="processing").all():
            d.status, d.error = "failed", str(e)
        db.commit()
    finally:
        db.close()


@router.post("/ingest", response_model=IngestStatus)
def ingest(background: BackgroundTasks, db: Session = Depends(get_db)):
    docs = db.query(Document).all()
    if not docs:
        raise HTTPException(400, "No documents uploaded")
    for d in docs:
        d.status = "processing"
    db.commit()
    background.add_task(_run_ingest)
    return {"status": "processing", "documents": [DocumentOut.model_validate(d) for d in docs]}


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.id).all()


@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    (config.ARTIFACTS_DIR / doc.filename).unlink(missing_ok=True)
    db.delete(doc)
    db.commit()
    # ponytail: index keeps the deleted file's chunks until next ingest; drop it if nothing's left.
    # Re-ingest to fully remove a deleted file's chunks from retrieval.
    if db.query(Document).count() == 0:
        shutil.rmtree(config.FAISS_DIR, ignore_errors=True)
    return {"deleted": doc_id}
