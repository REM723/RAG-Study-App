"""Self-check for question parsing/validation. Run: python -m backend.test_generate
No LLM/network calls."""
import numpy as np
from .generate import parse_mcq, parse_descriptive, _norm, _too_similar


def demo():
    # valid mcq, even wrapped in prose + code fence
    raw = 'Here:\n```json\n{"question":"Q?","options":["a","b","c","d"],"answer":"b","explanation":"x"}\n```'
    q = parse_mcq(raw)
    assert q["answer"] == "b" and len(q["options"]) == 4

    # model can refuse a junk chunk
    for skip in ('{"skip": true}', 'sure:\n{"skip": true}'):
        try:
            parse_mcq(skip); assert False, "skip should raise"
        except ValueError:
            pass

    # 2 options is valid (don't force 4)
    assert len(parse_mcq('{"question":"Q","options":["a","b"],"answer":"a"}')["options"]) == 2

    # out-of-range option count rejected (1 or 5+)
    for bad in ('{"question":"Q","options":["a"],"answer":"a"}',
                '{"question":"Q","options":["a","b","c","d","e"],"answer":"a"}',
                '{"question":"Q","options":["a","b","c","d"],"answer":"z"}'):  # answer not in options
        try:
            parse_mcq(bad); assert False, "should have raised"
        except ValueError:
            pass

    # descriptive rubric
    d = parse_descriptive('{"question":"Explain X","rubric":["p1","p2","p3"]}')
    assert d["rubric"] == ["p1", "p2", "p3"]

    # empty rubric rejected
    try:
        parse_descriptive('{"question":"Q","rubric":[]}'); assert False
    except ValueError:
        pass

    # dedup key normalizes whitespace/case
    assert _norm("  What  IS  x? ") == "what is x?"

    # semantic dedup: near-parallel vectors are duplicates, orthogonal ones aren't
    a, near, far = np.array([1.0, 0]), np.array([0.99, 0.14]), np.array([0.0, 1.0])
    assert _too_similar(near, [a])
    assert not _too_similar(far, [a])

    print("OK")


if __name__ == "__main__":
    demo()
