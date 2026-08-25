#!/bin/zsh

set -u

APP_DIR="${0:A:h}"
cd "$APP_DIR" || exit 1
mkdir -p .data

print ""
print "========================================"
print "  篮球高光 AI 解说 · 本地启动器"
print "========================================"
print ""

fail_and_wait() {
  print ""
  print "启动失败：$1"
  print ""
  read "?按回车键关闭窗口…"
  exit 1
}

if [[ -n "${BASKETBALL_RUNTIME_PYTHON:-}" ]]; then
  APP_PYTHON="$BASKETBALL_RUNTIME_PYTHON"
  [[ -x "$APP_PYTHON" ]] || fail_and_wait "指定的 Python 不可执行：$APP_PYTHON"
else
  SYSTEM_PYTHON="$(command -v python3 2>/dev/null || true)"
  [[ -n "$SYSTEM_PYTHON" ]] || fail_and_wait "没有找到 Python 3。请先安装 Python 3.11 或更高版本。"

  PYTHON_OK="$($SYSTEM_PYTHON -c 'import sys; print(int(sys.version_info >= (3, 11)))' 2>/dev/null || true)"
  [[ "$PYTHON_OK" == "1" ]] || fail_and_wait "需要 Python 3.11 或更高版本。"

  if [[ ! -x .venv/bin/python ]]; then
    print "首次运行，正在创建本地运行环境…"
    "$SYSTEM_PYTHON" -m venv .venv || fail_and_wait "无法创建 Python 虚拟环境。"
  fi

  APP_PYTHON="$APP_DIR/.venv/bin/python"
  REQUIREMENTS_HASH="$(shasum -a 256 requirements.txt | awk '{print $1}')"
  REQUIREMENTS_MARKER="$APP_DIR/.venv/.requirements-$REQUIREMENTS_HASH"

  if [[ ! -f "$REQUIREMENTS_MARKER" ]]; then
    print "正在安装视频处理组件，第一次可能需要几分钟…"
    "$APP_PYTHON" -m pip install --disable-pip-version-check -r requirements.txt \
      || fail_and_wait "依赖安装失败。请检查网络后重新双击启动器。"
    touch "$REQUIREMENTS_MARKER"
  fi
fi

if [[ ! -f .env ]]; then
  cp .env.example .env || fail_and_wait "无法创建 .env 配置文件。"
  print "已创建本地配置文件 .env"
fi

APP_PORT="${BASKETBALL_PORT:-8765}"
if curl -fsS "http://127.0.0.1:$APP_PORT/health" >/dev/null 2>&1; then
  print "服务已经在运行，正在打开浏览器…"
  if [[ "${BASKETBALL_NO_OPEN:-0}" != "1" ]]; then
    open "http://127.0.0.1:$APP_PORT"
  fi
  exit 0
fi

while lsof -nP -iTCP:"$APP_PORT" -sTCP:LISTEN >/dev/null 2>&1; do
  APP_PORT=$((APP_PORT + 1))
done

print "正在启动服务：http://127.0.0.1:$APP_PORT"
print "提示：关闭这个终端窗口会停止服务。"
print ""

"$APP_PYTHON" -m uvicorn app:app --host 127.0.0.1 --port "$APP_PORT" &
SERVER_PID=$!

stop_server() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap stop_server INT TERM EXIT

READY=0
for _ in {1..80}; do
  if curl -fsS "http://127.0.0.1:$APP_PORT/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

if [[ "$READY" != "1" ]]; then
  stop_server
  fail_and_wait "后台服务没有成功启动，请查看上方错误信息。"
fi

print "服务已就绪。"
if [[ "${BASKETBALL_NO_OPEN:-0}" != "1" ]]; then
  open "http://127.0.0.1:$APP_PORT"
fi

wait "$SERVER_PID"
