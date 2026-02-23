#!/usr/bin/env python3
"""
PostToolUse 훅: requirements.txt 변경 시 pip 자동 설치

requirements.txt 파일이 저장되면 즉시 pip install -r 를 실행합니다.
패키지를 수동으로 설치하지 않아도 됩니다.
"""

import json
import subprocess
import sys
from pathlib import Path

try:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    tool_input = data.get("tool_input", {})
    file_path  = tool_input.get("file_path", "")

    if "requirements.txt" not in file_path:
        sys.exit(0)

    req_path = Path(file_path)
    if not req_path.exists():
        sys.exit(0)

    print(f"\n[패키지 자동 설치] requirements.txt 변경 감지 → pip install 실행 중...", file=sys.stderr)

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_path), "-q"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.returncode == 0:
        print(f"[패키지 설치 ✓] 모든 패키지 설치/업데이트 완료", file=sys.stderr)
    else:
        print(f"[패키지 설치 ✗] 오류 발생:", file=sys.stderr)
        print(result.stderr.strip(), file=sys.stderr)

except Exception as e:
    print(f"[pip 자동 설치 오류] {e}", file=sys.stderr)

sys.exit(0)
