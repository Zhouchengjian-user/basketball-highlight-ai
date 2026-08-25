from __future__ import annotations

import math
import re
from collections.abc import Sequence

from .types import LintIssue


CRITICAL_RHYTHM_CODES = {
    "FIVE_CHAR_MARCH",
    "SHORT_CADENCE_GRID",
    "MONOTONOUS_LENGTH",
    "SHORT_BEAT_MARCH",
    "MISSING_FULL_SENTENCE",
    "FRAGMENT",
}


def spoken_length(text: str) -> int:
    return len(re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", text))


def spoken_units(text: str) -> list[str]:
    return [
        unit
        for unit in re.split(r"[，,。！？!?；;：:\n]+", text)
        if spoken_length(unit) >= 2
    ]


def minimum_natural_chars(beat_count: int) -> int:
    if beat_count <= 0:
        return 0
    long_count = max(1, math.ceil(beat_count * 0.2))
    short_count = min(max(1, math.floor(beat_count * 0.28)), beat_count - long_count)
    medium_count = max(0, beat_count - long_count - short_count)
    return long_count * 13 + short_count * 4 + medium_count * 7


def lint_beats(texts: Sequence[str]) -> list[LintIssue]:
    cleaned = [text.strip() for text in texts if text and text.strip()]
    if not cleaned:
        return [LintIssue("EMPTY", "没有可口播的解说句")]

    issues: list[LintIssue] = []
    beat_lengths = [spoken_length(text) for text in cleaned]
    units = [unit for text in cleaned for unit in spoken_units(text)]
    unit_lengths = [spoken_length(unit) for unit in units]

    exact_five = [index for index, length in enumerate(unit_lengths) if length == 5]
    five_run = 0
    longest_five_run = 0
    for length in unit_lengths:
        five_run = five_run + 1 if length == 5 else 0
        longest_five_run = max(longest_five_run, five_run)
    if longest_five_run >= 3 or (
        len(unit_lengths) >= 4 and len(exact_five) / len(unit_lengths) >= 0.5
    ):
        issues.append(
            LintIssue(
                "FIVE_CHAR_MARCH",
                "多个五字分句排成整齐口号，缺少自然呼吸变化",
                tuple(exact_five),
            )
        )

    short_grid_indexes: tuple[int, ...] = ()
    for start in range(max(0, len(unit_lengths) - 3)):
        window = unit_lengths[start : start + 4]
        if (
            all(4 <= length <= 7 for length in window)
            and max(window) - min(window) <= 2
            and window[0] == window[2]
            and window[1] == window[3]
        ):
            short_grid_indexes = tuple(range(start, start + 4))
            break
    if short_grid_indexes and not any(
        issue.code == "FIVE_CHAR_MARCH" for issue in issues
    ):
        issues.append(
            LintIssue(
                "SHORT_CADENCE_GRID",
                "连续分句都落在相近的四到七字拍子上，听起来像整齐口号",
                short_grid_indexes,
            )
        )

    if len(beat_lengths) >= 6:
        sorted_lengths = sorted(beat_lengths)
        central = sorted_lengths[1:-1]
        if central and max(central) - min(central) <= 2:
            issues.append(
                LintIssue(
                    "MONOTONOUS_LENGTH",
                    "绝大多数解说段长度几乎相同",
                    tuple(range(len(cleaned))),
                )
            )
        required_full = max(1, math.ceil(len(cleaned) * 0.2))
        full_indexes = [index for index, length in enumerate(beat_lengths) if length >= 13]
        if len(full_indexes) < required_full:
            issues.append(
                LintIssue(
                    "MISSING_FULL_SENTENCE",
                    "缺少能交代球权和动作关系的完整口语句",
                    tuple(full_indexes),
                )
            )

    short_run: list[int] = []
    longest_short_run: list[int] = []
    for index, length in enumerate(beat_lengths):
        if length <= 7:
            short_run.append(index)
            if len(short_run) > len(longest_short_run):
                longest_short_run = short_run[:]
        else:
            short_run = []
    if len(longest_short_run) >= 3:
        issues.append(
            LintIssue(
                "SHORT_BEAT_MARCH",
                "连续短句过多，听起来像逐条播报",
                tuple(longest_short_run),
            )
        )

    fragment_pattern = re.compile(
        r"推进传|空切跑|起跳投|刷网进|接球稳|投篮偏|断球下|补防扰|"
        r"抛投出|打进篮|控球过|果断投|命中敌|背身打|跳投中|发快攻|"
        r"攻势起|悬念(?:瞬间)?满|(?:红队|白队|黑队|蓝队|\d+号)带[，。！？]"
    )
    fragment_indexes = [
        index for index, text in enumerate(cleaned) if fragment_pattern.search(text)
    ]
    if fragment_indexes:
        issues.append(
            LintIssue(
                "FRAGMENT",
                "句子为了凑长度省掉了必要的动词、助词或动作关系",
                tuple(fragment_indexes),
            )
        )

    openings = [re.sub(r"^[，。！？\s]+", "", text)[:3] for text in cleaned]
    repeated: list[int] = []
    for index in range(2, len(openings)):
        if openings[index] and openings[index] == openings[index - 1] == openings[index - 2]:
            repeated.extend([index - 2, index - 1, index])
    if repeated:
        issues.append(
            LintIssue(
                "REPEATED_OPENING",
                "连续多句用同一个主语或起手式重新开场",
                tuple(sorted(set(repeated))),
            )
        )
    return issues


def critical_rhythm_issues(texts: Sequence[str]) -> list[LintIssue]:
    return [issue for issue in lint_beats(texts) if issue.code in CRITICAL_RHYTHM_CODES]
