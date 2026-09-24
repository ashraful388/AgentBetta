"""Version parsing and comparison for the update checker.

Handles both PEP 440-style versions (``0.2.0a1``) and common release tags
(``v0.2.0-alpha.1``, ``0.2.1``).
"""

from __future__ import annotations

import re

_NUM_RE = re.compile(r"(\d+(?:\.\d+)*)")
_PRE_RE = re.compile(r"(alpha|beta|rc|pre|dev|a|b)\.?(\d*)", re.IGNORECASE)
_PRE_RANK = {"dev": 0, "alpha": 1, "a": 1, "beta": 2, "b": 2, "pre": 3, "rc": 3}
_FINAL_RANK = 99


def parse_version(text: str) -> tuple[tuple[int, ...], tuple[int, int]]:
    """Return ``(numbers, pre_release)`` for a version string.

    ``pre_release`` is ``(rank, number)`` where a final release ranks higher
    than any pre-release.
    """

    value = (text or "").strip().lstrip("vV")
    match = _NUM_RE.search(value)
    numbers = tuple(int(part) for part in match.group(1).split(".")) if match else (0,)
    rest = value[match.end():] if match else value
    pre = _PRE_RE.search(rest.split("+", 1)[0])
    if pre:
        rank = _PRE_RANK.get(pre.group(1).lower(), 1)
        number = int(pre.group(2) or 0)
        return numbers, (rank, number)
    return numbers, (_FINAL_RANK, 0)


def is_prerelease(text: str) -> bool:
    return parse_version(text)[1][0] != _FINAL_RANK


def _pad(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    length = max(len(a), len(b))
    return a + (0,) * (length - len(a)), b + (0,) * (length - len(b))


def compare_versions(a: str, b: str) -> int:
    """Return -1 if a<b, 0 if equal, 1 if a>b."""

    a_nums, a_pre = parse_version(a)
    b_nums, b_pre = parse_version(b)
    a_nums, b_nums = _pad(a_nums, b_nums)
    if a_nums != b_nums:
        return -1 if a_nums < b_nums else 1
    if a_pre != b_pre:
        return -1 if a_pre < b_pre else 1
    return 0


def is_newer(candidate: str, current: str) -> bool:
    return compare_versions(candidate, current) > 0
