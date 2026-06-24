import io
import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pypdf import PdfReader
from sqlalchemy.orm import Session

from .. import config, rag, security
from ..db import Chunk, Document, SessionLocal, get_db
from ..schemas import DocumentOut, IngestStatus, UploadResult

log = logging.getLogger("rag")
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResult)
def upload(files: list[UploadFile] = File(...), user_id: int = Form(...),
           db: Session = Depends(get_db)):
    if not 1 <= len(files) <= config.MAX_FILES:
        raise HTTPException(400, f"Upload 1-{config.MAX_FILES} PDF files (got {len(files)})")

    folder = config.user_artifacts(user_id)
    # ponytail: fail-fast per file; earlier files in a failing batch stay saved (re-uploadable)
    out = []
    for f in files:
        name = Path(f.filename or "").name
        if not name.lower().endswith(".pdf"):
            raise HTTPException(400, f"{name or 'file'}: not a PDF")

        data = f.file.read()
        if len(data) > config.MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(400, f"{name}: exceeds {config.MAX_UPLOAD_MB}MB")

        try:
            if len(PdfReader(io.BytesIO(data)).pages) == 0:
                raise ValueError("no pages")
        except Exception:
            raise HTTPException(400, f"{name}: unreadable or corrupt PDF")

        # allow re-uploading the same name: auto-suffix so each copy stays distinct
        stem, suffix = Path(name).stem, Path(name).suffix
        cand, i = name, 1
        while (folder / cand).exists() or db.query(Document).filter_by(user_id=user_id, filename=cand).first():
            cand = f"{stem} ({i}){suffix}"
            i += 1
        name = cand

        dest = folder / name
        dest.write_bytes(security.encrypt_bytes(data))  # encrypted at rest
        doc = Document(filename=name, status="pending", file_size=len(data), user_id=user_id)
        db.add(doc)
        db.commit()
        db.refresh(doc)
        out.append(DocumentOut.model_validate(doc))

    return {"uploaded": out}


def _run_ingest(user_id):
    """Background: rebuild this user's FAISS index, update their documents' status."""
    db = SessionLocal()
    try:
        docs = db.query(Document).filter_by(user_id=user_id).all()
        docmap = {d.filename: d.id for d in docs}
        # remove orphan PDFs (no matching Document row) so they aren't indexed
        for f in config.user_artifacts(user_id).glob("*.pdf"):
            if f.name not in docmap:
                f.unlink(missing_ok=True)

        per_file, chunks = rag.rebuild_index(user_id)
        doc_ids = [d.id for d in docs]
        # refresh this user's Chunk rows to match the rebuilt index
        if doc_ids:
            db.query(Chunk).filter(Chunk.document_id.in_(doc_ids)).delete(synchronize_session=False)
        for c in chunks:
            f = c.metadata.get("source_file")
            did = docmap.get(f)
            if did is None:
                continue  # guard: never insert a chunk with NULL document_id
            db.add(Chunk(
                document_id=did,
                text=c.page_content,
                page_number=c.metadata.get("page"),
                chapter=c.metadata.get("chapter"),
                embedding_ref=f"{f}#{c.metadata.get('chunk_index')}",
            ))
        for d in docs:
            n = per_file.get(d.filename)
            if n:
                d.status, d.chunks, d.error = "completed", n, None
            else:
                d.status, d.error = "failed", "No chunks extracted"
        db.commit()
    except Exception as e:
        db.rollback()  # clear the failed transaction before writing the failure status
        log.exception("Ingest failed")
        msg = str(e) or e.__class__.__name__  # some exceptions (e.g. InvalidToken) stringify empty
        for d in db.query(Document).filter_by(user_id=user_id, status="processing").all():
            d.status, d.error = "failed", msg
        db.commit()
    finally:
        db.close()


@router.post("/ingest", response_model=IngestStatus)
def ingest(user_id: int, background: BackgroundTasks, db: Session = Depends(get_db)):
    docs = db.query(Document).filter_by(user_id=user_id).all()
    if not docs:
        raise HTTPException(400, "No documents uploaded")
    for d in docs:
        d.status = "processing"
    db.commit()
    background.add_task(_run_ingest, user_id)
    return {"status": "processing", "documents": [DocumentOut.model_validate(d) for d in docs]}


@router.get("", response_model=list[DocumentOut])
def list_documents(user_id: int, db: Session = Depends(get_db)):
    return db.query(Document).filter_by(user_id=user_id).order_by(Document.id).all()


@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    (config.user_artifacts(doc.user_id) / doc.filename).unlink(missing_ok=True)
    db.query(Chunk).filter_by(document_id=doc_id).delete()
    db.delete(doc)
    db.commit()
    # ponytail: index keeps the deleted file's chunks until next ingest; drop it if the user has none left.
    if db.query(Document).filter_by(user_id=doc.user_id).count() == 0:
        shutil.rmtree(config.user_index(doc.user_id), ignore_errors=True)
    return {"deleted": doc_id}
