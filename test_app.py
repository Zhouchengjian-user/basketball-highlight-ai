from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

import app as app_module


client = TestClient(app_module.app)


def test_home_and_relative_assets_are_served():
    home = client.get("/")
    assert home.status_code == 200
    assert 'href="./styles.css' in home.text
    assert 'src="./app.js' in home.text
    assert 'name="voice_engine"' in home.text
    assert "Qwen Audio Plus" in home.text
    assert "MiniMax 2.8 HD" in home.text
    assert "声音克隆" not in home.text
    assert client.get("/styles.css").status_code == 200
    assert client.get("/app.js").status_code == 200
    assert client.get("/favicon.svg").status_code == 200


def test_system_status_explains_runtime_mode(monkeypatch):
    monkeypatch.setenv("MINIMAX_ENABLED", "false")
    response = client.get("/api/system")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["ready"], bool)
    assert isinstance(data["ffmpeg_ready"], bool)
    assert isinstance(data["tts_ready"], bool)
    assert data["ai_mode"] in {"demo", "qwen"}
    assert set(data["tts_engines"]) == {"qwen_audio", "minimax"}
    assert data["tts_engines"]["minimax"]["ready"] is False
    assert "尚未开通" in data["tts_engines"]["minimax"]["reason"]
    assert data["min_video_seconds"] < data["max_video_seconds"]


def test_system_status_displays_the_configured_omni_video_model(monkeypatch):
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-key-for-omni")
    monkeypatch.setenv("QWEN_MODEL", "qwen3.7-flash")
    monkeypatch.setenv("QWEN_VIDEO_MODEL", "qwen3.5-omni-flash")
    monkeypatch.setenv("TTS_PROVIDER", "qwen_audio")
    monkeypatch.setattr(app_module, "resolve_ffmpeg", lambda *_: "ffmpeg")
    monkeypatch.setattr(
        app_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout="libx264 aac", stderr=""
        ),
    )

    response = client.get("/api/system")

    assert response.status_code == 200
    data = response.json()
    assert data["ai_enabled"] is True
    assert data["ai_model"] == "qwen3.5-omni-flash"


def test_system_status_exposes_authorized_profile_without_provider_voice_id(monkeypatch):
    provider_voice_id = "private-provider-voice-id-for-test"
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-key-for-profile-status")
    monkeypatch.setenv("QWEN_AUDIO_VOICE_AUTHORIZED_1_ID", provider_voice_id)
    monkeypatch.setattr(app_module, "resolve_ffmpeg", lambda *_: "ffmpeg")
    monkeypatch.setattr(
        app_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout="libx264 aac", stderr=""
        ),
    )

    response = client.get("/api/system")

    assert response.status_code == 200
    assert response.json()["voices"] == [
        {
            "id": "authorized_1",
            "label": "授权音色 1",
            "provider": "qwen_audio",
            "ready": True,
            "commentary_profile_label": "原创专业篮球转播叙事",
        }
    ]
    assert provider_voice_id not in response.text


def test_job_rejects_unactivated_minimax_before_upload_is_processed(monkeypatch):
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-key-for-minimax")
    monkeypatch.setenv("MINIMAX_ENABLED", "false")

    response = client.post(
        "/api/jobs",
        data={"style": "hype", "voice_engine": "minimax"},
        files={"video": ("clip.mp4", b"not-read", "video/mp4")},
    )

    assert response.status_code == 400
    assert "尚未" in response.json()["detail"]
    assert "开通" in response.json()["detail"]


def test_job_resolves_authorized_profile_into_job_specific_settings(tmp_path: Path, monkeypatch):
    provider_voice_id = "private-provider-voice-id-for-job-test"
    captured = {}

    class DeferredThread:
        def __init__(self, *, target, args, daemon):
            captured["target"] = target
            captured["args"] = args
            captured["daemon"] = daemon

        def start(self):
            captured["started"] = True

    monkeypatch.setenv("QWEN_API_KEY", "sk-test-key-for-profile-job")
    monkeypatch.setenv("QWEN_AUDIO_VOICE_AUTHORIZED_1_ID", provider_voice_id)
    monkeypatch.setattr(app_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(app_module.threading, "Thread", DeferredThread)
    monkeypatch.setattr(app_module, "jobs", {})

    response = client.post(
        "/api/jobs",
        data={
            "style": "hype",
            "voice_engine": "minimax",
            "voice_profile": "authorized_1",
        },
        files={"video": ("clip.mp4", b"video", "video/mp4")},
    )

    assert response.status_code == 202
    data = response.json()
    assert data["voice_engine"] == "qwen_audio"
    assert data["voice_profile_id"] == "authorized_1"
    assert data["voice_profile_label"] == "授权音色 1"
    assert data["commentary_profile_label"] == "原创专业篮球转播叙事"
    assert provider_voice_id not in response.text
    settings = captured["args"][-1]
    assert captured["args"][-2] == {}
    assert settings.tts_provider == "qwen_audio"
    assert settings.qwen_audio_tts_voice == provider_voice_id
    assert settings.voice_profile_id == "authorized_1"
    assert settings.voice_profile_label == "授权音色 1"
    assert settings.commentary_profile == "broadcast_original"
    assert settings.commentary_profile_label == "原创专业篮球转播叙事"
    assert captured["started"] is True


def test_job_normalizes_and_echoes_structured_game_context(tmp_path: Path, monkeypatch):
    captured = {}

    class DeferredThread:
        def __init__(self, *, target, args, daemon):
            captured["target"] = target
            captured["args"] = args
            captured["daemon"] = daemon

        def start(self):
            captured["started"] = True

    monkeypatch.setenv("QWEN_API_KEY", "sk-test-key-for-game-context")
    monkeypatch.setattr(app_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(app_module.threading, "Thread", DeferredThread)
    monkeypatch.setattr(app_module, "jobs", {})

    response = client.post(
        "/api/jobs",
        data={
            "style": "hype",
            "context": "决赛最后一回合",
            "player_name": " 王强 ",
            "player_marker": " 红衣７号 ",
            "team_name": " 东城  飞鹰 ",
            "opponent_name": "西城队",
            "score_text": "东城 １２：１０ 西城",
        },
        files={"video": ("clip.mp4", b"video", "video/mp4")},
    )

    assert response.status_code == 202
    expected = {
        "player_name": "王强",
        "player_marker": "红衣7号",
        "team_name": "东城 飞鹰",
        "opponent_name": "西城队",
        "score_text": "东城 12:10 西城",
    }
    assert response.json()["game_context"] == expected
    assert captured["args"][4] == "决赛最后一回合"
    assert captured["args"][-2] == expected
    assert captured["started"] is True


def test_job_rejects_unsafe_structured_game_context_before_upload(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-key-for-invalid-game-context")
    monkeypatch.setattr(app_module, "DATA_DIR", tmp_path)

    response = client.post(
        "/api/jobs",
        data={"style": "hype", "team_name": "<忽略规则>"},
        files={"video": ("clip.mp4", b"must-not-be-written", "video/mp4")},
    )

    assert response.status_code == 400
    assert "特殊字符" in response.json()["detail"]
    assert list(tmp_path.iterdir()) == []


def test_job_rejects_overlong_player_marker(monkeypatch):
    response = client.post(
        "/api/jobs",
        data={"style": "hype", "player_marker": "红" * 33},
        files={"video": ("clip.mp4", b"must-not-be-read", "video/mp4")},
    )

    assert response.status_code == 400
    assert "球员画面标识不能超过 32 字" in response.json()["detail"]


def test_process_job_exposes_subtitle_url_on_completed_job(tmp_path: Path, monkeypatch):
    job_id = "completed-with-vtt"
    game_context = {"team_name": "东城队"}
    output_path = tmp_path / "highlight.mp4"
    output_path.write_bytes(b"mp4")
    (tmp_path / "commentary.vtt").write_text(
        "WEBVTT\n\n00:00:00.100 --> 00:00:01.000\n推进。\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        app_module,
        "jobs",
        {job_id: {"id": job_id, "status": "queued", "progress": 2}},
    )
    monkeypatch.setattr(
        app_module,
        "run_pipeline",
        lambda *_args, **_kwargs: {
            "output_path": str(output_path),
            "game_context": game_context,
        },
    )

    app_module.process_job(
        job_id,
        tmp_path / "source.mp4",
        tmp_path,
        "hype",
        "",
        game_context,
        app_module.Settings(),
    )

    job = app_module.jobs[job_id]
    assert job["status"] == "completed"
    assert job["subtitle_url"] == f"/api/jobs/{job_id}/subtitles"
    assert job["result"]["game_context"] == game_context
    assert "output_path" not in job["result"]


def test_process_job_never_completes_without_real_output_files(tmp_path: Path, monkeypatch):
    job_id = "missing-final-output"
    output_dir = tmp_path / job_id
    output_dir.mkdir()
    monkeypatch.setattr(app_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        app_module,
        "jobs",
        {job_id: {"id": job_id, "status": "queued", "progress": 2}},
    )
    monkeypatch.setattr(app_module, "job_runtime", {})
    monkeypatch.setattr(
        app_module,
        "run_pipeline",
        lambda *_args, **_kwargs: {"output_path": str(output_dir / "highlight.mp4")},
    )

    app_module.process_job(
        job_id,
        output_dir / "source.mp4",
        output_dir,
        "hype",
        "",
        {},
        app_module.Settings(),
    )

    job = app_module.jobs[job_id]
    assert job["status"] == "failed"
    assert job["failed_stage"] == "render"
    assert job["retryable"] is True
    assert "MP4" in job["message"]


def test_completed_job_and_runtime_restore_after_service_restart(tmp_path: Path, monkeypatch):
    job_id = "persisted-completed-job"
    output_dir = tmp_path / job_id
    output_dir.mkdir()
    source = output_dir / "source.mp4"
    source.write_bytes(b"source")
    (output_dir / "highlight.mp4").write_bytes(b"rendered-video")
    secret = "must-never-be-written-to-runtime-state"
    runtime = app_module.JobRuntime(
        video_path=source,
        output_dir=output_dir,
        style="hype",
        context="决胜回合",
        game_context={"team_name": "东城队"},
        settings=app_module.Settings(
            qwen_api_key=secret,
            qwen_audio_tts_voice="private-provider-voice-id",
            tts_provider="qwen_audio",
        ),
    )
    monkeypatch.setattr(app_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        app_module,
        "jobs",
        {
            job_id: {
                "id": job_id,
                "status": "completed",
                "message": "成片已生成",
                "progress": 100,
                "result": {"title": "已恢复成片", "beats": []},
            }
        },
    )
    monkeypatch.setattr(app_module, "job_runtime", {job_id: runtime})

    app_module._persist_runtime(runtime)
    with app_module.jobs_lock:
        app_module._persist_job_locked(job_id)
    runtime_state = (output_dir / app_module.RUNTIME_STATE_FILENAME).read_text(
        encoding="utf-8"
    )
    assert secret not in runtime_state
    assert "private-provider-voice-id" not in runtime_state

    app_module.jobs.clear()
    app_module.job_runtime.clear()
    restored = app_module.load_persisted_jobs()

    assert restored == 1
    assert app_module.jobs[job_id]["status"] == "completed"
    assert app_module.jobs[job_id]["video_url"] == f"/api/jobs/{job_id}/video"
    assert app_module.job_runtime[job_id].context == "决胜回合"


def test_interrupted_persisted_job_becomes_retryable_failure(tmp_path: Path, monkeypatch):
    job_id = "persisted-interrupted-job"
    output_dir = tmp_path / job_id
    output_dir.mkdir()
    source = output_dir / "source.mp4"
    source.write_bytes(b"source")
    runtime = app_module.JobRuntime(
        video_path=source,
        output_dir=output_dir,
        style="pro",
        context="",
        game_context={},
        settings=app_module.Settings(tts_provider="qwen_audio"),
    )
    monkeypatch.setattr(app_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        app_module,
        "jobs",
        {
            job_id: {
                "id": job_id,
                "status": "processing",
                "message": "正在生成配音",
                "progress": 68,
                "stage": "voice",
                "retryable": False,
            }
        },
    )
    monkeypatch.setattr(app_module, "job_runtime", {job_id: runtime})
    app_module._persist_runtime(runtime)
    with app_module.jobs_lock:
        app_module._persist_job_locked(job_id)

    app_module.jobs.clear()
    app_module.job_runtime.clear()
    restored = app_module.load_persisted_jobs()

    assert restored == 1
    restored_job = app_module.jobs[job_id]
    assert restored_job["status"] == "failed"
    assert restored_job["retryable"] is True
    assert restored_job["failed_stage"] == "voice"
    assert "检查点" in restored_job["message"]
    on_disk = (output_dir / app_module.JOB_STATE_FILENAME).read_text(encoding="utf-8")
    assert '"status": "failed"' in on_disk


def test_failed_job_can_retry_from_saved_analysis_checkpoint(tmp_path: Path, monkeypatch):
    captured = {}
    job_id = "retryable-job"
    job_dir = tmp_path / job_id
    job_dir.mkdir()
    source = job_dir / "source.mp4"
    source.write_bytes(b"video")

    class DeferredThread:
        def __init__(self, *, target, args, daemon):
            captured["target"] = target
            captured["args"] = args
            captured["daemon"] = daemon

        def start(self):
            captured["started"] = True

    settings = app_module.Settings(qwen_api_key="test-key")
    runtime = app_module.JobRuntime(
        video_path=source,
        output_dir=job_dir,
        style="hype",
        context="",
        game_context={},
        settings=settings,
    )
    monkeypatch.setattr(app_module.threading, "Thread", DeferredThread)
    monkeypatch.setattr(
        app_module,
        "jobs",
        {
            job_id: {
                "id": job_id,
                "status": "failed",
                "message": "配音失败",
                "progress": 0,
                "retryable": True,
            }
        },
    )
    monkeypatch.setattr(app_module, "job_runtime", {job_id: runtime})

    response = client.post(f"/api/jobs/{job_id}/retry")

    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    assert response.json()["message"] == "正在从上次检查点继续"
    assert captured["target"] is app_module.process_job
    assert captured["args"][-1] is True
    assert captured["started"] is True


def test_completed_job_accepts_a_validated_timeline_revision(tmp_path: Path, monkeypatch):
    captured = {}
    job_id = "revision-job"
    job_dir = tmp_path / job_id
    job_dir.mkdir()
    source = job_dir / "source.mp4"
    source.write_bytes(b"video")

    class DeferredThread:
        def __init__(self, *, target, args, daemon):
            captured["target"] = target
            captured["args"] = args
            captured["daemon"] = daemon

        def start(self):
            captured["started"] = True

    result = {
        "title": "原始成片",
        "commentary": "持球推进。打进！",
        "observed_actions": ["持球推进", "命中"],
        "mode": "qwen_omni",
        "duration": 8.0,
        "beats": [
            {
                "time": 0.2,
                "text": "持球推进。",
                "event_id": "p1",
                "event_kind": "possession",
            },
            {
                "time": 3.0,
                "text": "打进！",
                "event_id": "m1",
                "event_kind": "made_shot",
                "anchor_time": 3.0,
                "hard_anchor": True,
            },
        ],
    }
    settings = app_module.Settings(qwen_api_key="test-key")
    runtime = app_module.JobRuntime(
        video_path=source,
        output_dir=job_dir,
        style="hype",
        context="",
        game_context={},
        settings=settings,
    )
    monkeypatch.setattr(app_module.threading, "Thread", DeferredThread)
    monkeypatch.setattr(
        app_module,
        "jobs",
        {job_id: {"id": job_id, "status": "completed", "result": result}},
    )
    monkeypatch.setattr(app_module, "job_runtime", {job_id: runtime})

    response = client.post(
        f"/api/jobs/{job_id}/revision",
        json={
            "beats": [
                {"time": 0.3, "text": "白队控制球权。", "event_kind": "possession"},
                {"time": 3.2, "text": "这球没进。", "event_kind": "missed_shot"},
            ]
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "processing"
    assert response.json()["revision_status"] == "processing"
    assert captured["target"] is app_module.process_revision
    revision_dir = captured["args"][-1]
    checkpoint = (revision_dir / "analysis-plan.json").read_text(encoding="utf-8")
    assert "这球没进" in checkpoint
    assert '"event_kind": "missed_shot"' in checkpoint
    assert '"hard_anchor": true' in checkpoint
    assert captured["started"] is True


def test_timeline_revision_rejects_unknown_event_kind(tmp_path: Path, monkeypatch):
    job_id = "invalid-revision"
    source = tmp_path / "source.mp4"
    source.write_bytes(b"video")
    result = {
        "title": "原始成片",
        "commentary": "持球推进。",
        "observed_actions": ["持球推进"],
        "mode": "qwen_omni",
        "duration": 5.0,
        "beats": [{"time": 0.2, "text": "持球推进。", "event_id": "p1"}],
    }
    runtime = app_module.JobRuntime(
        video_path=source,
        output_dir=tmp_path,
        style="hype",
        context="",
        game_context={},
        settings=app_module.Settings(qwen_api_key="test-key"),
    )
    monkeypatch.setattr(
        app_module,
        "jobs",
        {job_id: {"id": job_id, "status": "completed", "result": result}},
    )
    monkeypatch.setattr(app_module, "job_runtime", {job_id: runtime})

    response = client.post(
        f"/api/jobs/{job_id}/revision",
        json={"beats": [{"time": 1.0, "text": "犯规。", "event_kind": "foul"}]},
    )

    assert response.status_code == 400
    assert "事件类型不支持" in response.json()["detail"]


def test_completed_job_serves_webvtt_subtitles(tmp_path: Path, monkeypatch):
    job_id = "vtt-job"
    job_dir = tmp_path / job_id
    job_dir.mkdir()
    (job_dir / "commentary.vtt").write_text(
        "WEBVTT\n\n00:00:00.200 --> 00:00:01.600\n白队推进。\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(app_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        app_module,
        "jobs",
        {job_id: {"id": job_id, "status": "completed"}},
    )

    response = client.get(f"/api/jobs/{job_id}/subtitles")
    download = client.get(f"/api/jobs/{job_id}/subtitles?download=1")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/vtt")
    assert response.text.startswith("WEBVTT\n\n")
    assert "白队推进。" in response.text
    assert download.status_code == 200
    assert "attachment" in download.headers["content-disposition"]
    assert "basketball-commentary.vtt" in download.headers["content-disposition"]


def test_subtitle_endpoint_rejects_unready_and_missing_files(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(app_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        app_module,
        "jobs",
        {
            "processing": {"id": "processing", "status": "processing"},
            "missing": {"id": "missing", "status": "completed"},
        },
    )

    assert client.get("/api/jobs/unknown/subtitles").status_code == 404
    assert client.get("/api/jobs/processing/subtitles").status_code == 409
    missing = client.get("/api/jobs/missing/subtitles")
    assert missing.status_code == 404
    assert "字幕文件不存在" in missing.json()["detail"]


def test_job_rejects_unknown_profile_without_accepting_raw_voice_id(monkeypatch):
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-key-for-unknown-profile")

    response = client.post(
        "/api/jobs",
        data={"style": "hype", "voice_profile": "raw-provider-voice-id"},
        files={"video": ("clip.mp4", b"not-read", "video/mp4")},
    )

    assert response.status_code == 400
    assert "未知" in response.json()["detail"]


def test_ai_key_can_be_saved_locally_without_being_returned(tmp_path: Path, monkeypatch):
    (tmp_path / ".env.example").write_text("QWEN_API_KEY=\nQWEN_MODEL=qwen3.7-flash\n", encoding="utf-8")
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    monkeypatch.delenv("QWEN_API_KEY", raising=False)

    response = client.post("/api/settings/ai", json={"api_key": "sk-local-test-value"})

    assert response.status_code == 200
    assert "sk-local-test-value" not in response.text
    assert "sk-local-test-value" in (tmp_path / ".env").read_text(encoding="utf-8")
