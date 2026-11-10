"""Placeholder renderer: fills {key} in a template from the facts, formatting by type.

Money "US$ 5.482", dates "31/03/2018", integers as is, lists "A, B e C".
"""
import re
import sys

sys.dont_write_bytecode = True
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from facts import DATE, LIST, MONEY  # noqa: E402

PLACEHOLDER = re.compile(r"\{([^{}]*)\}")


def fmt_money(v):
    if float(v) == int(v):
        return "US$ " + f"{int(v):,}".replace(",", ".")
    whole, cents = f"{v:,.2f}".split(".")
    return "US$ " + whole.replace(",", ".") + "," + cents


def fmt_date(s):
    y, m, d = s.split("-")
    return f"{d}/{m}/{y}"


def fmt_list(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " e " + items[-1]


def fmt(key, value):
    if key in MONEY:
        return fmt_money(value)
    if key in DATE:
        return fmt_date(value)
    if key in LIST:
        return fmt_list(value)
    return str(value)


SENTENCE_START = re.compile(r"(^|[.!?] +)([a-zà-ÿ])")


def capitalise(text):
    """Capital letter at the start of the text and after '. ', '! ' and '? '."""
    return SENTENCE_START.sub(lambda m: m.group(1) + m.group(2).upper(), text)


def render(template, facts):
    """Fill the template; raises KeyError on a placeholder that is not in facts."""
    return capitalise(PLACEHOLDER.sub(lambda m: fmt(m.group(1), facts[m.group(1)]), template))


def render_mask(template, facts):
    """Like render, plus one flag per character: True when it was typed in the template."""
    text, mask, pos = "", [], 0
    for m in PLACEHOLDER.finditer(template):
        lit = template[pos:m.start()]
        fill = fmt(m.group(1), facts[m.group(1)])
        text += lit + fill
        mask += [True] * len(lit) + [False] * len(fill)
        pos = m.end()
    lit = template[pos:]
    text += lit
    mask += [True] * len(lit)
    return text, mask
