from pathlib import Path
import os
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
    assert client.get("/static/timeline-utils.js").status_code == 200
    assert client.get("/favicon.svg").status_code == 200


def test_current_product_demo_assets_are_served():
    home = client.get("/")
    styles = client.get("/styles.css").text
    script = client.get("/app.js").text
    assert 'src="/product-demo.mp4?v=20260828-1"' in home.text
    assert 'poster="/product-demo-cover.jpg?v=20260828-1"' in home.text
    assert 'src="/product-demo-captions.vtt?v=20260828-1"' in home.text
    assert 'id="product-promo-backdrop"' in home.text
    assert ".promo-video-backdrop" in styles
    assert "object-fit: cover" in styles
    assert ".manga-booth.promo-is-playing .feed-toolbar" in styles
    assert ".manga-booth.promo-is-playing .hero-scoreboard" in styles
    assert ".manga-booth.promo-is-playing > figcaption" in styles
    assert "syncPromoBackdrop" in script

    video = client.get("/product-demo.mp4")
    cover = client.get("/product-demo-cover.jpg")
    captions = client.get("/product-demo-captions.vtt")

    assert video.status_code == 200
    assert video.headers["content-type"].startswith("video/mp4")
    assert len(video.content) > 100_000
    assert cover.status_code == 200
    assert cover.headers["content-type"].startswith("image/jpeg")
    assert len(cover.content) > 10_000
    assert captions.status_code == 200
    assert captions.headers["content-type"].startswith("text/vtt")
    assert captions.text.startswith("WEBVTT")


def test_review_workbench_is_click_driven_and_supports_middle_insertion():
    home = client.get("/").text
    script = client.get("/app.js").text
    styles = client.get("/styles.css").text

    promo_tag = home.split('id="product-promo-video"', 1)[1].split(">", 1)[0]
    assert " autoplay" not in promo_tag
    assert " loop" not in promo_tag
    assert 'class="result-player-pane"' in home
    assert '<span class="panel-number" aria-hidden="true">01</span>' in home
    assert '<span class="panel-number" aria-hidden="true">02</span>' in home
    assert '<span class="panel-number" aria-hidden="true">03</span>' in home
    assert 'id="result-details" class="result-details" role="region"' in home
    assert 'aria-labelledby="script-pane-title" tabindex="0"' in home
    assert 'id="script-pane-title">解说词</h2>' in home
    assert 'id="review-playhead-time"' in home
    assert 'id="review-nav-studio"' in home
    assert 'id="review-nav-video"' in home
    assert 'id="review-nav-script"' in home
    assert 'id="review-scroll-cue"' in home
    assert 'id="job-form" class="card settings-card" novalidate' in home
    assert 'id="settings-scroll-body"' in home
    assert 'id="settings-scroll-cue"' in home
    assert 'id="submit-feedback"' in home
    assert "继续下滑填写完整信息" in home
    assert 'id="mode-note"' not in home
    assert "＋ 在当前画面补一句" in home
    assert "qwen3.5-omni-flash" not in home
    assert "setPromoIdleState" in script
    assert "scrollReviewToTimeline" in script
    assert "updateReviewScrollCue" in script
    assert 'document.querySelector("#mode-note")' not in script
    assert "insertEventEditorRow" in script
    assert "createEventInsertionControl" in script
    assert "＋ 开头补一句" in script
    assert "＋ 这里补一句" in script
    assert "＋ 结尾补一句" in script
    assert "两句太近，先调时间" in script
    assert "row.append(previewButton, timeControl, kindSelect, textInput, removeButton)" in script
    assert "[...result.beats].sort" in script
    assert "timelineEditorBusy = busy" in script
    assert 'const revisionProgress = name === "progress" && Boolean(currentResult)' in script
    assert 'const visibleState = revisionProgress ? "completed" : name' in script
    assert 'workspace.classList.toggle("is-correcting", timelineEditing)' in script
    assert 'timelineEditToggle.textContent = timelineEditing ? "修改中" : "直接修改"' in script
    assert "syncSubmitAvailability" in script
    availability = script.split("function syncSubmitAvailability()", 1)[1].split("}", 1)[0]
    assert "!selectedFileValid" not in availability
    assert 'form.getAttribute("aria-busy") === "true"' in availability
    assert 'setRuntimeBadge("", "服务已连接")' in script
    assert '服务已连接 · ${system.ai_model}' not in script
    assert "showSubmitFeedback" in script
    assert "updateSettingsScrollCue" in script
    assert 'querySelectorAll(".event-editor-row input, .event-editor-row select, .event-editor-row button")' in script
    assert 'id="resume-result"' in home
    assert "compact 01 / 02 / 03 same-screen review desk" in styles
    assert "--review-side: clamp(360px, 27vw, 410px)" in styles
    assert "grid-template-columns: var(--review-side) minmax(0, 1fr)" in styles
    assert "grid-template-columns: minmax(0, 1fr) var(--review-side)" in styles
    assert ".workspace-review-mode .settings-scroll-body" in styles
    assert ".settings-scroll-cue" in styles
    assert '"play time kind copy remove" 44px' in styles
    assert "grid-area: play" in styles
    assert "grid-area: time" in styles
    assert "grid-area: kind" in styles
    assert "grid-area: copy" in styles
    assert "grid-area: remove" in styles
    assert ".workspace-review-mode.is-correcting .event-timeline" in styles
    assert ".workspace-review-mode .result-details::-webkit-scrollbar" in styles


def test_latest_completed_job_restores_when_browser_storage_is_empty(tmp_path: Path, monkeypatch):
    older = {
        "id": "older-result",
        "status": "completed",
        "result": {"title": "旧成片", "beats": [{"time": 1.0, "text": "好球"}]},
    }
    latest = {
        "id": "latest-result",
        "status": "completed",
        "result": {"title": "最新成片", "beats": [{"time": 2.0, "text": "漂亮"}]},
    }
    monkeypatch.setattr(app_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(app_module, "jobs", {"older-result": older, "latest-result": latest})
    older_state = tmp_path / "older-result" / app_module.JOB_STATE_FILENAME
    latest_state = tmp_path / "latest-result" / app_module.JOB_STATE_FILENAME
    older_state.parent.mkdir()
    latest_state.parent.mkdir()
    older_state.write_text("{}", encoding="utf-8")
    latest_state.write_text("{}", encoding="utf-8")
    os.utime(older_state, ns=(1_000_000_000, 1_000_000_000))
    os.utime(latest_state, ns=(2_000_000_000, 2_000_000_000))

    response = client.get("/api/jobs/latest")

    assert response.status_code == 200
    assert response.json()["id"] == "latest-result"


def test_frontend_falls_back_to_latest_completed_job_without_saved_id():
    script = client.get("/app.js").text

    assert 'const restoreUrl = savedJobId ? `/api/jobs/${savedJobId}` : "/api/jobs/latest";' in script
    assert "if (currentJobId) saveCurrentJob(currentJobId);" in script


def test_timeline_editor_time_stepper_seeks_preview_live():
    script = client.get("/app.js").text
    styles = client.get("/styles.css").text

    assert 'timeControl.className = "event-editor-time-control"' in script
    assert 'timeStepper.className = "event-editor-time-stepper"' in script
    assert 'increaseButton.textContent = "▲"' in script
    assert 'decreaseButton.textContent = "▼"' in script
    assert 'timeToggleLabel.textContent = "调时间"' not in script
    assert "setEventTimeControlOpen" not in script
    assert "closeOtherEventTimeControls" not in script
    assert 'aria-label", "减少 0.1 秒"' in script
    assert 'aria-label", "增加 0.1 秒"' in script
    assert "timeStepper.append(increaseButton, decreaseButton)" in script
    assert "timeControl.append(timeInput, timeStepper)" in script
    assert "adjustEventTime(-1)" in script
    assert "adjustEventTime(1)" in script
    assert "timeInput.stepDown()" in script
    assert "timeInput.stepUp()" in script

    input_handler = script.split(
        'timeInput.addEventListener("input"', 1
    )[1].split('timeInput.addEventListener("change"', 1)[0]
    assert 'seekResultVideo(timeInput.value, { autoplay: false, lead: 0 })' in input_handler
    assert ".event-editor-time-control" in styles
    assert ".event-editor-time-stepper" in styles
    assert ".event-editor-time-control.is-saved" in styles
    assert ".event-editor-time-step" in styles
    assert "grid-template-columns: minmax(0, 1fr) 24px" in styles
    assert '"play time kind copy remove" 44px /' in styles
    assert "44px 72px 60px minmax(114px, 1fr) 44px" in styles
    assert ".event-editor-time-control > .event-editor-time" in styles
    assert "grid-area: 1 / 1;" in styles
    assert ".event-editor-time-control > .event-editor-time-stepper" in styles
    assert "grid-area: 1 / 2;" in styles
    assert 'event-editor-time-control[aria-busy="true"]' in styles


def test_timeline_tick_math_rejects_duplicate_and_out_of_range_insertions():
    node_script = """
      const assert = require('node:assert/strict');
      const timeline = require('./static/timeline-utils.js');
      assert.equal(timeline.findInsertionTime({ previous: 0.1, next: 0.2, duration: 8 }), null);
      assert.equal(timeline.findInsertionTime({ previous: 0.1, next: 0.3, duration: 8 }), 0.2);
      assert.equal(timeline.findInsertionTime({ previous: 7.9, next: null, duration: 8 }), null);
      assert.equal(timeline.validateTimes([0.1, 0.2, 0.2], 8).ok, false);
      assert.equal(timeline.validateTimes([0.1, 7.95], 8).ok, false);
      assert.deepEqual(timeline.validateTimes([0.1, 0.2, 7.9], 8).normalized, [0.1, 0.2, 7.9]);
    """
    completed = subprocess.run(
        ["node", "-e", node_script],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


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
