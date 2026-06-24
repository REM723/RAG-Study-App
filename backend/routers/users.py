from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import security
from ..db import Attempt, Test, User, get_db

router = APIRouter(prefix="/users", tags=["users"])


class UserIn(BaseModel):
    name: str
    email: str
    password: str
    role: str = "student"


class LoginIn(BaseModel):
    email: str
    password: str


def _u(o):
    return {"id": o.id, "name": o.name, "email": o.email, "role": o.role}


@router.get("")
def list_users(db: Session = Depends(get_db)):
    return [_u(o) for o in db.query(User).order_by(User.id).all()]


@router.post("")
def create_user(body: UserIn, db: Session = Depends(get_db)):
    """Sign up. Email must be unique; password is hashed before storage."""
    if db.query(User).filter_by(email=body.email).first():
        raise HTTPException(409, "Email already registered — log in instead")
    if len(body.password) < 4:
        raise HTTPException(400, "Password must be at least 4 characters")
    u = User(name=body.name, email=body.email, role=body.role,
             password_hash=security.hash_password(body.password))
    db.add(u)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Could not create user")
    db.refresh(u)
    return _u(u)


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=body.email).first()
    if not u:
        raise HTTPException(401, "Invalid email or password")
    if not u.password_hash:
        # legacy account created before passwords existed: first login sets it
        u.password_hash = security.hash_password(body.password)
        db.commit()
    elif not security.verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return _u(u)


@router.get("/{user_id}/tests")
def user_tests(user_id: int, db: Session = Depends(get_db)):
    """A user's tests with their attempt score — powers the dashboard/history."""
    out = []
    for t in db.query(Test).filter_by(user_id=user_id).order_by(Test.id.desc()).all():
        a = db.query(Attempt).filter_by(test_id=t.id).first()
        done = bool(a and a.submitted)
        out.append({
            "id": t.id,
            "seq": t.seq,
            "question_count": t.question_count,
            "status": t.status,
            "created_at": t.created_at,
            "submitted": done,
            "score": a.score if done else None,
            "max": (a.result or {}).get("max") if done else None,
        })
    return out
