from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import threading
import traceback
import uuid
from dataclasses import dataclass, replace
from pathlib import Path

from dotenv import load_dotenv, set_key

load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from video_pipeline import (
    CommentaryBeat,
    Settings,
    TTS_VOICES,
    _pick_macos_voice,
    commentary_plan_from_dict,
    normalize_game_context,
    resolve_ffmpeg,
    run_pipeline,
)
from voice_profiles import (
    UnconfiguredVoiceProfileError,
    UnknownVoiceProfileError,
    public_voice_profiles,
    resolve_voice_profile,
)


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / ".data"
STATIC_DIR = ROOT / "static"
DATA_DIR.mkdir(exist_ok=True)

ALLOWED_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm"}
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "300")) * 1024 * 1024
STYLES = {"hype", "pro", "fun"}
VOICE_ENGINES = {"qwen_audio", "minimax"}

app = FastAPI(title="篮球高光 AI 解说", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

jobs: dict[str, dict] = {}
job_runtime: dict[str, "JobRuntime"] = {}
jobs_lock = threading.Lock()


@dataclass(frozen=True)
class JobRuntime:
    video_path: Path
    output_dir: Path
    style: str
    context: str
    game_context: dict[str, str]
    settings: Settings


class AiSettingsRequest(BaseModel):
    api_key: str


class CommentaryBeatRevision(BaseModel):
    time: float
    text: str
    event_kind: str = "other"


class CommentaryRevisionRequest(BaseModel):
    beats: list[CommentaryBeatRevision]


EDITABLE_EVENT_KINDS = {
    "possession",
    "pass",
    "drive",
    "shot",
    "made_shot",
    "missed_shot",
    "block",
    "steal",
    "rebound",
    "transition",
    "stoppage",
    "other",
}
HARD_RESULT_KINDS = {
    "made_shot",
    "missed_shot",
    "block",
    "steal",
    "rebound",
    "stoppage",
}
JOB_STATE_FILENAME = "job.json"
RUNTIME_STATE_FILENAME = "runtime.json"


def _write_json_atomic(path: Path, payload: dict) -> None:
    """Persist small local state without ever exposing a half-written JSON file."""
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _runtime_state_payload(runtime: JobRuntime) -> dict:
    # API keys and provider-side voice IDs are deliberately excluded.  They are
    # reloaded from the user's local .env when the service starts again.
    return {
        "source_filename": runtime.video_path.name,
        "style": runtime.style,
        "context": runtime.context,
        "game_context": runtime.game_context,
        "voice_engine": runtime.settings.tts_provider,
        "voice_profile_id": runtime.settings.voice_profile_id or None,
    }


def _persist_runtime(runtime: JobRuntime) -> None:
    try:
        if runtime.output_dir.is_dir():
            _write_json_atomic(
                runtime.output_dir / RUNTIME_STATE_FILENAME,
                _runtime_state_payload(runtime),
            )
    except OSError:
        # A persistence failure must not abort an otherwise healthy render.
        traceback.print_exc()


def _job_output_dir_locked(job_id: str) -> Path | None:
    runtime = job_runtime.get(job_id)
    candidate = runtime.output_dir if runtime else DATA_DIR / job_id
    return candidate if candidate.is_dir() else None


def _persist_job_locked(job_id: str) -> None:
    job = jobs.get(job_id)
    output_dir = _job_output_dir_locked(job_id)
    if job is None or output_dir is None:
        return
    try:
        _write_json_atomic(output_dir / JOB_STATE_FILENAME, dict(job))
    except (OSError, TypeError, ValueError):
        traceback.print_exc()


def _settings_from_runtime_state(payload: dict) -> Settings:
    base_settings = Settings()
    profile_id = str(payload.get("voice_profile_id") or "").strip()
    if profile_id:
        profile = resolve_voice_profile(profile_id)
        return replace(
            base_settings,
            tts_provider=profile.provider,
            qwen_audio_tts_voice=profile.voice_id,
            voice_profile_id=profile.id,
            voice_profile_label=profile.label,
            commentary_profile=profile.commentary_profile,
            commentary_profile_label=profile.commentary_profile_label,
        )
    voice_engine = str(payload.get("voice_engine") or base_settings.tts_provider)
    if voice_engine not in VOICE_ENGINES:
        voice_engine = base_settings.tts_provider
    return replace(
        base_settings,
        tts_provider=voice_engine,
        voice_profile_id="",
        voice_profile_label="",
        commentary_profile="",
        commentary_profile_label="",
    )


def _restore_runtime(output_dir: Path) -> JobRuntime | None:
    state_path = output_dir / RUNTIME_STATE_FILENAME
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return None
        source_filename = Path(str(payload.get("source_filename") or "")).name
        source_path = output_dir / source_filename
        style = str(payload.get("style") or "hype")
        context = str(payload.get("context") or "")
        raw_game_context = payload.get("game_context")
        game_context = normalize_game_context(
            raw_game_context if isinstance(raw_game_context, dict) else {}
        )
        if (
            not source_filename
            or not source_path.is_file()
            or style not in STYLES
            or len(context) > 500
        ):
            return None
        settings = _settings_from_runtime_state(payload)
    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        UnknownVoiceProfileError,
        UnconfiguredVoiceProfileError,
    ):
        return None
    return JobRuntime(
        video_path=source_path,
        output_dir=output_dir,
        style=style,
        context=context,
        game_context=game_context,
        settings=settings,
    )


def load_persisted_jobs() -> int:
    """Recover completed and interrupted local jobs after a service restart."""
    restored = 0
    if not DATA_DIR.is_dir():
        return restored
    for state_path in DATA_DIR.glob(f"*/{JOB_STATE_FILENAME}"):
        output_dir = state_path.parent
        job_id = output_dir.name
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", job_id):
            continue
        try:
            job = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(job, dict) or str(job.get("id") or "") != job_id:
            continue
        runtime = _restore_runtime(output_dir)
        status = str(job.get("status") or "")
        if status in {"queued", "processing"}:
            job.update(
                status="failed",
                message="服务曾在生成过程中退出，可从已保存的检查点继续",
                progress=0,
                retryable=runtime is not None,
                failed_stage=job.get("stage") or "unknown",
            )
        elif status == "completed":
            highlight_path = output_dir / "highlight.mp4"
            if not highlight_path.is_file() or highlight_path.stat().st_size == 0:
                job.update(
                    status="failed",
                    message="已完成任务的成片文件缺失，需要重新生成",
                    progress=0,
                    retryable=runtime is not None,
                    failed_stage="render",
                )
        elif status == "failed":
            job["retryable"] = bool(job.get("retryable") and runtime is not None)
        elif status != "completed":
            continue
        if job.get("status") == "completed":
            job.setdefault("video_url", f"/api/jobs/{job_id}/video")
            job.setdefault("download_url", f"/api/jobs/{job_id}/video?download=1")
            job.setdefault("subtitle_url", f"/api/jobs/{job_id}/subtitles")
        jobs[job_id] = job
        if runtime is not None:
            job_runtime[job_id] = runtime
        _persist_job_locked(job_id)
        restored += 1
    return restored


def update_job(job_id: str, **changes) -> None:
    with jobs_lock:
        jobs[job_id].update(changes)
        _persist_job_locked(job_id)


def process_job(
    job_id: str,
    video_path: Path,
    output_dir: Path,
    style: str,
    context: str,
    game_context: dict[str, str],
    settings: Settings,
    resume_from_checkpoint: bool = False,
) -> None:
    def progress(message: str, percent: int) -> None:
        if percent < 16:
            stage = "upload"
        elif percent < 60:
            stage = "analysis"
        elif percent < 80:
            stage = "voice"
        else:
            stage = "render"
        update_job(
            job_id,
            status="processing",
            message=message,
            progress=percent,
            stage=stage,
            retryable=False,
        )

    try:
        result = run_pipeline(
            video_path,
            output_dir,
            style,
            context,
            progress,
            settings,
            game_context=game_context,
            resume_from_checkpoint=resume_from_checkpoint,
        )
        output_path = Path(str(result.get("output_path") or ""))
        subtitle_path = output_dir / "commentary.vtt"
        update_job(job_id, stage="render")
        if not output_path.is_file() or output_path.stat().st_size == 0:
            raise RuntimeError("视频合成结束但没有生成可用的 MP4 成片")
        if not subtitle_path.is_file() or subtitle_path.stat().st_size == 0:
            raise RuntimeError("视频合成结束但没有生成可用的字幕文件")
        result.setdefault("game_context", game_context)
        result.setdefault("voice_profile_id", settings.voice_profile_id or None)
        result.setdefault("voice_profile_label", settings.voice_profile_label or None)
        result.setdefault(
            "commentary_profile_label",
            settings.commentary_profile_label or None,
        )
        update_job(
            job_id,
            status="completed",
            message="成片已生成",
            progress=100,
            stage="completed",
            retryable=False,
            failed_stage=None,
            result={
                key: value
                for key, value in result.items()
                if key not in {"output_path", "analysis_fallback_reason"}
            },
            video_url=f"/api/jobs/{job_id}/video",
            download_url=f"/api/jobs/{job_id}/video?download=1",
            subtitle_url=f"/api/jobs/{job_id}/subtitles",
        )
    except Exception as exc:
        traceback.print_exc()
        with jobs_lock:
            failed_stage = jobs.get(job_id, {}).get("stage", "unknown")
        update_job(
            job_id,
            status="failed",
            message=str(exc),
            progress=0,
            retryable=True,
            failed_stage=failed_stage,
        )


def _validated_revision_beats(
    payload: CommentaryRevisionRequest,
    duration: float,
) -> list[CommentaryBeat]:
    if not 1 <= len(payload.beats) <= 32:
        raise HTTPException(400, "事件时间轴需要保留 1–32 句解说")
    beats: list[CommentaryBeat] = []
    for index, item in enumerate(payload.beats):
        if not math.isfinite(item.time):
            raise HTTPException(400, f"第 {index + 1} 个事件时间不正确")
        time_value = round(max(0.08, min(duration - 0.1, item.time)), 2)
        text = " ".join(item.text.split()).strip()
        if not 1 <= len(text) <= 80:
            raise HTTPException(400, f"第 {index + 1} 句解说需要 1–80 个字")
        if any(ord(character) < 32 for character in text):
            raise HTTPException(400, f"第 {index + 1} 句解说包含不支持的字符")
        event_kind = item.event_kind.strip()
        if event_kind not in EDITABLE_EVENT_KINDS:
            raise HTTPException(400, f"第 {index + 1} 个事件类型不支持")
        hard_anchor = event_kind in HARD_RESULT_KINDS
        beats.append(
            CommentaryBeat(
                time=time_value,
                text=text,
                event_id=f"user-revision-{index + 1}",
                event_kind=event_kind,
                event_start=max(0.0, time_value - (0.18 if hard_anchor else 0.0)),
                anchor_time=time_value,
                confidence=1.0,
                hard_anchor=hard_anchor,
            )
        )
    beats.sort(key=lambda beat: beat.time)
    return beats


def process_revision(
    job_id: str,
    runtime: JobRuntime,
    revision_dir: Path,
) -> None:
    def progress(message: str, percent: int) -> None:
        stage = "voice" if percent < 80 else "render"
        update_job(
            job_id,
            status="processing",
            revision_status="processing",
            message=message,
            progress=max(60, percent),
            stage=stage,
        )

    with jobs_lock:
        previous_result = dict(jobs.get(job_id, {}).get("result") or {})
        previous_revision_count = int(
            jobs.get(job_id, {}).get("revision_count") or 0
        )
    try:
        result = run_pipeline(
            runtime.video_path,
            revision_dir,
            runtime.style,
            runtime.context,
            progress,
            runtime.settings,
            game_context=runtime.game_context,
            resume_from_checkpoint=True,
        )
        artifact_names = (
            "analysis-plan.json",
            "commentary.srt",
            "commentary.vtt",
            "voice-timeline.wav",
            "plan.json",
            "highlight.mp4",
        )
        artifact_sources = {
            filename: revision_dir / filename for filename in artifact_names
        }
        for filename, source in artifact_sources.items():
            if not source.exists() or source.stat().st_size == 0:
                raise RuntimeError(f"修正版缺少必要文件：{filename}")

        staged_artifacts: dict[str, Path] = {}
        for filename, source in artifact_sources.items():
            temporary = runtime.output_dir / f".{filename}.{revision_dir.name}.tmp"
            shutil.copyfile(source, temporary)
            staged_artifacts[filename] = temporary
        try:
            # Keep the previous MP4 available until every supporting artifact
            # has been copied successfully.  The visible video is replaced last.
            for filename in artifact_names:
                staged_artifacts[filename].replace(runtime.output_dir / filename)
        finally:
            for temporary in staged_artifacts.values():
                if temporary.exists():
                    temporary.unlink()

        result.setdefault("game_context", runtime.game_context)
        result.setdefault("voice_profile_id", runtime.settings.voice_profile_id or None)
        result.setdefault("voice_profile_label", runtime.settings.voice_profile_label or None)
        result.setdefault(
            "commentary_profile_label",
            runtime.settings.commentary_profile_label or None,
        )
        result["revision_count"] = previous_revision_count + 1
        result["revision_source"] = "user_timeline_correction"
        public_result = {
            key: value
            for key, value in result.items()
            if key not in {"output_path", "analysis_fallback_reason"}
        }
        update_job(
            job_id,
            status="completed",
            revision_status="completed",
            revision_error=None,
            revision_count=previous_revision_count + 1,
            message="修正版成片已生成",
            progress=100,
            stage="completed",
            result=public_result,
            video_url=f"/api/jobs/{job_id}/video",
            download_url=f"/api/jobs/{job_id}/video?download=1",
            subtitle_url=f"/api/jobs/{job_id}/subtitles",
        )
    except Exception as exc:
        traceback.print_exc()
        update_job(
            job_id,
            status="completed",
            revision_status="failed",
            revision_error=str(exc),
            message="修正版生成失败，原成片仍然保留",
            progress=100,
            stage="completed",
            result=previous_result,
        )


load_persisted_jobs()


@app.get("/")
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/styles.css", include_in_schema=False)
def styles() -> FileResponse:
    return FileResponse(STATIC_DIR / "styles.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def frontend_script() -> FileResponse:
    return FileResponse(STATIC_DIR / "app.js", media_type="text/javascript")


@app.get("/favicon.svg", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/system")
def system_status() -> dict:
    settings = Settings()
    ffmpeg_error = ""
    try:
        ffmpeg = resolve_ffmpeg(settings.ffmpeg_binary)
        encoders = subprocess.run(
            [ffmpeg, "-hide_banner", "-encoders"], capture_output=True, text=True, check=False, timeout=10
        )
        missing_encoders = [name for name in ("libx264", "aac") if name not in encoders.stdout]
        ffmpeg_ready = encoders.returncode == 0 and not missing_encoders
        if not ffmpeg_ready:
            ffmpeg_error = "缺少视频编码器：" + "、".join(missing_encoders or ["未知"])
    except Exception as exc:
        ffmpeg_ready = False
        ffmpeg_error = str(exc)

    tts_provider = settings.tts_provider.lower()
    engine_status = {
        "qwen_audio": {
            "ready": bool(settings.qwen_api_key),
            "label": "原创赛事男声 · Qwen Audio Plus",
            "reason": "" if settings.qwen_api_key else "尚未配置百炼 API Key",
        },
        "minimax": {
            "ready": bool(settings.qwen_api_key) and settings.minimax_enabled,
            "label": "成熟播报男声 · MiniMax 2.8 HD",
            "reason": (
                ""
                if settings.qwen_api_key and settings.minimax_enabled
                else "百炼账号尚未开通 MiniMax 2.8 HD"
                if settings.qwen_api_key
                else "尚未配置百炼 API Key"
            ),
        },
    }
    if tts_provider == "macos":
        voice = _pick_macos_voice(settings.macos_tts_voice)
        tts_ready = shutil.which("say") is not None and voice is not None
        tts_label = f"macOS 本地语音 · {voice}" if voice else "没有可用的中文语音"
    elif tts_provider == "qwen_audio":
        tts_ready = bool(settings.qwen_api_key)
        tts_label = engine_status["qwen_audio"]["label"] if tts_ready else "请先配置百炼 API Key"
    elif tts_provider == "minimax":
        tts_ready = bool(engine_status["minimax"]["ready"])
        tts_label = (
            engine_status["minimax"]["label"]
            if tts_ready
            else str(engine_status["minimax"]["reason"])
        )
    elif tts_provider == "qwen":
        if settings.qwen_api_key:
            voices = settings.qwen_tts_voice or "/".join(dict.fromkeys(TTS_VOICES.values()))
            tts_ready = True
            tts_label = f"Qwen3-TTS · {voices}"
        else:
            tts_ready = False
            tts_label = "请先配置百炼 API Key"
    elif tts_provider == "openai_compatible":
        tts_ready = bool(settings.tts_api_key)
        tts_label = "OpenAI 兼容云端语音"
    else:
        tts_ready = False
        tts_label = f"未知配音引擎：{tts_provider}"

    return {
        "ready": ffmpeg_ready and tts_ready,
        "ffmpeg_ready": ffmpeg_ready,
        "ffmpeg_error": ffmpeg_error,
        "tts_ready": tts_ready,
        "tts_label": tts_label,
        "tts_provider": tts_provider,
        "tts_engines": engine_status,
        "voices": public_voice_profiles(
            {
                provider: bool(status["ready"])
                for provider, status in engine_status.items()
            }
        ),
        "ai_enabled": bool(settings.qwen_api_key),
        "ai_mode": "qwen" if settings.qwen_api_key else "demo",
        "ai_model": settings.qwen_video_model if settings.qwen_api_key else None,
        "ai_text_model": settings.qwen_model if settings.qwen_api_key else None,
        "analysis_engine": "omni_av",
        "analysis_fallback_available": settings.qwen_video_fallback,
        "min_video_seconds": settings.min_seconds,
        "max_video_seconds": settings.max_seconds,
    }


@app.post("/api/settings/ai")
def save_ai_settings(payload: AiSettingsRequest, request: Request) -> dict:
    client_host = request.client.host if request.client else ""
    if client_host not in {"127.0.0.1", "::1", "testclient"}:
        raise HTTPException(403, "只允许在本机配置 AI 密钥")
    api_key = payload.api_key.strip()
    if not 10 <= len(api_key) <= 512:
        raise HTTPException(400, "密钥长度不正确")

    env_path = ROOT / ".env"
    if not env_path.exists():
        shutil.copyfile(ROOT / ".env.example", env_path)
    set_key(str(env_path), "QWEN_API_KEY", api_key, quote_mode="always")
    os.environ["QWEN_API_KEY"] = api_key
    settings = Settings()
    return {
        "ok": True,
        "ai_enabled": True,
        "ai_model": settings.qwen_video_model,
        "ai_text_model": settings.qwen_model,
    }


@app.post("/api/jobs", status_code=202)
async def create_job(
    video: UploadFile = File(...),
    style: str = Form("hype"),
    context: str = Form(""),
    player_name: str = Form(""),
    player_marker: str = Form(""),
    team_name: str = Form(""),
    opponent_name: str = Form(""),
    score_text: str = Form(""),
    voice_engine: str = Form("qwen_audio"),
    voice_profile: str | None = Form(None),
) -> dict:
    suffix = Path(video.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(400, "仅支持 MP4、MOV、M4V 或 WebM 视频")
    if style not in STYLES:
        raise HTTPException(400, "未知的解说风格")
    if len(context) > 500:
        raise HTTPException(400, "补充信息不能超过 500 字")
    try:
        game_context = normalize_game_context(
            {
                "player_name": player_name,
                "player_marker": player_marker,
                "team_name": team_name,
                "opponent_name": opponent_name,
                "score_text": score_text,
            }
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    base_settings = Settings()
    requested_profile = voice_profile.strip() if voice_profile else ""
    if requested_profile:
        try:
            resolved_profile = resolve_voice_profile(requested_profile)
        except UnknownVoiceProfileError as exc:
            raise HTTPException(400, str(exc)) from exc
        except UnconfiguredVoiceProfileError as exc:
            raise HTTPException(400, str(exc)) from exc
        voice_engine = resolved_profile.provider
        settings = replace(
            base_settings,
            tts_provider=resolved_profile.provider,
            qwen_audio_tts_voice=resolved_profile.voice_id,
            voice_profile_id=resolved_profile.id,
            voice_profile_label=resolved_profile.label,
            commentary_profile=resolved_profile.commentary_profile,
            commentary_profile_label=resolved_profile.commentary_profile_label,
        )
    else:
        if voice_engine not in VOICE_ENGINES:
            raise HTTPException(400, "未知的配音引擎")
        settings = replace(
            base_settings,
            tts_provider=voice_engine,
            voice_profile_id="",
            voice_profile_label="",
            commentary_profile="",
            commentary_profile_label="",
        )
    if not settings.qwen_api_key:
        raise HTTPException(400, "所选云端配音需要先配置阿里云百炼 API Key")
    if voice_engine == "minimax" and not settings.minimax_enabled:
        raise HTTPException(400, "MiniMax 2.8 HD 尚未在当前百炼账号中开通")
    job_id = uuid.uuid4().hex
    output_dir = DATA_DIR / job_id
    output_dir.mkdir(parents=True)
    video_path = output_dir / f"source{suffix}"
    size = 0
    try:
        with video_path.open("wb") as target:
            while chunk := await video.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, f"视频不能超过 {MAX_UPLOAD_BYTES // 1024 // 1024} MB")
                target.write(chunk)
    except Exception:
        if video_path.exists():
            video_path.unlink()
        raise
    finally:
        await video.close()

    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "message": "视频已上传，等待处理",
            "progress": 2,
            "stage": "upload",
            "retryable": False,
            "filename": video.filename,
            "voice_engine": voice_engine,
            "voice_profile_id": settings.voice_profile_id or None,
            "voice_profile_label": settings.voice_profile_label or None,
            "commentary_profile_label": settings.commentary_profile_label or None,
            "game_context": game_context,
        }
        job_runtime[job_id] = JobRuntime(
            video_path=video_path,
            output_dir=output_dir,
            style=style,
            context=context,
            game_context=dict(game_context),
            settings=settings,
        )
        _persist_runtime(job_runtime[job_id])
        _persist_job_locked(job_id)
    worker = threading.Thread(
        target=process_job,
        args=(job_id, video_path, output_dir, style, context, game_context, settings),
        daemon=True,
    )
    worker.start()
    with jobs_lock:
        return dict(jobs[job_id])


@app.post("/api/jobs/{job_id}/retry", status_code=202)
def retry_job(job_id: str) -> dict:
    with jobs_lock:
        job = jobs.get(job_id)
        runtime = job_runtime.get(job_id)
        if job is None or runtime is None:
            raise HTTPException(404, "任务不存在或服务已重启")
        if job.get("status") != "failed":
            raise HTTPException(409, "任务正在处理中，请稍候")
        if not runtime.video_path.exists():
            raise HTTPException(404, "原视频文件不存在，无法直接重试")
        job.update(
            status="queued",
            message="正在从上次检查点继续",
            progress=8,
            stage="analysis",
            retryable=False,
            failed_stage=None,
        )
        _persist_job_locked(job_id)
        response = dict(job)

    worker = threading.Thread(
        target=process_job,
        args=(
            job_id,
            runtime.video_path,
            runtime.output_dir,
            runtime.style,
            runtime.context,
            runtime.game_context,
            runtime.settings,
            True,
        ),
        daemon=True,
    )
    worker.start()
    return response


@app.post("/api/jobs/{job_id}/revision", status_code=202)
def revise_job(job_id: str, payload: CommentaryRevisionRequest) -> dict:
    with jobs_lock:
        job = jobs.get(job_id)
        runtime = job_runtime.get(job_id)
        if job is None or runtime is None:
            raise HTTPException(404, "任务不存在或服务已重启")
        if job.get("status") != "completed" or not isinstance(job.get("result"), dict):
            raise HTTPException(409, "需要先完成一版成片，才能校正时间轴")
        if job.get("revision_status") == "processing":
            raise HTTPException(409, "修正版正在生成，请稍候")
        result_snapshot = dict(job["result"])
        try:
            duration = float(result_snapshot.get("duration") or 0)
        except (TypeError, ValueError):
            duration = 0
        if duration <= 0:
            raise HTTPException(409, "原任务缺少视频时长，无法校正")

    beats = _validated_revision_beats(payload, duration)
    try:
        base_plan = commentary_plan_from_dict(result_snapshot)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    corrected_plan = replace(
        base_plan,
        commentary="".join(beat.text for beat in beats),
        observed_actions=[beat.text for beat in beats],
        beats=beats,
    )
    revision_id = f"revision-{uuid.uuid4().hex[:10]}"
    revision_dir = runtime.output_dir / "revisions" / revision_id
    revision_dir.mkdir(parents=True, exist_ok=False)
    (revision_dir / "analysis-plan.json").write_text(
        json.dumps(corrected_plan.as_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with jobs_lock:
        current = jobs.get(job_id)
        if current is None or current.get("status") != "completed":
            raise HTTPException(409, "任务状态已经变化，请刷新后重试")
        current.update(
            status="processing",
            revision_status="processing",
            revision_error=None,
            message="正在按校正时间轴重新配音",
            progress=62,
            stage="voice",
        )
        _persist_job_locked(job_id)
        response = dict(current)

    worker = threading.Thread(
        target=process_revision,
        args=(job_id, runtime, revision_dir),
        daemon=True,
    )
    worker.start()
    return response


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(404, "任务不存在或服务已重启")
        return dict(job)


@app.get("/api/jobs/{job_id}/video")
def get_video(job_id: str, download: int = 0) -> FileResponse:
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(404, "任务不存在")
        if job["status"] != "completed":
            raise HTTPException(409, "视频仍在生成")
    output_path = DATA_DIR / job_id / "highlight.mp4"
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise HTTPException(404, "成片文件不存在")
    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename="basketball-highlight.mp4" if download else None,
        content_disposition_type="attachment" if download else "inline",
    )


@app.get("/api/jobs/{job_id}/subtitles")
def get_subtitles(job_id: str, download: int = 0) -> FileResponse:
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(404, "任务不存在")
        if job["status"] != "completed":
            raise HTTPException(409, "字幕仍在生成")
    subtitle_path = DATA_DIR / job_id / "commentary.vtt"
    if not subtitle_path.exists():
        raise HTTPException(404, "字幕文件不存在")
    return FileResponse(
        subtitle_path,
        media_type="text/vtt; charset=utf-8",
        filename="basketball-commentary.vtt" if download else None,
        content_disposition_type="attachment" if download else "inline",
    )
