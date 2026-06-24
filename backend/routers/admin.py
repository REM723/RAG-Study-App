"""Generic CRUD over the data-model tables. ponytail: one router for all 8 entities
instead of hand-coding list/create/delete per table. Minimal validation (DB constraints
only) — this is an admin/data-model surface, not a public API."""
import shutil

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import config
from ..db import Attempt, Chunk, Document, Evaluation, Question, Rubric, Test, User, get_db


def check_admin(x_admin_password: str = Header(None)):
    if x_admin_password != config.ADMIN_PASSWORD:
        raise HTTPException(401, "Invalid admin password")

ENTITIES = {
    "users": User,
    "documents": Document,
    "chunks": Chunk,
    "questions": Question,
    "rubrics": Rubric,
    "tests": Test,
    "attempts": Attempt,
    "evaluations": Evaluation,
}

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(check_admin)])


@router.get("/_check")
def check():
    return {"ok": True}


@router.post("/reset")
def reset(db: Session = Depends(get_db)):
    """Wipe everything: all tables, the FAISS index, and uploaded PDFs."""
    for m in ENTITIES.values():
        db.query(m).delete()
    db.commit()
    shutil.rmtree(config.FAISS_DIR, ignore_errors=True)
    for p in config.ARTIFACTS_DIR.glob("*.pdf"):
        p.unlink(missing_ok=True)
    return {"reset": True}


def _model(entity):
    m = ENTITIES.get(entity)
    if not m:
        raise HTTPException(404, f"Unknown entity '{entity}'")
    return m


def _row(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def _coerce(model, key, val):
    col = model.__table__.columns.get(key)
    if col is not None and isinstance(col.type, Integer) and isinstance(val, str) and val.strip():
        try:
            return int(val)
        except ValueError:
            pass
    return val


@router.get("/{entity}")
def list_rows(entity: str, db: Session = Depends(get_db)):
    m = _model(entity)
    return [_row(o) for o in db.query(m).order_by(m.id).all()]


@router.post("/{entity}")
def create_row(entity: str, data: dict, db: Session = Depends(get_db)):
    m = _model(entity)
    cols = {c.name for c in m.__table__.columns} - {"id"}
    payload = {k: _coerce(m, k, v) for k, v in data.items() if k in cols and v not in (None, "")}
    obj = m(**payload)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(400, f"Constraint failed: {e.orig}")
    db.refresh(obj)
    return _row(obj)


@router.delete("/{entity}/{row_id}")
def delete_row(entity: str, row_id: int, db: Session = Depends(get_db)):
    m = _model(entity)
    obj = db.get(m, row_id)
    if not obj:
        raise HTTPException(404, "Not found")
    db.delete(obj)
    db.commit()
    return {"deleted": row_id}
