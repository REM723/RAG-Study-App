import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import generate, scoring
from ..db import Attempt, Evaluation, Question, Test, get_db
from ..schemas import AttemptRequest, TestQuestionOut, TestRequest, TestView

router = APIRouter(prefix="/tests", tags=["tests"])


def _pick(db, qtype, n, user_id):
    if n <= 0:
        return []
    rows = db.query(Question).filter_by(type=qtype, user_id=user_id).all()
    if len(rows) < n:
        raise HTTPException(
            400, f"Only {len(rows)} {qtype} questions available; need {n}. Generate more first."
        )
    return random.sample(rows, n)


def _view(db, test):
    qs = db.query(Question).filter(Question.id.in_(test.question_ids)).all()
    order = {qid: i for i, qid in enumerate(test.question_ids)}
    qs.sort(key=lambda q: order[q.id])
    return {"id": test.id, "seq": test.seq, "questions": [TestQuestionOut.model_validate(q) for q in qs]}


def _attempt(db, test_id):
    a = db.query(Attempt).filter_by(test_id=test_id).first()
    if not a:
        a = Attempt(test_id=test_id, answers={})
        db.add(a)
    return a


@router.post("", response_model=TestView)
def create_test(req: TestRequest, db: Session = Depends(get_db)):
    if req.mcq_count + req.descriptive_count == 0:
        raise HTTPException(400, "A test needs at least one question")
    qs = _pick(db, "mcq", req.mcq_count, req.user_id) + _pick(db, "descriptive", req.descriptive_count, req.user_id)
    seq = db.query(Test).filter_by(user_id=req.user_id).count() + 1
    test = Test(question_ids=[q.id for q in qs], question_count=len(qs), user_id=req.user_id, seq=seq)
    db.add(test)
    db.commit()
    db.refresh(test)
    return _view(db, test)


@router.get("/{test_id}", response_model=TestView)
def get_test(test_id: int, db: Session = Depends(get_db)):
    test = db.get(Test, test_id)
    if not test:
        raise HTTPException(404, "Test not found")
    return _view(db, test)


@router.post("/{test_id}/attempt")
def save_attempt(test_id: int, req: AttemptRequest, db: Session = Depends(get_db)):
    if not db.get(Test, test_id):
        raise HTTPException(404, "Test not found")
    a = _attempt(db, test_id)
    if a.submitted:
        raise HTTPException(409, "Test already submitted")
    if req.user_id:
        a.user_id = req.user_id
    a.answers = {**(a.answers or {}), **req.answers}
    db.commit()
    return {"saved": True, "answers": a.answers}


@router.post("/{test_id}/submit")
def submit(test_id: int, req: AttemptRequest, db: Session = Depends(get_db)):
    test = db.get(Test, test_id)
    if not test:
        raise HTTPException(404, "Test not found")
    a = _attempt(db, test_id)
    if a.submitted:
        raise HTTPException(409, "Test already submitted")
    answers = {**(a.answers or {}), **req.answers}
    if req.user_id:
        a.user_id = req.user_id
    qs = db.query(Question).filter(Question.id.in_(test.question_ids)).all()
    result = scoring.grade(qs, answers, generate.grade_descriptive)
    a.answers, a.submitted, a.result, a.score = answers, True, result, result["total"]
    db.commit()  # ensures a.id for the Evaluation row
    db.add(Evaluation(
        attempt_id=a.id,
        per_question_score=[{"id": q["id"], "marks": q["marks"], "max": q["max"]}
                            for q in result["questions"]],
        feedback="; ".join(q["feedback"] for q in result["questions"] if q.get("feedback")),
        total_score=result["total"],
    ))
    db.commit()
    return result


@router.get("/{test_id}/result")
def result(test_id: int, db: Session = Depends(get_db)):
    a = db.query(Attempt).filter_by(test_id=test_id).first()
    if not a or not a.submitted:
        raise HTTPException(400, "Test not submitted yet")
    return a.result
