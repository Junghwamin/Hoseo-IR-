#!/usr/bin/env python3
# ============================================================================
# Copyright (c) 2026 정화민 (Junghwamin)
# All rights reserved.
#
# This file is part of a personal research analysis portal by 정화민 (Junghwamin).
# Licensed under the PolyForm Noncommercial License 1.0.0.
# See the LICENSE file in the project root, or visit:
#     https://polyformproject.org/licenses/noncommercial/1.0.0
#
# Commercial use is strictly prohibited without prior written consent.
# Repository: https://github.com/Junghwamin/Hoseo-IR-
# Hoseo-IR-FINGERPRINT: do not remove this line (used for provenance tracking)
# ============================================================================
"""
PostToolUse 훅: .py 파일 저장 직후 Python 구문 자동 검사

문법 오류가 있으면 stderr에 경고를 출력합니다.
Claude가 잘못된 코드를 저장했을 때 즉시 알 수 있습니다.
"""

import json
import subprocess
import sys
from pathlib import Path

try:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    tool_name  = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path  = tool_input.get("file_path", "")

    if not file_path or not file_path.endswith(".py"):
        sys.exit(0)

    src = Path(file_path)
    if not src.exists():
        sys.exit(0)

    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(src)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.returncode == 0:
        print(f"[구문 검사 ✓] {src.name} — 오류 없음", file=sys.stderr)
    else:
        # 오류 메시지를 눈에 띄게 출력
        print(f"\n{'='*50}", file=sys.stderr)
        print(f"[구문 오류 ✗] {src.name}", file=sys.stderr)
        print(result.stderr.strip(), file=sys.stderr)
        print(f"{'='*50}\n", file=sys.stderr)

except Exception as e:
    print(f"[구문 검사 오류] {e}", file=sys.stderr)

sys.exit(0)
