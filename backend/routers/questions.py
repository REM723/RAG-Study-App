from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import generate
from ..db import Question, Rubric, get_db
from ..schemas import CountRequest, QuestionOut

router = APIRouter(prefix="/questions", tags=["questions"])


def _persist(db, items, qtype, user_id):
    rows = [
        Question(
            user_id=user_id,
            type=qtype,
            question=i["question"],
            options=i.get("options"),
            answer=i.get("answer"),
            explanation=i.get("explanation"),
            rubric=i.get("rubric"),
            source_file=i["source_file"],
            source_page=i["source_page"],
        )
        for i in items
    ]
    db.add_all(rows)
    db.commit()
    for r in rows:
        db.refresh(r)
    return rows


@router.post("/mcq", response_model=list[QuestionOut])
def mcq(req: CountRequest, db: Session = Depends(get_db)):
    try:
        items = generate.generate_mcqs(req.count, req.user_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _persist(db, items, "mcq", req.user_id)


@router.post("/descriptive", response_model=list[QuestionOut])
def descriptive(req: CountRequest, db: Session = Depends(get_db)):
    try:
        items = generate.generate_descriptive(req.count, req.user_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    rows = _persist(db, items, "descriptive", req.user_id)
    for r in rows:  # one Rubric row per descriptive question
        if r.rubric:
            db.add(Rubric(question_id=r.id, scoring_points=r.rubric, max_marks=len(r.rubric)))
    db.commit()
    return rows
