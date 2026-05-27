from __future__ import annotations

import re

MCQ_PATTERN = re.compile(r"(?mi)^\s*([A-Za-z])\s*[.)\]:\-]\s*.+")
ANSWER_PATTERN = re.compile(r"\b([A-Za-z])\b")


def is_mcq(text: str) -> bool:
    matches = MCQ_PATTERN.findall(text)
    unique_labels = {match.upper() for match in matches}
    return len(unique_labels) >= 2


def normalize_mcq_answer(answer: str) -> str:
    matches = ANSWER_PATTERN.findall(answer.strip())
    if matches:
        return " ".join([m.upper() for m in matches])
    return answer.strip()
