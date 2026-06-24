"""Self-check for grading math. Run: python -m backend.test_scoring  (no network)."""
from types import SimpleNamespace

from .scoring import grade


def Q(**kw):
    kw.setdefault("explanation", "")
    kw.setdefault("source_file", "f.pdf")
    kw.setdefault("source_page", 1)
    return SimpleNamespace(**kw)


def demo():
    questions = [
        Q(id=1, type="mcq", question="Q1", options=["a", "b"], answer="a", rubric=None),
        Q(id=2, type="mcq", question="Q2", options=["a", "b"], answer="b", rubric=None),
        Q(id=3, type="descriptive", question="Q3", options=None, answer=None,
          rubric=["p1", "p2", "p3"]),
    ]
    answers = {"1": "a", "2": "a", "3": "some answer"}  # q1 right, q2 wrong

    # fake grader: covers first 2 of 3 points
    fake = lambda ans, rubric: ([True, True, False], "ok")
    r = grade(questions, answers, fake)

    assert r["sections"]["mcq"] == {"score": 1, "max": 2}, r["sections"]
    assert r["sections"]["descriptive"] == {"score": 2, "max": 3}, r["sections"]
    assert r["total"] == 3 and r["max"] == 5
    # mcq detail
    q2 = next(q for q in r["questions"] if q["id"] == 2)
    assert q2["correct"] is False and q2["correct_answer"] == "b"
    # unanswered descriptive scores 0 without calling grader
    r2 = grade([questions[2]], {}, lambda a, rb: (_ for _ in ()).throw(AssertionError("called")))
    assert r2["total"] == 0 and r2["questions"][0]["feedback"] == "No answer provided."

    print("OK")


if __name__ == "__main__":
    demo()
