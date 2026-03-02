#!/bin/bash
# ===========================================================================
# IR센터 연구실적 분석 포털 - macOS 런처
#
# .app 번들 내에서 실행되어 Streamlit 서버를 시작하고 브라우저를 연다.
# ===========================================================================

DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
APP_DIR="$DIR/app"
VENV_DIR="$DIR/python-venv"
PYTHON="$VENV_DIR/bin/python3"
PORT=8501

export PYTHONPATH="$APP_DIR"
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# 사용 가능한 포트 찾기
find_free_port() {
    local port=$PORT
    while [ $port -le 8510 ]; do
        if ! lsof -i :$port > /dev/null 2>&1; then
            echo $port
            return
        fi
        port=$((port + 1))
    done
    echo $PORT
}

PORT=$(find_free_port)

# Streamlit 서버 시작 (백그라운드)
"$PYTHON" -m streamlit run "$APP_DIR/report_app/app.py" \
    --server.headless true \
    --server.port "$PORT" &

SERVER_PID=$!

# 서버 준비 대기
echo "서버 시작 대기 중..."
for i in $(seq 1 60); do
    if curl -s "http://localhost:$PORT" > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# 브라우저 열기
open "http://localhost:$PORT"

# 서버 프로세스 대기 (종료 시까지)
wait $SERVER_PID
