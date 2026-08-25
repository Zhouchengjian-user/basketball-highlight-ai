from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LintIssue:
    code: str
    detail: str
    indexes: tuple[int, ...] = ()
