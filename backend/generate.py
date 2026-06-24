import json
import logging
import random
import re

from langchain_groq import ChatGroq

from . import config, rag

log = logging.getLogger("rag")

_llm = None
_grader = None


def llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(groq_api_key=config.GROQ_API_KEY, model=config.MODEL_ID, temperature=0.4)
    return _llm


def grader_llm():
    global _grader
    if _grader is None:  # deterministic grading
        _grader = ChatGroq(groq_api_key=config.GROQ_API_KEY, model=config.MODEL_ID, temperature=0)
    return _grader


MCQ_PROMPT = """Based ONLY on the context below, write one multiple-choice question.
Return STRICT JSON, nothing else:
{{"question": "...", "options": ["a","b","c","d"], "answer": "<exact text of the correct option>", "explanation": "..."}}
Exactly 4 options. "answer" must be verbatim one of the options.

Context:
{context}"""

DESC_PROMPT = """Based ONLY on the context below, write one descriptive question and a model
answer broken into distinct marking points (one idea per point).
Return STRICT JSON, nothing else:
{{"question": "...", "rubric": ["point 1", "point 2", "..."]}}
Use 2 to 6 rubric points.

Context:
{context}"""


def _extract_json(text):
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise ValueError("no JSON found")
        return json.loads(m.group(0))


def _norm(q):
    return re.sub(r"\s+", " ", q).strip().lower()


def parse_mcq(text):
    obj = _extract_json(text)
    opts = obj["options"]
    if not isinstance(opts, list) or len(opts) != 4:
        raise ValueError("need exactly 4 options")
    opts = [str(o).strip() for o in opts]
    answer = str(obj["answer"]).strip()
    if answer not in opts:
        raise ValueError("answer not among options")
    return {
        "question": str(obj["question"]).strip(),
        "options": opts,
        "answer": answer,
        "explanation": str(obj.get("explanation", "")).strip(),
    }


def parse_descriptive(text):
    obj = _extract_json(text)
    rubric = obj["rubric"]
    if not isinstance(rubric, list) or not 1 <= len(rubric) <= 8:
        raise ValueError("rubric must have 1-8 points")
    return {
        "question": str(obj["question"]).strip(),
        "rubric": [str(p).strip() for p in rubric],
    }


def _usable_chunks():
    store = rag.load_index()
    if store is None:
        raise ValueError("No index. Upload and ingest documents first.")
    chunks = [d for d in store.docstore._dict.values() if len(d.page_content) > 200]
    if not chunks:
        raise ValueError("No usable content in the index.")
    random.shuffle(chunks)
    return chunks


def _generate(count, prompt, parser):
    """One question per chunk so every question traces to a single source chunk."""
    out, seen = [], set()
    for d in _usable_chunks():
        if len(out) >= count:
            break
        try:
            raw = llm().invoke(prompt.format(context=d.page_content)).content
            q = parser(raw)
        except Exception as e:
            log.warning("skip chunk: %s", e)
            continue
        key = _norm(q["question"])
        if key in seen:
            continue
        seen.add(key)
        q["source_file"] = d.metadata.get("source_file")
        q["source_page"] = d.metadata.get("page")
        out.append(q)
    return out


def generate_mcqs(count):
    return _generate(count, MCQ_PROMPT, parse_mcq)


def generate_descriptive(count):
    return _generate(count, DESC_PROMPT, parse_descriptive)


GRADE_PROMPT = """Grade a student's answer against a rubric. For each rubric point, decide
whether the student's answer covers it (be fair but require the idea to actually be present).
Return STRICT JSON, nothing else:
{{"covered": [<true or false per point, in order>], "feedback": "1-2 sentence summary"}}

Rubric points:
{points}

Student answer:
{answer}"""


def grade_descriptive(answer, rubric):
    """Return (covered: list[bool] aligned to rubric, feedback: str)."""
    if not rubric:
        return [], ""
    points = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(rubric))
    try:
        raw = grader_llm().invoke(GRADE_PROMPT.format(points=points, answer=answer)).content
        obj = _extract_json(raw)
        covered = [bool(c) for c in obj.get("covered", [])]
        feedback = str(obj.get("feedback", "")).strip()
    except Exception as e:
        log.warning("grade failed: %s", e)
        return [False] * len(rubric), "Could not grade automatically."
    covered = (covered + [False] * len(rubric))[: len(rubric)]  # align to rubric length
    return covered, feedback
