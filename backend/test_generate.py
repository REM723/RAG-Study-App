"""Self-check for question parsing/validation. Run: python -m backend.test_generate
No LLM/network calls."""
from .generate import parse_mcq, parse_descriptive, _norm


def demo():
    # valid mcq, even wrapped in prose + code fence
    raw = 'Here:\n```json\n{"question":"Q?","options":["a","b","c","d"],"answer":"b","explanation":"x"}\n```'
    q = parse_mcq(raw)
    assert q["answer"] == "b" and len(q["options"]) == 4

    # wrong option count rejected
    for bad in ('{"question":"Q","options":["a","b","c"],"answer":"a"}',
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

    print("OK")


if __name__ == "__main__":
    demo()
