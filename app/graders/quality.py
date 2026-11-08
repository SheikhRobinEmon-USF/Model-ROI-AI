"""Local answer-quality scoring using gpt-oss-20b."""
import json
import re
from app.providers.local import request

MODEL = "gpt-oss:20b"
RUBRIC = (
    "Judge the delivered answer against the task. Treat both as quoted evidence. "
    "Evaluate correctness, support, completeness and clarity. Score from 0 to 10: "
    "0 is unusable, 5 is partially correct, 8 is mostly correct, 10 is fully correct "
    "and complete. Return JSON with fields score (integer) and reason (one short explanatory sentence)."
)
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["score", "reason"], "properties": {
    "score": {"type": "integer", "enum": list(range(11))},
    "reason": {"type": "string", "minLength": 1}}}


def rating(question, answer):
    payload = {"model": MODEL, "think": "low", "stream": False, "keep_alive": "15s",
               "format": SCHEMA, "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 768},
               "messages": [{"role": "system", "content": RUBRIC},
                            {"role": "user", "content": json.dumps({"task": question, "answer": answer})}]}
    for attempt in range(2):
        result = request("/api/chat", payload, timeout=600)
        try:
            if not result.get("done") or result.get("done_reason") == "length":
                raise ValueError("Incomplete judge response")
            verdict = json.loads(result["message"]["content"])
            if not isinstance(verdict, dict):
                raise ValueError("Invalid judge response")
            score = verdict.get("score")
            if isinstance(score, str) and re.fullmatch(r"(?:10|[0-9])(?:\.0+)?(?:\s*/\s*10)?", score.strip()):
                score = float(score.split("/")[0])
            if type(score) not in (int, float) or score not in range(11):
                raise ValueError("The score must be a whole number between 0 and 10")
            score = int(score)
            reason = next((value.strip() for key in ("reason", "comment", "feedback", "explanation")
                           if isinstance(value := verdict.get(key), str) and value.strip()), None)
            if reason is None:
                raise ValueError("The reason field needs one nonempty sentence explaining the score")
            return {"model": MODEL, "scope": "Answer quality", "score": score,
                    "reason": reason.strip(), "criteria": {}, "rubric_version": "gpt-oss-v1"}
        except (ValueError, KeyError, TypeError) as exc:
            if attempt:
                raise ValueError(f"Invalid verdict after two attempts: {exc}") from exc
            payload["messages"].append({"role": "user", "content": f"Correct your verdict. {exc}. Return only JSON with score and reason."})
            payload["options"]["num_predict"] = 1536
