const form = document.querySelector("#job-form");
const fileInput = document.querySelector("#video");
const fileLabel = document.querySelector("#file-label");
const dropZone = document.querySelector("#drop-zone");
const fileValidation = document.querySelector("#file-validation");
const submitButton = document.querySelector("#submit-button");
const submitFeedback = document.querySelector("#submit-feedback");
const settingsScrollBody = document.querySelector("#settings-scroll-body");
const settingsScrollCue = document.querySelector("#settings-scroll-cue");
const previewStatus = document.querySelector("#preview-status");
const progressTrack = document.querySelector(".progress-track");
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
const resultDetails = document.querySelector("#result-details");
const workspace = document.querySelector("#studio");
const reviewPlayheadTime = document.querySelector("#review-playhead-time");
const reviewNavStudio = document.querySelector("#review-nav-studio");
const reviewNavVideo = document.querySelector("#review-nav-video");
const reviewNavScript = document.querySelector("#review-nav-script");
const reviewScrollCue = document.querySelector("#review-scroll-cue");
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
const returnToSetupButton = document.querySelector("#return-to-setup");
const resumeResultButton = document.querySelector("#resume-result");
const promoVideo = document.querySelector("#product-promo-video");
const promoBackdrop = document.querySelector("#product-promo-backdrop");
const promoPlayToggle = document.querySelector("#promo-play-toggle");
const reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
const finePointerQuery = window.matchMedia("(hover: hover) and (pointer: fine)");
const timelineMath = window.CourtCastTimeline;
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
let timelineEditorBusy = false;
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
  syncSubmitAvailability();
}

function syncSubmitAvailability() {
  submitButton.disabled = !serviceReady
    || timelineEditorBusy
    || form.getAttribute("aria-busy") === "true";
}

function updateSettingsScrollCue() {
  const reviewVisible = workspace.classList.contains("workspace-review-mode") && window.innerWidth >= 901;
  const remaining = settingsScrollBody.scrollHeight
    - settingsScrollBody.scrollTop
    - settingsScrollBody.clientHeight;
  const shouldShow = reviewVisible
    && settingsScrollBody.scrollHeight > settingsScrollBody.clientHeight + 8
    && remaining > 24;
  settingsScrollCue.classList.toggle("hidden", !shouldShow);
  settingsScrollCue.disabled = !shouldShow;
  settingsScrollCue.setAttribute("aria-hidden", shouldShow ? "false" : "true");
}

function scrollSettingsForward() {
  const behavior = reducedMotionQuery.matches ? "auto" : "smooth";
  settingsScrollBody.scrollBy({
    top: Math.max(220, settingsScrollBody.clientHeight * 0.68),
    behavior,
  });
  window.requestAnimationFrame(updateSettingsScrollCue);
}

function showSubmitFeedback(message = "", isError = false) {
  submitFeedback.textContent = message;
  submitFeedback.classList.toggle("error", Boolean(message) && isError);
  if (!message) return;
  const behavior = reducedMotionQuery.matches ? "auto" : "smooth";
  if (settingsScrollBody.scrollHeight > settingsScrollBody.clientHeight + 8) {
    settingsScrollBody.scrollTo({ top: settingsScrollBody.scrollHeight, behavior });
  } else {
    submitFeedback.scrollIntoView({ behavior, block: "nearest" });
  }
  window.requestAnimationFrame(updateSettingsScrollCue);
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
    syncSubmitAvailability();
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
      setRuntimeBadge("", "服务已连接");
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
  const revisionProgress = name === "progress" && Boolean(currentResult);
  const visibleState = revisionProgress ? "completed" : name;
  Object.entries(states).forEach(([key, element]) => element.classList.toggle("hidden", key !== visibleState));
  const keepReviewLayout = visibleState === "completed";
  workspace.classList.toggle("workspace-review-mode", keepReviewLayout);
  workspace.classList.toggle("workspace-revision-progress", revisionProgress);
  workspace.dataset.state = revisionProgress ? "revision-progress" : name;
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
    if (visibleState === "empty") fitPreviewFrame(sourcePreview, sourcePreviewWrap, 380);
    if (visibleState === "completed") fitPreviewFrame(resultVideo, resultVideoWrap, 640);
    updateReviewViewportNavigation();
    updateSettingsScrollCue();
  });
}

function setReviewNavActive(target) {
  [
    [reviewNavVideo, target === "video"],
    [reviewNavScript, target === "script"],
  ].forEach(([button, active]) => {
    button.classList.toggle("is-active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
}

function scrollReviewToVideo() {
  const behavior = reducedMotionQuery.matches ? "auto" : "smooth";
  if (window.innerWidth > 900) {
    resultDetails.scrollTo({ top: 0, behavior });
  } else {
    resultVideo.closest(".result-player-pane")?.scrollIntoView({ behavior, block: "start" });
  }
  setReviewNavActive("video");
}

function scrollReviewToTimeline({ focus = false } = {}) {
  if (eventTimeline.classList.contains("hidden")) return;
  const behavior = reducedMotionQuery.matches ? "auto" : "smooth";
  if (window.innerWidth > 900) {
    const detailsRect = resultDetails.getBoundingClientRect();
    const timelineRect = eventTimeline.getBoundingClientRect();
    const top = resultDetails.scrollTop + timelineRect.top - detailsRect.top - 78;
    resultDetails.scrollTo({ top: Math.max(0, top), behavior });
  } else {
    eventTimeline.scrollIntoView({ behavior, block: "start" });
  }
  setReviewNavActive("script");
  if (focus) {
    window.requestAnimationFrame(() => timelineEditToggle.focus({ preventScroll: true }));
  }
}

function updateReviewScrollCue() {
  const resultVisible = !states.completed.classList.contains("hidden");
  const timelineVisible = !eventTimeline.classList.contains("hidden");
  let shouldShow = false;
  if (resultVisible && timelineVisible && !timelineEditing) {
    if (window.innerWidth > 900) {
      const remainingScroll = resultDetails.scrollHeight - resultDetails.scrollTop - resultDetails.clientHeight;
      shouldShow = remainingScroll > 96;
    } else {
      const remainingScroll = document.documentElement.scrollHeight - window.scrollY - window.innerHeight;
      shouldShow = remainingScroll > 120;
    }
  }
  reviewScrollCue.classList.toggle("hidden", !shouldShow);
}

function updateReviewViewportNavigation() {
  updateReviewScrollCue();
  if (states.completed.classList.contains("hidden") || eventTimeline.classList.contains("hidden") || timelineEditing) return;
  const timelineRect = eventTimeline.getBoundingClientRect();
  const threshold = window.innerWidth > 900
    ? resultDetails.getBoundingClientRect().top + 104
    : window.innerHeight * 0.56;
  setReviewNavActive(timelineRect.top <= threshold ? "script" : "video");
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
  const reviewPaneLimit = frame === resultVideoWrap && window.innerWidth <= 900
    ? Math.max(180, window.innerHeight * 0.31)
    : maxHeight;
  const heightLimit = Math.min(reviewPaneLimit, Math.max(180, window.innerHeight * 0.64));
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
  showSubmitFeedback("");
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
  const roundedProgress = Math.round(progress);
  document.querySelector("#progress-message").textContent = message;
  document.querySelector("#progress-percent").textContent = `${roundedProgress}%`;
  document.querySelector("#progress-bar").style.width = `${progress}%`;
  progressTrack?.setAttribute("aria-valuenow", String(roundedProgress));
  progressTrack?.setAttribute("aria-valuetext", `${message}，${roundedProgress}%`);
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

function seekResultVideo(time, { autoplay = true, lead = 0.35 } = {}) {
  const target = Math.max(0, Number(time) - Math.max(0, Number(lead) || 0));
  try {
    if (!autoplay) resultVideo.pause();
    resultVideo.currentTime = target;
  } catch (_error) {
    return;
  }
  updateReviewPlayhead();
  if (autoplay) resultVideo.play().catch(() => {});
}

function jumpToEvent(time) {
  seekResultVideo(time, { autoplay: true, lead: 0.35 });
}

function syncEventTimeControlState(timeControl) {
  const timeInput = timeControl?.querySelector(".event-editor-time");
  const decreaseButton = timeControl?.querySelector(".event-editor-time-decrease");
  const increaseButton = timeControl?.querySelector(".event-editor-time-increase");
  if (!timeInput || !decreaseButton || !increaseButton) return;

  const value = Number(timeInput.value);
  const minimum = Number(timeInput.min);
  const maximum = Number(timeInput.max);
  const hasValue = timeInput.value.trim() !== "" && Number.isFinite(value);
  const disabled = timelineEditorBusy || timeInput.disabled;
  timeInput.setAttribute("aria-label", hasValue
    ? `解说出现时间 ${value.toFixed(1)} 秒`
    : "解说出现时间（秒）");
  decreaseButton.disabled = disabled || !hasValue || value <= minimum + Number.EPSILON;
  increaseButton.disabled = disabled || !hasValue || value >= maximum - Number.EPSILON;
  timeControl.classList.toggle("is-disabled", disabled);
  timeControl.setAttribute("aria-busy", String(timelineEditorBusy));
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
  timeInput.value = timelineMath.clampTime(
    beat.time,
    Number(currentResult?.duration) || Number(resultVideo.duration) || 1,
  ).toFixed(1);
  timeInput.setAttribute("aria-label", "解说出现时间（秒）");
  timeInput.setAttribute("inputmode", "decimal");
  timeInput.setAttribute("aria-describedby", "timeline-edit-status");
  row.dataset.time = timeInput.value;
  timeInput.disabled = timelineEditorBusy;

  const timeControl = document.createElement("div");
  timeControl.className = "event-editor-time-control";
  timeControl.setAttribute("role", "group");
  timeControl.setAttribute("aria-label", "微调解说出现时间");

  const timeStepper = document.createElement("span");
  timeStepper.className = "event-editor-time-stepper";
  timeStepper.setAttribute("aria-hidden", "false");

  const decreaseButton = document.createElement("button");
  decreaseButton.className = "event-editor-time-step event-editor-time-decrease";
  decreaseButton.type = "button";
  decreaseButton.textContent = "▼";
  decreaseButton.title = "提前 0.1 秒";
  decreaseButton.setAttribute("aria-label", "减少 0.1 秒");

  const increaseButton = document.createElement("button");
  increaseButton.className = "event-editor-time-step event-editor-time-increase";
  increaseButton.type = "button";
  increaseButton.textContent = "▲";
  increaseButton.title = "延后 0.1 秒";
  increaseButton.setAttribute("aria-label", "增加 0.1 秒");

  const adjustEventTime = (direction) => {
    if (timeInput.disabled) return;
    if (!timeInput.value.trim()) timeInput.value = row.dataset.time;
    try {
      if (direction < 0) timeInput.stepDown();
      else timeInput.stepUp();
    } catch (_error) {
      return;
    }
    timeInput.dispatchEvent(new Event("input", { bubbles: true }));
    timeInput.dispatchEvent(new Event("change", { bubbles: true }));
  };

  decreaseButton.addEventListener("click", () => adjustEventTime(-1));
  increaseButton.addEventListener("click", () => adjustEventTime(1));
  timeStepper.append(increaseButton, decreaseButton);
  timeControl.append(timeInput, timeStepper);

  const previewButton = document.createElement("button");
  previewButton.className = "event-editor-preview";
  previewButton.type = "button";
  previewButton.textContent = "▶";
  previewButton.title = "从这句对应的画面开始预览";
  previewButton.setAttribute("aria-label", "预览这句对应的画面");
  previewButton.disabled = timelineEditorBusy;
  previewButton.addEventListener("click", () => {
    seekResultVideo(timeInput.value, { autoplay: true, lead: 0.35 });
  });

  timeInput.addEventListener("focus", () => {
    seekResultVideo(timeInput.value, { autoplay: false, lead: 0 });
  });

  timeInput.addEventListener("input", () => {
    syncEventTimeControlState(timeControl);
    const value = Number(timeInput.value);
    const minimum = Number(timeInput.min);
    const maximum = Number(timeInput.max);
    const valid = timeInput.value.trim() !== ""
      && Number.isFinite(value)
      && value >= minimum
      && value <= maximum;
    if (!valid) return;
    timeInput.removeAttribute("aria-invalid");
    seekResultVideo(timeInput.value, { autoplay: false, lead: 0 });
  });

  timeInput.addEventListener("change", () => {
    const rows = getEventEditorRows();
    const values = rows.map((candidate) => (
      candidate === row
        ? timeInput.value
        : candidate.querySelector(".event-editor-time")?.value
    ));
    const validation = timelineMath.validateTimes(
      values,
      Number(currentResult?.duration) || Number(resultVideo.duration) || 1,
    );
    if (!validation.ok) {
      timeInput.setAttribute("aria-invalid", "true");
      timeInput.value = row.dataset.time;
      setTimelineStatus(validation.message, true);
      seekResultVideo(row.dataset.time, { autoplay: false, lead: 0 });
      syncEventTimeControlState(timeControl);
      return;
    }
    const normalizedTime = validation.normalized[rows.indexOf(row)];
    timeInput.value = normalizedTime.toFixed(1);
    row.dataset.time = timeInput.value;
    timeInput.removeAttribute("aria-invalid");
    setTimelineStatus("");
    seekResultVideo(normalizedTime, { autoplay: false, lead: 0 });
    syncEventTimeControlState(timeControl);
    timeControl.classList.add("is-saved");
    window.setTimeout(() => timeControl.classList.remove("is-saved"), 650);
    sortEventEditorRows();
  });

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
  kindSelect.disabled = timelineEditorBusy;

  const textInput = document.createElement("input");
  textInput.className = "event-editor-text";
  textInput.type = "text";
  textInput.maxLength = 80;
  textInput.value = String(beat.text || EVENT_KIND_DEFAULT_TEXT[kindSelect.value]);
  textInput.setAttribute("aria-label", "这句解说词");
  textInput.disabled = timelineEditorBusy;
  textInput.addEventListener("focus", () => {
    seekResultVideo(timeInput.value, { autoplay: false, lead: 0 });
  });

  let previousKind = kindSelect.value;
  kindSelect.addEventListener("change", () => {
    const previousDefault = EVENT_KIND_DEFAULT_TEXT[previousKind] || "继续看这个回合。";
    const nextDefault = EVENT_KIND_DEFAULT_TEXT[kindSelect.value] || "继续看这个回合。";
    if (!textInput.value.trim() || textInput.value.trim() === previousDefault) {
      textInput.value = nextDefault;
    }
    previousKind = kindSelect.value;
  });

  const removeButton = document.createElement("button");
  removeButton.className = "event-editor-remove";
  removeButton.type = "button";
  removeButton.textContent = "×";
  removeButton.title = "删除这句解说";
  removeButton.setAttribute("aria-label", "删除这句解说");
  removeButton.disabled = timelineEditorBusy;
  removeButton.addEventListener("click", () => {
    row.remove();
    refreshEventInsertionControls();
    updateEventCount();
  });

  row.append(previewButton, timeControl, kindSelect, textInput, removeButton);
  syncEventTimeControlState(timeControl);
  return row;
}

function getEventEditorRows() {
  return [...eventTimelineList.querySelectorAll(".event-editor-row")];
}

function getEditorRowTime(row) {
  const value = row?.querySelector(".event-editor-time")?.value;
  const tick = timelineMath.toTick(value);
  return tick === null ? Number.NaN : tick / timelineMath.TICKS_PER_SECOND;
}

function updateEventCount() {
  const count = timelineEditing
    ? getEventEditorRows().length
    : eventTimelineList.querySelectorAll(".event-row").length;
  eventCount.textContent = `${count} 个事件`;
}

function suggestedInsertionTime(index) {
  const rows = getEventEditorRows();
  const duration = Number(currentResult?.duration) || Number(resultVideo.duration) || 1;
  const previous = index > 0 ? getEditorRowTime(rows[index - 1]) : null;
  const next = index < rows.length ? getEditorRowTime(rows[index]) : null;
  return timelineMath.findInsertionTime({
    previous: Number.isFinite(previous) ? previous : null,
    next: Number.isFinite(next) ? next : null,
    duration,
    fallback: Number.isFinite(resultVideo.currentTime) ? resultVideo.currentTime : duration / 2,
  });
}

function createEventInsertionControl(index) {
  const slot = document.createElement("div");
  slot.className = "event-insert-slot";
  const button = document.createElement("button");
  const rows = getEventEditorRows();
  const suggestion = suggestedInsertionTime(index);
  const limitReached = rows.length >= 32;
  const positionLabel = index === 0
    ? "＋ 开头补一句"
    : index === rows.length
      ? "＋ 结尾补一句"
      : "＋ 这里补一句";
  const unavailableLabel = index === 0
    ? "第一句已经贴近开头"
    : index === rows.length
      ? "最后一句已经贴近结尾"
      : "两句太近，先调时间";
  button.type = "button";
  button.className = "event-insert-button";
  button.textContent = limitReached
    ? "已经有 32 句了"
    : suggestion === null
      ? unavailableLabel
      : positionLabel;
  button.disabled = timelineEditorBusy || limitReached || suggestion === null;
  button.title = suggestion === null
    ? "先调整前后解说的出现时间，再从这里补一句"
    : positionLabel.replace("＋ ", "");
  button.setAttribute("aria-label", `${positionLabel.replace("＋ ", "")}，第 ${index + 1} 个位置`);
  button.addEventListener("click", () => {
    if (suggestion !== null) insertEventEditorRow(index, suggestion);
  });
  slot.append(button);
  return slot;
}

function refreshEventInsertionControls() {
  eventTimelineList.querySelectorAll(".event-insert-slot").forEach((slot) => slot.remove());
  if (!timelineEditing) return;
  const rows = getEventEditorRows();
  timelineAddEvent.disabled = timelineEditorBusy || rows.length >= 32;
  rows.forEach((row, index) => {
    eventTimelineList.insertBefore(createEventInsertionControl(index), row);
  });
  eventTimelineList.append(createEventInsertionControl(rows.length));
}

function sortEventEditorRows() {
  const rows = getEventEditorRows().sort((left, right) => {
    const leftTime = getEditorRowTime(left);
    const rightTime = getEditorRowTime(right);
    return (Number.isFinite(leftTime) ? leftTime : Number.POSITIVE_INFINITY)
      - (Number.isFinite(rightTime) ? rightTime : Number.POSITIVE_INFINITY);
  });
  rows.forEach((row) => eventTimelineList.append(row));
  refreshEventInsertionControls();
  updateEventCount();
}

function insertEventEditorRow(index, preferredTime) {
  const rows = getEventEditorRows();
  if (rows.length >= 32) {
    setTimelineStatus("一段视频最多保留 32 句解说。", true);
    return null;
  }
  const duration = Number(currentResult?.duration) || Number(resultVideo.duration) || 1;
  if (preferredTime === null || preferredTime === undefined) {
    setTimelineStatus("这里暂时放不下新解说，请先调整前后两句的出现时间。", true);
    return null;
  }
  const time = timelineMath.clampTime(preferredTime, duration);
  const validation = timelineMath.validateTimes(
    [...rows.map((row) => row.querySelector(".event-editor-time")?.value), time],
    duration,
  );
  if (!validation.ok) {
    setTimelineStatus(validation.message, true);
    return null;
  }
  const row = createEventEditorRow({
    time,
    event_kind: "other",
    text: EVENT_KIND_DEFAULT_TEXT.other,
  });
  eventTimelineList.insertBefore(row, rows[index] || null);
  sortEventEditorRows();
  setTimelineStatus(`已在 ${formatEventTime(time)} 加入一句，写下这段画面的解说吧。`, false);
  row.querySelector(".event-editor-text")?.focus();
  return row;
}

function updateActiveTimelineCue() {
  const rows = timelineEditing
    ? getEventEditorRows()
    : [...eventTimelineList.querySelectorAll(".event-row")];
  if (!rows.length) return;
  const playhead = Math.max(0, Number(resultVideo.currentTime) || 0);
  let activeRow = null;
  let activeTime = Number.NEGATIVE_INFINITY;
  rows.forEach((row) => {
    const time = timelineEditing ? getEditorRowTime(row) : Number(row.dataset.time);
    if (Number.isFinite(time) && time <= playhead + 0.35 && time >= activeTime) {
      activeRow = row;
      activeTime = time;
    }
  });
  rows.forEach((row) => row.classList.toggle("is-active", row === activeRow));
}

function updateReviewPlayhead() {
  const time = Math.max(0, Number(resultVideo.currentTime) || 0);
  if (reviewPlayheadTime) reviewPlayheadTime.textContent = formatEventTime(time);
  if (timelineEditing && timelineAddEvent) {
    timelineAddEvent.textContent = `＋ 在当前画面 ${formatEventTime(time)} 补一句`;
  }
  updateActiveTimelineCue();
}

function renderEventTimeline(result) {
  const beats = Array.isArray(result?.beats)
    ? [...result.beats].sort((left, right) => {
      const leftTime = Number(left?.time);
      const rightTime = Number(right?.time);
      return (Number.isFinite(leftTime) ? leftTime : Number.POSITIVE_INFINITY)
        - (Number.isFinite(rightTime) ? rightTime : Number.POSITIVE_INFINITY);
    })
    : [];
  workspace.classList.toggle("is-correcting", timelineEditing);
  reviewNavStudio.disabled = timelineEditing;
  reviewNavStudio.title = timelineEditing ? "请先取消或提交当前修改" : "返回转播台调整设置";
  reviewNavScript.disabled = !beats.length;
  eventTimelineList.replaceChildren();
  eventTimeline.classList.toggle("hidden", !beats.length);
  if (!beats.length) {
    window.requestAnimationFrame(updateReviewScrollCue);
    return;
  }
  eventCount.textContent = `${beats.length} 个事件`;
  timelineEditToggle.textContent = timelineEditing ? "修改中" : "直接修改";
  timelineEditToggle.disabled = timelineEditing || timelineEditorBusy;
  timelineEditActions.classList.toggle("hidden", !timelineEditing);
  eventTimelineHelp.textContent = timelineEditing
    ? "想补哪一句，就点前后解说之间的“这里补一句”；也可以播放到目标画面后，从底部按当前画面补充。生成修正版时会复用现有视频分析。"
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
  if (timelineEditing) refreshEventInsertionControls();
  updateEventCount();
  updateReviewPlayhead();
  syncSubmitAvailability();
  window.requestAnimationFrame(updateReviewScrollCue);
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
  const timeValidation = timelineMath.validateTimes(
    rows.map((row) => row.querySelector(".event-editor-time")?.value),
    duration,
  );
  if (!timeValidation.ok) throw new Error(timeValidation.message);
  const beats = rows.map((row, index) => {
    const time = timeValidation.normalized[index];
    const eventKind = String(row.querySelector(".event-editor-kind")?.value || "");
    const commentary = String(row.querySelector(".event-editor-text")?.value || "").trim();
    if (!EVENT_KIND_LABELS[eventKind]) {
      throw new Error(`第 ${index + 1} 个事件类型不正确。`);
    }
    if (!commentary || commentary.length > 80) {
      throw new Error(`第 ${index + 1} 句解说需要 1–80 个字。`);
    }
    return { time, event_kind: eventKind, text: commentary };
  });
  return beats.sort((left, right) => left.time - right.time);
}

function setTimelineEditorBusy(busy) {
  timelineEditorBusy = busy;
  timelineEditToggle.disabled = busy || timelineEditing;
  timelineCancelEdit.disabled = busy;
  timelineRenderRevision.disabled = busy;
  refreshEventInsertionControls();
  eventTimelineList.querySelectorAll(".event-editor-row input, .event-editor-row select, .event-editor-row button").forEach((control) => {
    control.disabled = busy;
  });
  eventTimelineList.querySelectorAll(".event-editor-time-control").forEach((control) => {
    syncEventTimeControlState(control);
  });
  timelineAddEvent.disabled = busy || getEventEditorRows().length >= 32;
  timelineRenderRevision.textContent = busy ? "正在生成修正版…" : "重新配音并生成修正版";
  syncSubmitAvailability();
}

function showResult(job) {
  const result = job.result;
  currentResult = result;
  resumeResultButton.classList.add("hidden");
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
  if (result.width && result.height) {
    previewDimensions.textContent = `原片与成片均为 ${result.width} × ${result.height} · 未裁切`;
  }
  resultDetails.scrollTop = 0;
  setReviewNavActive("video");
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
  setReviewNavActive("script");
  if (shouldScroll) scrollReviewToTimeline();
  window.requestAnimationFrame(() => eventTimelineList.querySelector(".event-editor-text")?.focus());
}

timelineEditToggle.addEventListener("click", () => {
  enterTimelineCorrection(false);
});

openCorrectionButton.addEventListener("click", () => {
  enterTimelineCorrection(true);
});

reviewNavVideo.addEventListener("click", scrollReviewToVideo);
reviewNavScript.addEventListener("click", () => scrollReviewToTimeline({ focus: true }));
reviewScrollCue.addEventListener("click", () => scrollReviewToTimeline({ focus: true }));
settingsScrollCue.addEventListener("click", scrollSettingsForward);
settingsScrollBody.addEventListener("scroll", updateSettingsScrollCue, { passive: true });
resultDetails.addEventListener("scroll", updateReviewViewportNavigation, { passive: true });
window.addEventListener("scroll", updateReviewViewportNavigation, { passive: true });
window.addEventListener("resize", updateReviewViewportNavigation, { passive: true });
window.addEventListener("resize", updateSettingsScrollCue, { passive: true });

resultVideo.addEventListener("timeupdate", updateReviewPlayhead);
resultVideo.addEventListener("seeked", updateReviewPlayhead);
resultVideo.addEventListener("loadedmetadata", updateReviewPlayhead);

timelineCancelEdit.addEventListener("click", () => {
  if (!currentResult) return;
  timelineEditing = false;
  setTimelineStatus("");
  renderEventTimeline(currentResult);
});

timelineAddEvent.addEventListener("click", () => {
  const duration = Number(currentResult?.duration) || Number(resultVideo.duration) || 1;
  const currentTime = Number(resultVideo.currentTime);
  const time = timelineMath.clampTime(
    Number.isFinite(currentTime) ? currentTime : duration / 2,
    duration,
  );
  const rows = getEventEditorRows();
  const validation = timelineMath.validateTimes(
    [...rows.map((row) => row.querySelector(".event-editor-time")?.value), time],
    duration,
  );
  if (!validation.ok) {
    setTimelineStatus(
      "当前画面已有一句解说，请移动播放头，或使用两句之间的插入按钮。",
      true,
    );
    return;
  }
  const insertIndex = rows.findIndex((row) => getEditorRowTime(row) > time);
  insertEventEditorRow(insertIndex === -1 ? rows.length : insertIndex, time);
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
    setTimelineStatus("AI 正在按新稿重新配音，画面与当前解说词会保留在这里。", false);
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
  try {
    const restoreUrl = savedJobId ? `/api/jobs/${savedJobId}` : "/api/jobs/latest";
    const response = await fetch(restoreUrl, { cache: "no-store" });
    if (response.status === 404) {
      if (savedJobId) clearSavedJob();
      return;
    }
    if (!response.ok) throw new Error("无法恢复上次任务");
    const job = await response.json();
    currentJobId = String(job.id || savedJobId || "");
    if (currentJobId) saveCurrentJob(currentJobId);
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
    showSubmitFeedback("后台服务没有准备好，请先重新启动服务。", true);
    return;
  }
  if (timelineEditing) {
    showSubmitFeedback("请先提交或取消右侧的逐句修改，再开始新的成片。", true);
    scrollReviewToTimeline({ focus: true });
    return;
  }
  if (!fileInput.files[0]) {
    showSubmitFeedback("再次生成需要重新选择原视频，正在为你打开文件选择器。", true);
    fileInput.click();
    return;
  }
  if (!selectedFileValid) {
    const message = fileValidation.textContent || "正在读取视频信息，请稍后再试。";
    setFileValidation(message);
    showSubmitFeedback(message, true);
    return;
  }
  showSubmitFeedback("设置已确认，正在上传视频并生成成片。", false);
  resumeResultButton.classList.add("hidden");
  currentResult = null;
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
    showSubmitFeedback(error.message || "生成失败，请检查后重试。", true);
    document.querySelector("#error-message").textContent = error.message || "未知错误";
    retryButton.classList.toggle("hidden", !currentJobId || !currentJobRetryable);
    showState("error");
  } finally {
    fileInput.disabled = false;
    dropZone.classList.remove("is-busy");
    form.removeAttribute("aria-busy");
    syncSubmitAvailability();
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
  resumeResultButton.classList.add("hidden");
  clearSavedJob();
  retryButton.classList.add("hidden");
  showState("empty");
});

function returnToStudioSetup() {
  resultVideo.pause();
  timelineEditing = false;
  setTimelineStatus("");
  resumeResultButton.classList.toggle("hidden", !currentResult);
  showState("empty");
  const behavior = reducedMotionQuery.matches ? "auto" : "smooth";
  workspace.scrollIntoView({ behavior, block: "start" });
}

returnToSetupButton.addEventListener("click", returnToStudioSetup);
reviewNavStudio.addEventListener("click", returnToStudioSetup);

resumeResultButton.addEventListener("click", () => {
  if (!currentResult) return;
  timelineEditing = false;
  resumeResultButton.classList.add("hidden");
  setTimelineStatus("");
  renderEventTimeline(currentResult);
  showState("completed");
  window.requestAnimationFrame(() => fitPreviewFrame(resultVideo, resultVideoWrap, 640));
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

document.documentElement.classList.toggle("fine-pointer", finePointerQuery.matches);

if (promoVideo && promoPlayToggle) {
  const promoFrame = promoVideo.closest(".promo-feed-frame");
  const promoBooth = promoVideo.closest(".manga-booth");

  const syncPromoBackdrop = ({ force = false } = {}) => {
    if (!promoBackdrop || !Number.isFinite(promoVideo.currentTime)) return;
    const drift = Math.abs(promoBackdrop.currentTime - promoVideo.currentTime);
    if (force || drift > 0.18) {
      try {
        promoBackdrop.currentTime = promoVideo.currentTime;
      } catch (_error) {
        // Metadata may still be loading; the next timeupdate will retry.
      }
    }
    promoBackdrop.playbackRate = promoVideo.playbackRate;
  };

  const setPromoIdleState = () => {
    promoVideo.pause();
    promoBackdrop?.pause();
    promoVideo.controls = false;
    promoVideo.muted = true;
    promoVideo.loop = false;
    promoVideo.currentTime = 0;
    if (promoBackdrop) {
      promoBackdrop.muted = true;
      promoBackdrop.loop = false;
      try {
        promoBackdrop.currentTime = 0;
      } catch (_error) {
        // Keep the static poster until metadata becomes available.
      }
    }
    promoFrame?.classList.remove("is-playing");
    promoBooth?.classList.remove("promo-is-playing");
    promoPlayToggle.disabled = false;
    promoPlayToggle.removeAttribute("aria-hidden");
  };

  setPromoIdleState();

  promoPlayToggle.addEventListener("click", async () => {
    promoVideo.loop = false;
    promoVideo.controls = true;
    promoVideo.muted = false;
    promoVideo.currentTime = 0;
    syncPromoBackdrop({ force: true });
    promoFrame?.classList.add("is-playing");
    promoBooth?.classList.add("promo-is-playing");
    promoPlayToggle.disabled = true;
    promoPlayToggle.setAttribute("aria-hidden", "true");
    try {
      promoBackdrop?.play().catch(() => {});
      await promoVideo.play();
      promoVideo.focus({ preventScroll: true });
    } catch (_error) {
      setPromoIdleState();
      promoPlayToggle.focus({ preventScroll: true });
    }
  });

  promoVideo.addEventListener("ended", () => {
    setPromoIdleState();
    promoPlayToggle.focus({ preventScroll: true });
  });

  promoVideo.addEventListener("play", () => {
    syncPromoBackdrop({ force: true });
    promoBackdrop?.play().catch(() => {});
  });
  promoVideo.addEventListener("pause", () => promoBackdrop?.pause());
  promoVideo.addEventListener("seeking", () => syncPromoBackdrop({ force: true }));
  promoVideo.addEventListener("timeupdate", () => syncPromoBackdrop());
  promoVideo.addEventListener("ratechange", () => syncPromoBackdrop({ force: true }));

  reducedMotionQuery.addEventListener("change", (event) => {
    if (event.matches) {
      setPromoIdleState();
    }
  });
}
