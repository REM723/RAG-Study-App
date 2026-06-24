def grade(questions, answers, desc_grader):
    """Grade a test. `answers` is {question_id(str): value}. `desc_grader(answer, rubric)
    -> (covered: list[bool], feedback: str)` is injected so this stays pure/testable.
    MCQ scoring is deterministic; descriptive scoring is 1 mark per covered rubric point.
    """
    sec = {"mcq": {"score": 0, "max": 0}, "descriptive": {"score": 0, "max": 0}}
    out = []
    for q in questions:
        ans = answers.get(str(q.id), answers.get(q.id))  # tolerate str or int keys
        base = {"id": q.id, "type": q.type, "question": q.question, "your_answer": ans,
                "source_file": q.source_file, "source_page": q.source_page}
        if q.type == "mcq":
            correct = ans is not None and ans == q.answer
            mark = 1 if correct else 0
            sec["mcq"]["score"] += mark
            sec["mcq"]["max"] += 1
            out.append({**base, "correct_answer": q.answer, "correct": correct,
                        "explanation": q.explanation, "marks": mark, "max": 1})
        else:
            rubric = q.rubric or []
            if ans:
                covered, feedback = desc_grader(ans, rubric)
            else:
                covered, feedback = [False] * len(rubric), "No answer provided."
            marks = sum(1 for c in covered if c)
            sec["descriptive"]["score"] += marks
            sec["descriptive"]["max"] += len(rubric)
            out.append({**base,
                        "rubric": [{"point": p, "covered": bool(c)} for p, c in zip(rubric, covered)],
                        "feedback": feedback, "marks": marks, "max": len(rubric)})
    total = sec["mcq"]["score"] + sec["descriptive"]["score"]
    mx = sec["mcq"]["max"] + sec["descriptive"]["max"]
    return {"total": total, "max": mx, "sections": sec, "questions": out}
