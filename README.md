# 篮球高光 AI 解说 · MVP

上传一段 3–90 秒篮球视频，自动完成关键画面抽取、中文解说稿、配音、现场声混音、字幕和 MP4 成片。

> 安全提醒：不要把 `.env`、`.data/`、用户视频或授权人声素材提交到 Git。仓库只提供 `.env.example`；API Key、供应商 voice ID 和授权音色试听文件都应保留在部署者自己的机器或私有密钥服务中。

## 第一版边界

- 输入：MP4、MOV、M4V、WebM，最大 300 MB。
- 风格：热血、专业、轻松。
- AI：`qwen3.5-omni-flash` 先联合理解完整画面与原始现场声，`qwen3.7-flash` 再把观察结果整理为受约束的逐球解说和严格 JSON；Omni 不可用时自动回退到关键画面分析。
- 配音：网页可在 `qwen-audio-3.0-tts-plus` 原创赛事男声与 `MiniMax/speech-2.8-hd` 成熟播报男声之间切换；同一回合的相邻 2–3 句会合成一组连续语气，再按真实停顿拆回动作时间点。
- 节奏：从开场到收尾持续解说，采用“平稳铺垫—动作短句加速—结果短促爆发—一句自然余韵”的结构。所有音色均为原创 AI 合成音色，不复刻或模仿任何真实解说员的声纹、名句、口头禅和个人标志。
- 活人感：项目内置 `commentary_style/basketball_live.py` 风格包和确定性口播检查器。它会拦截连续五字分句、同长句排队、压坏语法的残句和重复起调，并要求完整句与动作短句交替。
- 现场表达：内置 10 类、57 条原创口语节奏样例，覆盖传导、突破、出手、命中、封盖、抢断、转换和结果余韵。样例只在对应画面证据成立时解锁，不复制真实主播的名句或固定口头禅。
- 现场声：在本机对原片音轨做窄带声学检测，并围绕可能的回合停顿补抽画面。音频候选只作为后台线索，不会作为检测术语写入口播，也不会仅凭声音断言犯规、罚球或责任球员。
- 画面：预览和导出均保留原片宽高比与像素尺寸，不主动裁切或拉伸。
- 没有 Qwen 密钥时仍可完成上传、配音和视频合成，但只使用不描述具体动作的安全演示稿。
- 第一版把整段输入制作成“集锦风格成片”，暂不自动从一场长比赛中剪出多个高光。

比分、球员姓名和投篮分值只有在用户明确填写，且画面能够支持时才允许进入解说。这样可以显著减少模型“看错还硬说”的问题。

## 直接使用（macOS）

1. 在 Finder 中打开本项目文件夹。
2. 双击 **`启动篮球高光.command`**。
3. 首次运行会自动创建环境并安装视频组件，完成后会自动打开浏览器。
4. 保持启动器的终端窗口开启；关闭窗口会停止服务。

不要直接双击 `static/index.html`。HTML 页面本身不包含视频处理服务，直接打开只能看到界面，无法生成成片。页面现在会检测这种情况并给出明确提示。

要求 macOS、Python 3.11+ 和首次安装依赖时可用的网络。项目会优先使用系统 FFmpeg；没有安装时，`imageio-ffmpeg` 会自动提供可执行文件。

## 命令行运行（开发者）

```bash
cd /path/to/basketball-highlight-mvp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app:app --reload --port 8765
```

打开 <http://127.0.0.1:8765>。

页面右上角会显示真实运行状态：

- `AI 已连接`：Qwen 音画理解、文本编排、配音和成片均可使用。
- `演示模式`：上传、配音、字幕和视频合成可用，但解说稿不会分析真实动作。
- `服务未连接/运行环境异常`：页面会停止提交并显示对应解决方法。

## 开启真实 AI 音画解说

启动页面后，如果右上角显示“演示模式”，点击提示条中的 **配置 AI**，在本地页面里填写阿里云百炼 API Key 即可。密钥写入项目的 `.env` 文件，不保存在浏览器里，也不会通过接口返回。

也可以手动编辑 `.env`：

```dotenv
QWEN_API_KEY=你的阿里云百炼密钥
QWEN_MODEL=qwen3.7-flash
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_VIDEO_MODEL=qwen3.5-omni-flash
QWEN_VIDEO_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_VIDEO_FPS=4
QWEN_VIDEO_FALLBACK=true
QWEN_LOCAL_SHOT_REVIEW=true
QWEN_LOCAL_SHOT_REVIEW_MAX_REQUESTS=4
QWEN_LOCAL_SHOT_REVIEW_BUDGET_SECONDS=40
```

`QWEN_VIDEO_BASE_URL` 默认可以与文本模型共用兼容接口；如果当前账号仅在百炼业务空间中开通 Omni，请将它改为该 Workspace 的 `compatible-mode/v1` 地址。`QWEN_VIDEO_FPS` 控制第一遍模型理解快动作时的目标抽帧率，程序会结合片长自动限制实际值。`QWEN_LOCAL_SHOT_REVIEW=true` 会从原片裁取投篮附近的小窗口，以 10 FPS 复核出手与结果；`QWEN_LOCAL_SHOT_REVIEW_MAX_REQUESTS` 默认限制为 4 个分组，`QWEN_LOCAL_SHOT_REVIEW_BUDGET_SECONDS` 默认给整个局部复核阶段 40 秒。预算耗尽或首次遇到 HTTP 429 时，剩余候选会停止请求并保留第一遍事件时间轴。其他局部复核失败同样安全回退；`QWEN_VIDEO_FALLBACK=true` 则表示整个 Omni 请求、超时或分析副本准备失败时，继续使用已有关键画面链路完成任务。

网页内保存密钥后无需重启；手动编辑 `.env` 后需要重启服务。正常路径采用两步架构：程序先在任务目录生成不修改原片的 `analysis-omni.mp4` 分析副本，保留完整时长与原始现场声音轨，并压缩到适合 Base64 API 请求的大小；`qwen3.5-omni-flash` 只负责按时间观察球权、动作、篮筐结果和声音证据，不直接写最终解说。随后 `qwen3.7-flash` 对观察记录做事实约束、JSON 结构化和逐球口播编排。

关键画面链路始终保留。程序会按片长抽取最多 48 张常规画面，遇到现场声中的停顿候选会补抽邻近画面，总数最多 56 张；30 秒视频通常约 30–40 张。Omni 无法调用时会自动使用这些画面，并在结果页显示“关键画面分析（Omni 已自动降级）”，不会把底层接口错误暴露在网页上。两种路径都会生成最多 32 段逐球解说，首句尽快进入、末句覆盖视频收尾，并且只陈述能够确认的篮球动作。

活人感篮球解说 Skill 同时接入观察、编排、修稿和配音四个阶段。初稿至少包含一定比例的完整口语句，高潮附近才允许短句；连续五字齐句、所有段落同长或“接球稳、投篮偏、断球下”一类残句会触发自动修稿。配音过长时，系统优先把相邻事实合并成更少的完整句，再重新对齐时间轴，不再把每一句压缩成四五个字。修稿后仍不自然或没有覆盖完整视频时，系统会停止导出，避免把明显的机器稿交付给用户。

生成解说后，程序会把相邻语义句合并成连续语气配音，利用组内真实短停顿重新切分，再通过独立延迟和混音把每句放回对应动作窗口。切口带有短淡入淡出，字幕使用实际配音起止时间。定时路径只允许 `0.97×–1.06×` 的轻微节奏调整，并通过静音检测限制最长无解说间隔；不满足同步和持续解说质量门槛时会明确报错。

## 双配音引擎

两套配音都通过阿里云百炼调用，并与画面分析共用同一个 API Key：

```dotenv
TTS_PROVIDER=qwen_audio
QWEN_AUDIO_TTS_MODEL=qwen-audio-3.0-tts-plus
QWEN_AUDIO_TTS_VOICE=longanlufeng
MINIMAX_TTS_MODEL=MiniMax/speech-2.8-hd
MINIMAX_TTS_VOICE="Chinese (Mandarin)_Radio_Host"
MINIMAX_ENABLED=false
```

Qwen Audio Plus 支持自然语言情绪指令，默认使用平台男声，也可以使用本项目通过声音设计生成的 `courtcast` 原创音色。MiniMax 2.8 HD 使用平台系统男声和固定的情绪参数；需要先在百炼模型广场开通该模型，再把 `MINIMAX_ENABLED` 改为 `true`，否则网页会如实显示“未开通”并禁止提交。网页不提供录音上传、声音克隆或自由 voice ID，因此不能用来仿冒真实人物；真实配音员音色只有在取得明确授权后才能另行接入。

旧 `qwen3-tts-instruct-flash` 仍保留为内部兼容路径，但不在新网页中展示。

项目也保留了 OpenAI Speech API 兼容接口：

```dotenv
TTS_PROVIDER=openai_compatible
TTS_API_KEY=你的密钥
TTS_URL=https://api.openai.com/v1/audio/speech
TTS_MODEL=gpt-4o-mini-tts
TTS_VOICE=alloy
```

macOS 本地语音现在仅用于无密钥的演示模式。

## 生成文件

每个任务保存在 `.data/<任务ID>/`：

- `plan.json`：标题、解说稿、确认动作、模型模式，以及仅供内部复核的现场声候选。
- `analysis-omni.mp4`：供 Omni 使用的临时完整音视频分析副本；保留时长和现场声，不替换或改变用户原片。
- `commentary.srt`：中文字幕。
- `voice-beats/`：按连续语气组生成的原始配音，以及必要时的逐句降级配音。
- `voice-timeline.wav`：逐句修剪并按动作时间点组装后的完整解说音轨。
- `highlight.mp4`：最终成片。

服务重启后内存中的任务列表会清空，但生成文件仍在磁盘。正式版应把任务状态迁移到 SQLite/PostgreSQL，并增加定时清理。

## 测试

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
node --check static/app.js
```

测试覆盖事件时间锚点、投篮结果复核、专业术语证据边界、真人口语节奏、夸赞密度、授权音色白名单、字幕与配音时间线，以及 API 上传和任务恢复流程。

## 隐私与授权音色

- `.data/` 会保存用户原片、分析副本、配音中间件和最终成片，已在 `.gitignore` 中排除。
- `static/voice-authorized-*.wav` 是授权人声试听素材，已在 `.gitignore` 中排除，不随源码仓库发布。
- `QWEN_AUDIO_VOICE_AUTHORIZED_1_ID` 只从服务端环境变量读取，不会通过接口返回。
- 接入任何真人音色前，应取得音色本人对录制、合成、产品用途和发布范围的明确授权。
- 如曾误提交密钥，应立即在供应商后台撤销并重新生成；只从 Git 历史删除字符串并不能让旧密钥失效。
