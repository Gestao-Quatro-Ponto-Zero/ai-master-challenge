from __future__ import annotations

import re


PATTERNS = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")),
    ("IP", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("LONG_ID", re.compile(r"\b\d{11,19}\b")),
    ("PHONE", re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")),
]


def mask_pii(text: str) -> tuple[str, dict[str, int]]:
    masked = text
    counts: dict[str, int] = {}
    for label, pattern in PATTERNS:
        masked, count = pattern.subn(f"[{label}_MASKED]", masked)
        counts[label] = count
    return masked, counts
