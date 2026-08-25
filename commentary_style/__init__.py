from __future__ import annotations

from .basketball_live import (
    BASKETBALL_LIVE_SKILL,
    LIVE_SPOKEN_PATTERNS,
    BasketballLiveCommentarySkill,
)
from .broadcast_original import (
    MAX_SCENE_HINTS_PER_EVENT,
    MAX_SCENE_HINTS_TOTAL,
    ORIGINAL_BROADCAST_LEXICON,
    ORIGINAL_SCENE_PHRASES,
    ORIGINAL_PROFESSIONAL_BROADCAST,
    OriginalScenePhrase,
    OriginalProfessionalBroadcastProfile,
)
from .lint import (
    CRITICAL_RHYTHM_CODES,
    critical_rhythm_issues,
    lint_beats,
    minimum_natural_chars,
    spoken_length,
    spoken_units,
)


_STYLE_REGISTRY = {"basketball_live": BASKETBALL_LIVE_SKILL}
_DELIVERY_PROFILE_REGISTRY = {
    "broadcast_original": ORIGINAL_PROFESSIONAL_BROADCAST,
}


def load_style(name: str = "basketball_live") -> BasketballLiveCommentarySkill:
    try:
        return _STYLE_REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"未知解说风格包：{name}") from exc


def load_delivery_profile(name: str) -> OriginalProfessionalBroadcastProfile:
    try:
        return _DELIVERY_PROFILE_REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"未知解说表达配置：{name}") from exc


__all__ = [
    "CRITICAL_RHYTHM_CODES",
    "BasketballLiveCommentarySkill",
    "MAX_SCENE_HINTS_PER_EVENT",
    "MAX_SCENE_HINTS_TOTAL",
    "LIVE_SPOKEN_PATTERNS",
    "ORIGINAL_BROADCAST_LEXICON",
    "ORIGINAL_SCENE_PHRASES",
    "OriginalScenePhrase",
    "OriginalProfessionalBroadcastProfile",
    "critical_rhythm_issues",
    "lint_beats",
    "load_delivery_profile",
    "load_style",
    "minimum_natural_chars",
    "spoken_length",
    "spoken_units",
]
