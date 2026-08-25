from __future__ import annotations

import os
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class VoiceProfileDefinition:
    """Public metadata plus the environment key holding a private provider ID."""

    id: str
    label: str
    provider: str
    voice_id_env: str
    commentary_profile: str
    commentary_profile_label: str


@dataclass(frozen=True)
class ResolvedVoiceProfile:
    """A server-only profile resolved for one processing job."""

    id: str
    label: str
    provider: str
    voice_id: str
    commentary_profile: str
    commentary_profile_label: str


class UnknownVoiceProfileError(ValueError):
    pass


class UnconfiguredVoiceProfileError(ValueError):
    pass


_VOICE_PROFILE_DEFINITIONS = (
    VoiceProfileDefinition(
        id="authorized_1",
        label="授权音色 1",
        provider="qwen_audio",
        voice_id_env="QWEN_AUDIO_VOICE_AUTHORIZED_1_ID",
        commentary_profile="broadcast_original",
        commentary_profile_label="原创专业篮球转播叙事",
    ),
)

VOICE_PROFILE_REGISTRY: Mapping[str, VoiceProfileDefinition] = MappingProxyType(
    {profile.id: profile for profile in _VOICE_PROFILE_DEFINITIONS}
)


def _configured_voice_id(profile: VoiceProfileDefinition) -> str:
    return os.getenv(profile.voice_id_env, "").strip()


def resolve_voice_profile(profile_id: str) -> ResolvedVoiceProfile:
    """Resolve an exact public alias without ever accepting a raw provider ID."""

    profile = VOICE_PROFILE_REGISTRY.get(profile_id.strip())
    if profile is None:
        raise UnknownVoiceProfileError("未知的授权音色")
    voice_id = _configured_voice_id(profile)
    if not voice_id:
        raise UnconfiguredVoiceProfileError(f"{profile.label}尚未在服务端配置")
    return ResolvedVoiceProfile(
        id=profile.id,
        label=profile.label,
        provider=profile.provider,
        voice_id=voice_id,
        commentary_profile=profile.commentary_profile,
        commentary_profile_label=profile.commentary_profile_label,
    )


def public_voice_profiles(
    provider_ready: Mapping[str, bool] | None = None,
) -> list[dict[str, object]]:
    """Return API-safe metadata; provider voice IDs and env keys stay server-side."""

    profiles: list[dict[str, object]] = []
    for profile in _VOICE_PROFILE_DEFINITIONS:
        configured = bool(_configured_voice_id(profile))
        ready = configured
        if provider_ready is not None:
            ready = ready and bool(provider_ready.get(profile.provider, False))
        profiles.append(
            {
                "id": profile.id,
                "label": profile.label,
                "provider": profile.provider,
                "ready": ready,
                "commentary_profile_label": profile.commentary_profile_label,
            }
        )
    return profiles


def authorized_voice_ids(provider: str) -> frozenset[str]:
    """Return only exact, configured provider IDs registered by server policy."""

    return frozenset(
        voice_id
        for profile in _VOICE_PROFILE_DEFINITIONS
        if profile.provider == provider
        if (voice_id := _configured_voice_id(profile))
    )
