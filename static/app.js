const form = document.querySelector("#job-form");
const fileInput = document.querySelector("#video");
const fileLabel = document.querySelector("#file-label");
const dropZone = document.querySelector("#drop-zone");
const fileValidation = document.querySelector("#file-validation");
const submitButton = document.querySelector("#submit-button");
const previewStatus = document.querySelector("#preview-status");
const contextInput = document.querySelector("#context");
const contextCount = document.querySelector("#context-count");
const voiceProfile = document.querySelector("#voice-profile");
const voiceProfileHelp = document.querySelector("#voice-profile-help");
const voiceEngine = document.querySelector("#voice-engine");
const previewVoiceButton = document.querySelector("#preview-voice");
const runtimeBadge = document.querySelector("#runtime-badge");
const runtimeAlert = document.querySelector("#runtime-alert");
const runtimeAlertTitle = document.querySelector("#runtime-alert-title");
const runtimeAlertMessage = document.querySelector("#runtime-alert-message");
const openAiSettings = document.querySelector("#open-ai-settings");
const aiSettingsPanel = document.querySelector("#ai-settings-panel");
const aiSettingsMessage = document.querySelector("#ai-settings-message");
const qwenApiKey = document.querySelector("#qwen-api-key");
const saveAiSettings = document.querySelector("#save-ai-settings");
const sourcePreview = document.querySelector("#source-preview");
const sourcePreviewWrap = document.querySelector("#source-preview-wrap");
const previewPlaceholder = document.querySelector("#preview-placeholder");
const emptyState = document.querySelector("#empty-state");
const emptyTitle = document.querySelector("#empty-title");
const emptyDescription = document.querySelector("#empty-description");
const previewDimensions = document.querySelector("#preview-dimensions");
const resultVideo = document.querySelector("#result-video");
const resultVideoWrap = resultVideo.closest(".video-wrap");
const progressMeta = document.querySelector("#progress-meta");
const generationStages = [...document.querySelectorAll("#generation-stages li")];
const styleDescription = document.querySelector("#style-description");
const shareButton = document.querySelector("#share-button");
const copyCommentaryButton = document.querySelector("#copy-commentary");
const eventTimeline = document.querySelector("#event-timeline");
const eventTimelineList = document.querySelector("#event-timeline-list");
const eventCount = document.querySelector("#event-count");
const retryButton = document.querySelector("#retry-button");
const resetButton = document.querySelector("#reset-button");
const timelineEditToggle = document.querySelector("#timeline-edit-toggle");
const timelineEditActions = document.querySelector("#timeline-edit-actions");
const timelineAddEvent = document.querySelector("#timeline-add-event");
const timelineCancelEdit = document.querySelector("#timeline-cancel-edit");
const timelineRenderRevision = document.querySelector("#timeline-render-revision");
const timelineEditStatus = document.querySelector("#timeline-edit-status");
const eventTimelineHelp = document.querySelector("#event-timeline-help");
const openCorrectionButton = document.querySelector("#open-correction");
let serviceReady = false;
let sourceObjectUrl = "";
let activeVoicePreview = null;
let voiceProfiles = new Map();
let selectedFileValid = false;
let generationStartedAt = 0;
let progressClock = 0;
let currentDownloadUrl = "";
let currentJobId = "";
let currentJobRetryable = false;
let currentResult = null;
let timelineEditing = false;
let savedJobRestoreStarted = false;

const MAX_UPLOAD_BYTES = 300 * 1024 * 1024;
const MIN_VIDEO_DURATION = 15;
const MAX_VIDEO_DURATION = 90;
const SAVED_JOB_KEY = "basketball-highlight-active-job-v1";

const AUTHORIZED_VOICE_ID = "authorized_1";
const AUTHORIZED_VOICE_LABEL = "授权音色 1（AI 合成 · 专业转播）";
const AUTHORIZED_VOICE_PREVIEW = "/static/voice-authorized-clone-preview.wav";
const SYSTEM_VOICE_FALLBACK = {
  id: "default_qwen",
  label: "系统默认音色（AI 合成）",
  description: "使用当前已配置的系统默认音色生成解说。",
  provider: "qwen_audio",
  preview_url: "/static/voice-qwen-audio-live.wav",
  ready: true,
  disabled_reason: "",
  synthetic: true,
};

const states = {
  empty: document.querySelector("#empty-state"),
  progress: document.querySelector("#progress-state"),
  completed: document.querySelector("#completed-state"),
  error: document.querySelector("#error-state"),
};

const STYLE_DESCRIPTIONS = {
  hype: "先跟动作、再对结果做反应；关键球会自然提速和爆发，不提前喊进。",
  pro: "以攻防选择和动作事实为主，语气沉稳，在结果确认后给出简洁判断。",
  fun: "像场边朋友一样即时接住精彩动作，表达更松弛，但不会乱猜结果。",
};

const EVENT_KIND_LABELS = {
  possession: "持球",
  pass: "传球",
  drive: "突破",
  shot: "投篮",
  made_shot: "命中",
  missed_shot: "未进",
  block: "封盖",
  steal: "抢断",
  rebound: "篮板",
  transition: "转换",
  stoppage: "停球",
  other: "回合",
};

const EVENT_KIND_DEFAULT_TEXT = {
  possession: "持球推进。",
  pass: "球传了出去。",
  drive: "持球突破。",
  shot: "完成出手。",
  made_shot: "打进！",
  missed_shot: "这球没进。",
  block: "封盖！",
  steal: "抢断！",
  rebound: "保护下篮板。",
  transition: "快速转换。",
  stoppage: "回合停了下来。",
  other: "继续看这个回合。",
};

function formatElapsed(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

function renderElapsed() {
  if (!generationStartedAt) return;
  const seconds = (Date.now() - generationStartedAt) / 1000;
  progressMeta.textContent = seconds >= 300
    ? `已用时 ${formatElapsed(seconds)} · 长片或局部复核可能更久`
    : `预计 2–5 分钟 · 已用时 ${formatElapsed(seconds)}`;
}

function startProgressClock() {
  if (progressClock) window.clearInterval(progressClock);
  generationStartedAt = Date.now();
  renderElapsed();
  progressClock = window.setInterval(renderElapsed, 1000);
}

function stopProgressClock() {
  if (progressClock) window.clearInterval(progressClock);
  progressClock = 0;
  generationStartedAt = 0;
}

function setFileValidation(message = "") {
  selectedFileValid = !message;
  fileValidation.textContent = message;
  fileValidation.classList.toggle("hidden", !message);
  dropZone.classList.toggle("file-invalid", Boolean(message));
  if (message) dropZone.classList.remove("file-ready");
  if (message) {
    previewStatus.className = "status-pill failed";
    previewStatus.innerHTML = "<i></i>片段不可用";
  } else if (fileInput.files[0]) {
    previewStatus.className = "status-pill idle";
    previewStatus.innerHTML = "<i></i>片段已校验";
  }
  submitButton.disabled = !serviceReady || Boolean(message);
}

function supportsFileSharing() {
  if (!navigator.share || !navigator.canShare || typeof File !== "function") return false;
  try {
    const sample = new File([""], "basketball-highlight.mp4", { type: "video/mp4" });
    return navigator.canShare({ files: [sample] });
  } catch (_error) {
    return false;
  }
}

function setRuntimeBadge(kind, label) {
  runtimeBadge.className = `local-badge ${kind}`;
  runtimeBadge.querySelector("b").textContent = label;
}

function showRuntimeAlert(kind, title, message) {
  runtimeAlert.className = `runtime-alert ${kind}`;
  runtimeAlertTitle.textContent = title;
  runtimeAlertMessage.textContent = message;
}

function normalizeVoiceProfile(voice, fallbackProvider = "qwen_audio") {
  const id = String(voice?.id || "").trim();
  if (!id) return null;
  const isAuthorizedVoice = id === AUTHORIZED_VOICE_ID;
  const commentaryProfileLabel = String(
    voice?.commentary_profile_label || "",
  ).trim();
  return {
    id,
    label: isAuthorizedVoice
      ? AUTHORIZED_VOICE_LABEL
      : String(voice.label || "AI 解说音色").trim(),
    description: isAuthorizedVoice
      ? `已获合法授权的录制音色，已绑定${commentaryProfileLabel || "原创专业篮球转播叙事"}。场景表达只会在对应动作被画面确认后解锁。`
      : String(voice.description || "平台提供的 AI 合成解说音色。").trim(),
    provider: String(voice.provider || fallbackProvider || "qwen_audio").trim(),
    preview_url: isAuthorizedVoice
      ? AUTHORIZED_VOICE_PREVIEW
      : String(voice.preview_url || "").trim(),
    ready: voice.ready !== false,
    disabled_reason: String(voice.disabled_reason || "该音色当前不可用。").trim(),
    commentary_profile_label: commentaryProfileLabel,
    synthetic: false,
  };
}

function systemFallbackVoice(system) {
  const engines = system.tts_engines || {};
  const configuredProvider = String(system.tts_provider || "qwen_audio");
  const configuredReady = engines[configuredProvider]?.ready !== false;
  return {
    ...SYSTEM_VOICE_FALLBACK,
    provider: configuredReady ? configuredProvider : "qwen_audio",
    ready: system.tts_ready !== false,
    disabled_reason: system.tts_ready === false ? "系统语音组件尚未准备好。" : "",
  };
}

function stopVoicePreview() {
  const audio = activeVoicePreview;
  activeVoicePreview = null;
  if (audio) {
    audio.pause();
    try {
      audio.currentTime = 0;
    } catch (_error) {
      // Some browsers reject seeking before the preview metadata is available.
    }
  }
  previewVoiceButton.textContent = "试听";
}

function updateVoiceSelection() {
  const selected = voiceProfiles.get(voiceProfile.value);
  const ready = Boolean(selected?.ready);
  const hasPreview = Boolean(selected?.preview_url);
  voiceEngine.value = selected?.provider || "qwen_audio";
  voiceProfileHelp.classList.remove("error");
  if (!selected) {
    voiceProfileHelp.textContent = "系统没有返回可用的解说音色。";
  } else if (!ready) {
    voiceProfileHelp.textContent = selected.disabled_reason;
  } else if (!hasPreview) {
    voiceProfileHelp.textContent = `${selected.description} 暂无试听，可直接生成成片。`;
  } else {
    voiceProfileHelp.textContent = selected.description;
  }
  previewVoiceButton.disabled = !ready || !hasPreview;
  previewVoiceButton.textContent = "试听";
}

function renderVoiceProfiles(system) {
  stopVoicePreview();
  const currentId = voiceProfile.value;
  const apiVoices = Array.isArray(system.voices) ? system.voices : [];
  const fallback = systemFallbackVoice(system);
  let profiles = apiVoices
    .map((voice) => normalizeVoiceProfile(voice, fallback.provider))
    .filter(Boolean);

  if (!profiles.length) profiles = [fallback];
  if (!profiles.some((voice) => voice.ready) && fallback.ready) {
    const fallbackIndex = profiles.findIndex((voice) => voice.id === fallback.id);
    if (fallbackIndex >= 0) profiles[fallbackIndex] = fallback;
    else profiles.push(fallback);
  }

  voiceProfiles = new Map(profiles.map((voice) => [voice.id, voice]));
  voiceProfile.replaceChildren();
  profiles.forEach((voice) => {
    const option = document.createElement("option");
    option.value = voice.id;
    option.textContent = voice.ready ? voice.label : `${voice.label}（暂不可用）`;
    option.dataset.label = voice.label;
    option.disabled = !voice.ready;
    option.title = voice.ready ? voice.description : voice.disabled_reason;
    voiceProfile.append(option);
  });

  const preferredIds = [
    currentId,
    system.voice_profile,
    AUTHORIZED_VOICE_ID,
    fallback.id,
  ].filter(Boolean);
  const preferred = preferredIds
    .map((id) => voiceProfiles.get(id))
    .find((voice) => voice?.ready);
  const selected = preferred || profiles.find((voice) => voice.ready) || profiles[0];
  if (selected) voiceProfile.value = selected.id;
  updateVoiceSelection();
}

async function checkRuntime() {
  if (window.location.protocol === "file:") {
    serviceReady = false;
    setRuntimeBadge("offline", "服务未启动");
    showRuntimeAlert(
      "critical",
      "这个页面不能直接双击使用",
      "请关闭当前页面，返回项目文件夹，双击“启动篮球高光.command”。启动器会自动安装依赖、开启服务并重新打开正确页面。",
    );
    submitButton.disabled = true;
    openAiSettings.classList.add("hidden");
    return;
  }

  try {
    const response = await fetch("/api/system", { cache: "no-store" });
    if (!response.ok) throw new Error(`服务返回 ${response.status}`);
    const system = await response.json();
    serviceReady = Boolean(system.ready);
    submitButton.disabled = !serviceReady || Boolean(fileValidation.textContent);
    renderVoiceProfiles(system);

    if (!system.ready) {
      setRuntimeBadge("offline", "运行环境异常");
      const missing = [!system.ffmpeg_ready && "视频处理组件", !system.tts_ready && "语音组件"].filter(Boolean).join("、");
      showRuntimeAlert("critical", "运行组件没有准备好", `缺少：${missing || "未知组件"}。请关闭启动窗口后重新双击启动器；若仍失败，请查看窗口中的错误信息。`);
      openAiSettings.classList.add("hidden");
    } else if (!system.ai_enabled) {
      setRuntimeBadge("demo", "演示模式");
      showRuntimeAlert("", "当前是演示模式", "上传、配音、字幕和视频合成功能可以正常使用，但不会分析真实篮球动作。点击右侧“配置 AI”填写 QWEN_API_KEY 后，才会启用画面解说。");
      openAiSettings.classList.remove("hidden");
    } else {
      setRuntimeBadge("", `服务已连接 · ${system.ai_model}`);
      runtimeAlert.className = "runtime-alert hidden";
      openAiSettings.classList.add("hidden");
      aiSettingsPanel.classList.add("hidden");
    }
    await restoreSavedJob();
  } catch (error) {
    serviceReady = false;
    submitButton.disabled = true;
    setRuntimeBadge("offline", "服务未连接");
    showRuntimeAlert("critical", "后台服务没有运行", "请返回项目文件夹，双击“启动篮球高光.command”，不要直接打开 HTML 文件。");
    openAiSettings.classList.add("hidden");
  }
}

function showState(name) {
  if (name !== "progress") stopProgressClock();
  Object.entries(states).forEach(([key, element]) => element.classList.toggle("hidden", key !== name));
  const emptyLabel = fileValidation.textContent
    ? ["failed", "片段不可用"]
    : selectedFileValid
      ? ["idle", "片段已校验"]
      : fileInput.files[0]
        ? ["idle", "正在读取片段"]
        : ["idle", "等待上传"];
  const labels = {
    empty: emptyLabel,
    progress: ["processing", "正在生成"],
    completed: ["done", "生成完成"],
    error: ["failed", "生成失败"],
  };
  const [className, text] = labels[name];
  previewStatus.className = `status-pill ${className}`;
  previewStatus.innerHTML = `<i></i>${text}`;
  requestAnimationFrame(() => {
    if (name === "empty") fitPreviewFrame(sourcePreview, sourcePreviewWrap, 380);
    if (name === "completed") fitPreviewFrame(resultVideo, resultVideoWrap, 640);
  });
}

function saveCurrentJob(jobId) {
  const value = String(jobId || "").trim();
  if (!value) return;
  try {
    window.localStorage.setItem(SAVED_JOB_KEY, value);
  } catch (_error) {
    // Browsers can disable storage; generation still works in the active tab.
  }
}

function clearSavedJob() {
  try {
    window.localStorage.removeItem(SAVED_JOB_KEY);
  } catch (_error) {
    // Ignore storage restrictions.
  }
}

function readSavedJob() {
  try {
    return String(window.localStorage.getItem(SAVED_JOB_KEY) || "").trim();
  } catch (_error) {
    return "";
  }
}

function fitPreviewFrame(video, frame, maxHeight) {
  const width = video.videoWidth || Number(frame.dataset.width);
  const height = video.videoHeight || Number(frame.dataset.height);
  if (!width || !height || frame.classList.contains("hidden")) return;
  const parent = frame.parentElement;
  const style = getComputedStyle(parent);
  const availableWidth = Math.max(
    180,
    parent.clientWidth - parseFloat(style.paddingLeft || 0) - parseFloat(style.paddingRight || 0),
  );
  const heightLimit = Math.min(maxHeight, Math.max(280, window.innerHeight * 0.64));
  const renderedWidth = Math.min(availableWidth, heightLimit * (width / height));
  frame.style.width = `${renderedWidth}px`;
  frame.style.aspectRatio = `${width} / ${height}`;
  frame.dataset.width = String(width);
  frame.dataset.height = String(height);
}

function setSourceMetadata(width, height) {
  const orientation = height > width ? "竖屏" : width > height ? "横屏" : "方形";
  emptyTitle.textContent = `原片预览 · ${width} × ${height}`;
  emptyDescription.textContent = `已识别为${orientation}视频，成片预览和导出都会保持这个比例与像素尺寸。`;
  previewDimensions.textContent = `原片 ${width} × ${height} · 保持原比例`;
}

function setFile(file) {
  if (!file) return;
  fileLabel.textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(1)} MB`;
  dropZone.querySelector(".choose-file").textContent = "重新选择";
  sourcePreview.onloadedmetadata = null;
  sourcePreview.onerror = null;
  if (sourceObjectUrl) URL.revokeObjectURL(sourceObjectUrl);
  sourceObjectUrl = "";
  selectedFileValid = false;
  fileValidation.textContent = "";
  fileValidation.classList.add("hidden");
  dropZone.classList.remove("file-ready", "file-invalid");
  submitButton.disabled = true;
  previewDimensions.textContent = "正在读取原片尺寸与时长";

  if (file.size > MAX_UPLOAD_BYTES) {
    sourcePreview.removeAttribute("src");
    sourcePreview.load();
    sourcePreviewWrap.classList.add("hidden");
    previewPlaceholder.classList.remove("hidden");
    emptyState.classList.remove("has-source");
    emptyTitle.textContent = "这个视频超过上传上限";
    emptyDescription.textContent = "请选择不超过 300 MB 的视频后再生成。";
    previewDimensions.textContent = "当前片段不会提交";
    showState("empty");
    setFileValidation(`文件为 ${(file.size / 1024 / 1024).toFixed(1)} MB，超过 300 MB 上限，请压缩或截短后重试。`);
    return;
  }

  sourceObjectUrl = URL.createObjectURL(file);
  sourcePreview.src = sourceObjectUrl;
  sourcePreviewWrap.classList.remove("hidden");
  previewPlaceholder.classList.add("hidden");
  emptyState.classList.add("has-source");
  showState("empty");
  sourcePreview.onloadedmetadata = () => {
    const duration = Number(sourcePreview.duration);
    if (!Number.isFinite(duration) || duration < MIN_VIDEO_DURATION || duration > MAX_VIDEO_DURATION) {
      const durationLabel = Number.isFinite(duration) ? `${duration.toFixed(1)} 秒` : "无法读取";
      setFileValidation(`视频时长为 ${durationLabel}，请选择 15–90 秒的片段。`);
      emptyTitle.textContent = "视频时长不符合要求";
      emptyDescription.textContent = "请截取为 15–90 秒后重新选择，当前文件不会提交。";
      previewDimensions.textContent = "当前片段不会提交";
      return;
    }
    setFileValidation("");
    dropZone.classList.add("file-ready");
    setSourceMetadata(sourcePreview.videoWidth, sourcePreview.videoHeight);
    fitPreviewFrame(sourcePreview, sourcePreviewWrap, 380);
  };
  sourcePreview.onerror = () => {
    setFileValidation("无法读取视频信息，请转成标准 MP4 后重新选择。");
    sourcePreviewWrap.classList.add("hidden");
    previewPlaceholder.classList.remove("hidden");
    emptyTitle.textContent = "无法预览这个视频";
    emptyDescription.textContent = "请转成标准 MP4 后重新上传，当前文件不会提交。";
    previewDimensions.textContent = "当前片段不会提交";
  };
  sourcePreview.load();
}

fileInput.addEventListener("change", () => setFile(fileInput.files[0]));
["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragging");
  });
});
["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragging");
  });
});
dropZone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (!file) return;
  const transfer = new DataTransfer();
  transfer.items.add(file);
  fileInput.files = transfer.files;
  setFile(file);
});

contextInput.addEventListener("input", () => {
  contextCount.textContent = `${contextInput.value.length} / 500`;
});

form.querySelectorAll('input[name="style"]').forEach((input) => {
  input.addEventListener("change", () => {
    if (input.checked) styleDescription.textContent = STYLE_DESCRIPTIONS[input.value] || "";
  });
});

previewVoiceButton.addEventListener("click", async () => {
  if (activeVoicePreview) {
    stopVoicePreview();
    updateVoiceSelection();
    return;
  }
  const selected = voiceProfiles.get(voiceProfile.value);
  if (!selected?.ready || !selected.preview_url) return updateVoiceSelection();
  const audio = new Audio(selected.preview_url);
  activeVoicePreview = audio;
  previewVoiceButton.disabled = false;
  previewVoiceButton.textContent = "停止";
  voiceProfileHelp.classList.remove("error");
  voiceProfileHelp.textContent = `正在试听：${selected.label}`;
  const finish = () => {
    if (activeVoicePreview !== audio) return;
    stopVoicePreview();
    updateVoiceSelection();
  };
  const fail = () => {
    if (activeVoicePreview !== audio) return;
    stopVoicePreview();
    updateVoiceSelection();
    voiceProfileHelp.classList.add("error");
    voiceProfileHelp.textContent = "试听加载失败，请稍后重试或直接生成成片。";
  };
  audio.addEventListener("ended", finish, { once: true });
  audio.addEventListener("error", fail, { once: true });
  try {
    await audio.play();
  } catch (_error) {
    fail();
  }
});

voiceProfile.addEventListener("change", () => {
  stopVoicePreview();
  updateVoiceSelection();
});

function updateProgress(job) {
  const progress = Math.max(0, Math.min(100, Number(job.progress) || 0));
  const message = String(job.message || "正在准备视频");
  document.querySelector("#progress-message").textContent = message;
  document.querySelector("#progress-percent").textContent = `${Math.round(progress)}%`;
  document.querySelector("#progress-bar").style.width = `${progress}%`;
  const explicitStage = { upload: 0, analysis: 1, voice: 2, render: 3 }[job.stage];
  let activeStage = Number.isInteger(explicitStage)
    ? explicitStage
    : progress < 15 ? 0 : progress < 56 ? 1 : progress < 79 ? 2 : 3;
  if (!Number.isInteger(explicitStage)) {
    if (/上传|读取/.test(message)) activeStage = 0;
    else if (/分析|理解|关键画面|回合/.test(message)) activeStage = 1;
    else if (/配音|语音|对齐/.test(message)) activeStage = 2;
    else if (/混音|字幕|合成|导出|成片/.test(message)) activeStage = 3;
  }
  generationStages.forEach((stage, index) => {
    const done = progress >= 100 || index < activeStage;
    stage.classList.toggle("done", done);
    stage.classList.toggle("active", !done && index === activeStage);
    if (!done && index === activeStage) stage.setAttribute("aria-current", "step");
    else stage.removeAttribute("aria-current");
  });
}

function formatEventTime(value) {
  const seconds = Math.max(0, Number(value) || 0);
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds - minutes * 60;
  return `${String(minutes).padStart(2, "0")}:${remainder.toFixed(1).padStart(4, "0")}`;
}

function jumpToEvent(time) {
  try {
    resultVideo.currentTime = Math.max(0, Number(time) - 0.35);
  } catch (_error) {
    return;
  }
  resultVideo.play().catch(() => {});
}

function createEventEditorRow(beat = {}) {
  const row = document.createElement("div");
  row.className = "event-editor-row";

  const timeInput = document.createElement("input");
  timeInput.className = "event-editor-time";
  timeInput.type = "number";
  timeInput.min = "0.1";
  timeInput.max = String(Math.max(0.2, Number(currentResult?.duration) - 0.1));
  timeInput.step = "0.1";
  timeInput.value = Math.max(0.1, Number(beat.time) || 0.1).toFixed(1);
  timeInput.setAttribute("aria-label", "解说出现时间（秒）");
  timeInput.addEventListener("change", () => jumpToEvent(timeInput.value));

  const kindSelect = document.createElement("select");
  kindSelect.className = "event-editor-kind";
  kindSelect.setAttribute("aria-label", "篮球事件类型");
  Object.entries(EVENT_KIND_LABELS).forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    kindSelect.append(option);
  });
  kindSelect.value = EVENT_KIND_LABELS[beat.event_kind] ? beat.event_kind : "other";

  const textInput = document.createElement("input");
  textInput.className = "event-editor-text";
  textInput.type = "text";
  textInput.maxLength = 80;
  textInput.value = String(beat.text || EVENT_KIND_DEFAULT_TEXT[kindSelect.value]);
  textInput.setAttribute("aria-label", "这句解说词");

  kindSelect.addEventListener("change", () => {
    textInput.value = EVENT_KIND_DEFAULT_TEXT[kindSelect.value] || "继续看这个回合。";
  });

  const removeButton = document.createElement("button");
  removeButton.className = "event-editor-remove";
  removeButton.type = "button";
  removeButton.textContent = "×";
  removeButton.title = "删除这句解说";
  removeButton.setAttribute("aria-label", "删除这句解说");
  removeButton.addEventListener("click", () => {
    row.remove();
    eventCount.textContent = `${eventTimelineList.children.length} 个事件`;
  });

  row.append(timeInput, kindSelect, textInput, removeButton);
  return row;
}

function renderEventTimeline(result) {
  const beats = Array.isArray(result?.beats) ? result.beats : [];
  eventTimelineList.replaceChildren();
  eventTimeline.classList.toggle("hidden", !beats.length);
  if (!beats.length) return;
  eventCount.textContent = `${beats.length} 个事件`;
  timelineEditToggle.textContent = timelineEditing ? "矫正中" : "开始矫正";
  timelineEditActions.classList.toggle("hidden", !timelineEditing);
  eventTimelineHelp.textContent = timelineEditing
    ? "直接修改每句解说词、出现时间或事件类型。生成修正版时会复用现有视频分析，不必重新理解整段视频。"
    : "点击任意一句，视频会跳到对应动作。标记为“请复核”的句子建议重点检查。";
  if (!timelineEditing) {
    timelineEditStatus.classList.add("hidden");
    timelineEditStatus.classList.remove("error");
  }

  beats.forEach((beat, index) => {
    if (timelineEditing) {
      eventTimelineList.append(createEventEditorRow(beat));
      return;
    }
    const time = Math.max(0, Number(beat.time) || 0);
    const confidence = Number(beat.confidence);
    const needsReview = Number.isFinite(confidence) && confidence < 0.82;
    const row = document.createElement("button");
    row.className = "event-row";
    row.type = "button";
    row.dataset.time = String(time);
    row.setAttribute(
      "aria-label",
      `跳到 ${formatEventTime(time)}，${String(beat.text || `第 ${index + 1} 句解说`)}`,
    );

    const timeLabel = document.createElement("span");
    timeLabel.className = "event-time";
    timeLabel.textContent = formatEventTime(time);

    const copy = document.createElement("span");
    copy.className = "event-copy";
    const text = document.createElement("strong");
    text.textContent = String(beat.text || "回合解说");
    const kind = document.createElement("small");
    kind.textContent = EVENT_KIND_LABELS[beat.event_kind] || `事件 ${index + 1}`;
    copy.append(text, kind);

    const badge = document.createElement("span");
    badge.className = `event-review${needsReview ? "" : " event-locked"}`;
    badge.textContent = needsReview ? "请复核" : beat.hard_anchor ? "结果已锁定" : "已对齐";

    row.append(timeLabel, copy, badge);
    row.addEventListener("click", () => jumpToEvent(time));
    eventTimelineList.append(row);
  });
}

function setTimelineStatus(message = "", isError = false) {
  timelineEditStatus.textContent = message;
  timelineEditStatus.classList.toggle("hidden", !message);
  timelineEditStatus.classList.toggle("error", Boolean(message) && isError);
}

function collectTimelineRevision() {
  const rows = [...eventTimelineList.querySelectorAll(".event-editor-row")];
  if (!rows.length) throw new Error("至少保留一句与画面对应的解说。");
  if (rows.length > 32) throw new Error("一段视频最多保留 32 句解说。");
  const duration = Number(currentResult?.duration) || Number(resultVideo.duration) || 0;
  return rows.map((row, index) => {
    const time = Number(row.querySelector(".event-editor-time")?.value);
    const eventKind = String(row.querySelector(".event-editor-kind")?.value || "");
    const commentary = String(row.querySelector(".event-editor-text")?.value || "").trim();
    if (!Number.isFinite(time) || time < 0.08 || (duration > 0 && time >= duration)) {
      throw new Error(`第 ${index + 1} 个事件时间需要在视频时长内。`);
    }
    if (!EVENT_KIND_LABELS[eventKind]) {
      throw new Error(`第 ${index + 1} 个事件类型不正确。`);
    }
    if (!commentary || commentary.length > 80) {
      throw new Error(`第 ${index + 1} 句解说需要 1–80 个字。`);
    }
    return { time: Math.round(time * 10) / 10, event_kind: eventKind, text: commentary };
  });
}

function setTimelineEditorBusy(busy) {
  timelineEditToggle.disabled = busy;
  timelineAddEvent.disabled = busy;
  timelineCancelEdit.disabled = busy;
  timelineRenderRevision.disabled = busy;
  timelineRenderRevision.textContent = busy ? "正在生成修正版…" : "重新配音并生成修正版";
}

function showResult(job) {
  const result = job.result;
  currentResult = result;
  timelineEditing = false;
  currentJobId = String(job.id || currentJobId || "");
  saveCurrentJob(currentJobId);
  currentJobRetryable = false;
  const hasEditableBeats = Array.isArray(result.beats) && result.beats.length > 0;
  openCorrectionButton.disabled = !hasEditableBeats;
  openCorrectionButton.textContent = hasEditableBeats ? "去矫正解说词" : "暂无可矫正解说";
  document.querySelector("#result-title").textContent = result.title;
  document.querySelector("#result-commentary").textContent = result.beats?.length
    ? result.beats.map((beat) => beat.text).join(" ")
    : result.commentary;
  renderEventTimeline(result);
  resultVideoWrap.dataset.width = String(result.width || "");
  resultVideoWrap.dataset.height = String(result.height || "");
  resultVideo.src = `${job.video_url}?v=${Date.now()}`;
  resultVideo.querySelectorAll("track[data-generated-caption]").forEach((track) => track.remove());
  const subtitleUrl = String(job.subtitle_url || "").trim();
  const hasPlayerSubtitles = result.subtitle_mode !== "burned" && Boolean(subtitleUrl);
  if (hasPlayerSubtitles) {
    const track = document.createElement("track");
    track.kind = "captions";
    track.label = "中文字幕";
    track.srclang = "zh";
    track.src = subtitleUrl;
    track.default = true;
    track.dataset.generatedCaption = "true";
    resultVideo.append(track);
  }
  document.querySelector("#download-link").href = job.download_url;
  currentDownloadUrl = job.download_url;
  shareButton.querySelector("span").textContent = supportsFileSharing() ? "分享成片" : "另存成片";
  shareButton.disabled = false;
  const note = document.querySelector("#mode-note");
  const eventGrounded = result.alignment_mode === "event_grounded";
  const coverageNote = eventGrounded
    ? ` · 非比赛画面和无可靠事件处保留现场声，不强行填词`
    : Number.isFinite(result.max_silence_gap)
      ? ` · 最长自然停连 ${result.max_silence_gap.toFixed(2)} 秒`
      : "";
  const syncNote = result.audio_sync_mode === "per_beat"
    ? eventGrounded
      ? ` · ${result.grounded_event_count || 0} 个视频事件已锁定，${result.hard_anchor_count || 0} 个结果使用不可提前锚点`
      : ` · ${result.aligned_beat_count || result.beats?.length || 1}/${result.beats?.length || 1} 句按动作时间轴合成`
    : "";
  const deliveryNote = eventGrounded
    ? " · 逐事件独立对齐配音"
    : Number.isFinite(result.delivery_group_count)
      ? ` · 合并为 ${result.delivery_group_count} 组连续语气配音`
      : "";
  const selectedVoiceLabel = voiceProfile.selectedOptions[0]?.dataset.label;
  const backendVoiceLabel = String(
    result.voice_profile_label || job.voice_profile_label || "",
  ).trim();
  const resultVoiceLabel = backendVoiceLabel === "授权音色 1"
    ? AUTHORIZED_VOICE_LABEL
    : backendVoiceLabel || selectedVoiceLabel || "系统默认音色（AI 合成）";
  const analysisLabel = String(result.mode || "").startsWith("qwen_omni")
    ? result.analysis_audio_used
      ? result.mode === "qwen_omni_partial"
        ? "Qwen3.5-Omni 分段音画分析（个别区间已安全跳过）"
        : "Qwen3.5-Omni 音画联合分析"
      : "Qwen3.5-Omni 画面分析（原片无可用音轨）"
    : result.mode === "qwen_frames"
      ? "关键画面分析（Omni 已自动降级）"
      : "Qwen 关键画面分析";
  const skillNote = result.commentary_skill
    ? ` · ${result.commentary_skill}`
    : "";
  const commentaryProfileNote = result.commentary_profile_label
    ? ` · ${result.commentary_profile_label}`
    : "";
  const subtitleNote = result.subtitle_mode === "burned"
    ? "字幕已烧录"
    : result.subtitle_mode === "soft" || hasPlayerSubtitles
      ? "播放器字幕"
      : "字幕状态未返回";
  const revisionNote = Number(result.revision_count) > 0
    ? ` · 已应用第 ${result.revision_count} 次人工时间轴校正`
    : "";
  note.textContent = result.mode === "demo"
    ? "当前未配置 QWEN_API_KEY，成片使用安全的演示口播。配置密钥后会根据视频画面生成真实解说。"
    : `${analysisLabel}${skillNote}${commentaryProfileNote} · ${result.beats?.length || 1} 段逐球解说${syncNote}${deliveryNote}${coverageNote}${revisionNote} · 解说音色：${resultVoiceLabel} · ${subtitleNote}`;
  if (result.width && result.height) {
    previewDimensions.textContent = `原片与成片均为 ${result.width} × ${result.height} · 未裁切`;
  }
  showState("completed");
  resultVideo.onloadedmetadata = () => fitPreviewFrame(resultVideo, resultVideoWrap, 640);
  resultVideo.load();
  requestAnimationFrame(() => fitPreviewFrame(resultVideo, resultVideoWrap, 640));
}

function enterTimelineCorrection(shouldScroll = false) {
  if (!currentResult || timelineEditing || !Array.isArray(currentResult.beats) || !currentResult.beats.length) return;
  timelineEditing = true;
  setTimelineStatus("");
  renderEventTimeline(currentResult);
  if (shouldScroll) {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    eventTimeline.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
  }
  window.requestAnimationFrame(() => eventTimelineList.querySelector(".event-editor-text")?.focus());
}

timelineEditToggle.addEventListener("click", () => {
  enterTimelineCorrection(false);
});

openCorrectionButton.addEventListener("click", () => {
  enterTimelineCorrection(true);
});

timelineCancelEdit.addEventListener("click", () => {
  if (!currentResult) return;
  timelineEditing = false;
  setTimelineStatus("");
  renderEventTimeline(currentResult);
});

timelineAddEvent.addEventListener("click", () => {
  const count = eventTimelineList.querySelectorAll(".event-editor-row").length;
  if (count >= 32) {
    setTimelineStatus("一段视频最多保留 32 句解说。", true);
    return;
  }
  const duration = Number(currentResult?.duration) || Number(resultVideo.duration) || 1;
  const currentTime = Number(resultVideo.currentTime);
  const time = Math.min(
    Math.max(0.1, Number.isFinite(currentTime) && currentTime > 0 ? currentTime : duration / 2),
    Math.max(0.1, duration - 0.1),
  );
  const row = createEventEditorRow({
    time,
    event_kind: "other",
    text: EVENT_KIND_DEFAULT_TEXT.other,
  });
  eventTimelineList.append(row);
  eventCount.textContent = `${eventTimelineList.children.length} 个事件`;
  setTimelineStatus("已添加一句，请调整时间、事件类型和解说词。", false);
  row.querySelector(".event-editor-text")?.focus();
});

async function pollRevision(jobId) {
  for (;;) {
    const response = await fetch(`/api/jobs/${jobId}`, { cache: "no-store" });
    if (!response.ok) throw new Error("无法读取修正版进度");
    const job = await response.json();
    updateProgress(job);
    if (job.revision_status === "failed") {
      showResult(job);
      setTimelineStatus(job.revision_error || "修正版生成失败，原成片仍然保留。", true);
      return false;
    }
    if (job.status === "completed" && job.revision_status === "completed") {
      showResult(job);
      setTimelineStatus("已按校正后的时间轴重新配音并导出。", false);
      return true;
    }
    if (job.status === "failed") throw new Error(job.message || "修正版生成失败");
    await new Promise((resolve) => setTimeout(resolve, 900));
  }
}

timelineRenderRevision.addEventListener("click", async () => {
  if (!currentJobId || !currentResult || !timelineEditing) return;
  let beats;
  try {
    beats = collectTimelineRevision();
  } catch (error) {
    setTimelineStatus(error.message || "请检查事件时间轴。", true);
    return;
  }

  setTimelineEditorBusy(true);
  setTimelineStatus("正在保存校正结果…", false);
  try {
    const response = await fetch(`/api/jobs/${currentJobId}/revision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ beats }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "无法提交校正结果");
    startProgressClock();
    showState("progress");
    updateProgress(body);
    await pollRevision(currentJobId);
  } catch (error) {
    showState("completed");
    setTimelineStatus(`${error.message || "修正版生成失败"}，原成片没有被覆盖。`, true);
  } finally {
    setTimelineEditorBusy(false);
  }
});

shareButton.addEventListener("click", async () => {
  const downloadLink = document.querySelector("#download-link");
  if (!currentDownloadUrl || !supportsFileSharing()) {
    downloadLink.click();
    return;
  }
  const label = shareButton.querySelector("span");
  const originalLabel = label.textContent;
  shareButton.disabled = true;
  label.textContent = "正在准备…";
  try {
    const response = await fetch(currentDownloadUrl, { cache: "no-store" });
    if (!response.ok) throw new Error("无法读取成片");
    const blob = await response.blob();
    const file = new File([blob], "篮球高光解说.mp4", { type: blob.type || "video/mp4" });
    if (!navigator.canShare({ files: [file] })) throw new Error("浏览器不支持文件分享");
    await navigator.share({
      files: [file],
      title: "篮球高光解说成片",
      text: "我的篮球高光 AI 解说成片",
    });
  } catch (error) {
    if (error?.name !== "AbortError") downloadLink.click();
  } finally {
    shareButton.disabled = false;
    label.textContent = originalLabel;
  }
});

copyCommentaryButton.addEventListener("click", async () => {
  const text = document.querySelector("#result-commentary").textContent.trim();
  if (!text) return;
  const label = copyCommentaryButton.querySelector("span");
  let copied = false;
  try {
    if (!navigator.clipboard?.writeText) throw new Error("Clipboard API unavailable");
    await navigator.clipboard.writeText(text);
    copied = true;
  } catch (_error) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.append(textarea);
    textarea.select();
    try {
      copied = document.execCommand("copy");
    } catch (_fallbackError) {
      copied = false;
    } finally {
      textarea.remove();
    }
  }
  label.textContent = copied ? "已复制" : "复制失败";
  window.setTimeout(() => { label.textContent = "复制解说词"; }, 1600);
});

async function restoreSavedJob() {
  if (savedJobRestoreStarted) return;
  savedJobRestoreStarted = true;
  const savedJobId = readSavedJob();
  if (!savedJobId) return;
  try {
    const response = await fetch(`/api/jobs/${savedJobId}`, { cache: "no-store" });
    if (response.status === 404) {
      clearSavedJob();
      return;
    }
    if (!response.ok) throw new Error("无法恢复上次任务");
    const job = await response.json();
    currentJobId = String(job.id || savedJobId);
    currentJobRetryable = Boolean(job.retryable);
    if (job.status === "completed") {
      showResult(job);
      if (job.revision_status === "failed") {
        setTimelineStatus(job.revision_error || "修正版生成失败，原成片仍然保留。", true);
      }
      return;
    }
    if (job.status === "failed") {
      document.querySelector("#error-message").textContent = job.message || "上次任务没有生成成功";
      retryButton.classList.toggle("hidden", !currentJobRetryable);
      showState("error");
      return;
    }
    startProgressClock();
    showState("progress");
    updateProgress(job);
    await pollJob(currentJobId);
  } catch (error) {
    document.querySelector("#error-message").textContent = error.message || "无法恢复上次任务";
    retryButton.classList.toggle("hidden", !currentJobRetryable);
    showState("error");
  }
}

async function pollJob(jobId) {
  saveCurrentJob(jobId);
  for (;;) {
    const response = await fetch(`/api/jobs/${jobId}`);
    if (!response.ok) throw new Error("无法读取生成进度");
    const job = await response.json();
    updateProgress(job);
    if (job.status === "completed") return showResult(job);
    if (job.status === "failed") {
      currentJobId = String(job.id || jobId);
      currentJobRetryable = Boolean(job.retryable);
      const error = new Error(job.message);
      error.retryable = currentJobRetryable;
      throw error;
    }
    await new Promise((resolve) => setTimeout(resolve, 900));
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!serviceReady) {
    document.querySelector("#error-message").textContent = "后台服务没有准备好。请使用“启动篮球高光.command”打开本项目。";
    showState("error");
    return;
  }
  if (!fileInput.files[0]) return fileInput.click();
  if (!selectedFileValid) {
    setFileValidation(fileValidation.textContent || "正在读取视频时长，请稍后再试。");
    return;
  }
  startProgressClock();
  showState("progress");
  clearSavedJob();
  currentJobId = "";
  currentJobRetryable = false;
  submitButton.disabled = true;
  submitButton.querySelector(".button-label").textContent = "正在生成，请稍候…";
  updateProgress({ message: "正在上传视频", progress: 1 });
  try {
    const formData = new FormData(form);
    ["player_name", "player_marker", "team_name", "opponent_name", "score_text", "context"].forEach((name) => {
      const value = String(formData.get(name) || "").trim();
      if (value) formData.set(name, value);
      else formData.delete(name);
    });
    if (voiceProfiles.get(voiceProfile.value)?.synthetic) formData.delete("voice_profile");
    fileInput.disabled = true;
    dropZone.classList.add("is-busy");
    form.setAttribute("aria-busy", "true");
    const response = await fetch("/api/jobs", { method: "POST", body: formData });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "上传失败");
    currentJobId = String(body.id || "");
    saveCurrentJob(currentJobId);
    await pollJob(body.id);
  } catch (error) {
    document.querySelector("#error-message").textContent = error.message || "未知错误";
    retryButton.classList.toggle("hidden", !currentJobId || !currentJobRetryable);
    showState("error");
  } finally {
    fileInput.disabled = false;
    dropZone.classList.remove("is-busy");
    form.removeAttribute("aria-busy");
    submitButton.disabled = !serviceReady || !selectedFileValid;
    submitButton.querySelector(".button-label").textContent = "一键生成解说成片";
  }
});

retryButton.addEventListener("click", async () => {
  if (!currentJobId || !currentJobRetryable) return;
  retryButton.disabled = true;
  resetButton.disabled = true;
  startProgressClock();
  showState("progress");
  updateProgress({ message: "正在从上次检查点继续", progress: 8 });
  try {
    const response = await fetch(`/api/jobs/${currentJobId}/retry`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "无法继续任务");
    currentJobRetryable = false;
    await pollJob(currentJobId);
  } catch (error) {
    document.querySelector("#error-message").textContent = error.message || "重试失败";
    retryButton.classList.toggle("hidden", !currentJobRetryable);
    showState("error");
  } finally {
    retryButton.disabled = false;
    resetButton.disabled = false;
  }
});

resetButton.addEventListener("click", () => {
  currentJobId = "";
  currentJobRetryable = false;
  currentResult = null;
  timelineEditing = false;
  clearSavedJob();
  retryButton.classList.add("hidden");
  showState("empty");
});

openAiSettings.addEventListener("click", () => {
  aiSettingsPanel.classList.toggle("hidden");
  aiSettingsMessage.textContent = "";
  if (!aiSettingsPanel.classList.contains("hidden")) qwenApiKey.focus();
});

aiSettingsPanel.addEventListener("submit", async (event) => {
  event.preventDefault();
  aiSettingsMessage.className = "settings-message";
  aiSettingsMessage.textContent = "正在保存…";
  saveAiSettings.disabled = true;
  try {
    const response = await fetch("/api/settings/ai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: qwenApiKey.value }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "保存失败");
    qwenApiKey.value = "";
    aiSettingsMessage.className = "settings-message success";
    aiSettingsMessage.textContent = "密钥已保存在本机，后续生成将启用 AI 画面理解。";
    await checkRuntime();
  } catch (error) {
    aiSettingsMessage.textContent = error.message || "保存失败";
  } finally {
    saveAiSettings.disabled = false;
  }
});

voiceProfiles = new Map([
  [AUTHORIZED_VOICE_ID, normalizeVoiceProfile({
    id: AUTHORIZED_VOICE_ID,
    label: AUTHORIZED_VOICE_LABEL,
    description: "已获合法授权的录制音色，由 AI 合成用于本项目解说。",
    provider: "qwen_audio",
    preview_url: AUTHORIZED_VOICE_PREVIEW,
    ready: true,
  })],
  [SYSTEM_VOICE_FALLBACK.id, SYSTEM_VOICE_FALLBACK],
]);
updateVoiceSelection();
checkRuntime();

window.addEventListener("resize", () => {
  fitPreviewFrame(sourcePreview, sourcePreviewWrap, 380);
  fitPreviewFrame(resultVideo, resultVideoWrap, 640);
});
