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
PostToolUse 훅: .py 파일 저장 후 모듈 임포트 검사

ImportError, AttributeError, 순환 임포트 등을
코드 실행 전에 미리 잡아냅니다.
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/정화민/Desktop/IR센터 MCP")

# 임포트 검사 대상 모듈 (파일명 → 모듈 경로)
MODULE_MAP = {
    "config.py":          "report_app.config",
    "data_loader.py":     "report_app.data_loader",
    "chart_generator.py": "report_app.chart_generator",
    "gpt_reporter.py":    "report_app.gpt_reporter",
    "report_builder.py":  "report_app.report_builder",
    "app.py":             None,  # app.py는 streamlit 전용 → ast 구문 검사만
}

try:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    tool_input = data.get("tool_input", {})
    file_path  = tool_input.get("file_path", "")

    if not file_path or not file_path.endswith(".py"):
        sys.exit(0)

    fname = Path(file_path).name

    if fname not in MODULE_MAP:
        sys.exit(0)

    module = MODULE_MAP[fname]

    if module is None:
        # app.py: streamlit 의존성 때문에 직접 임포트 불가 → ast로만 검사
        print(f"[임포트 검사] {fname}: Streamlit 앱 — 구문 검사만 수행", file=sys.stderr)
        sys.exit(0)

    # 모듈 임포트 시도 (서브프로세스로 격리 실행)
    code = f"""
import sys
sys.path.insert(0, r'{PROJECT_ROOT}')
try:
    import importlib
    mod = importlib.import_module('{module}')
    print('OK')
except Exception as e:
    print(f'ERROR: {{type(e).__name__}}: {{e}}')
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(PROJECT_ROOT),
    )

    output = result.stdout.strip()

    if output == "OK":
        print(f"[임포트 검사 ✓] {fname} ({module}) — 정상", file=sys.stderr)
    else:
        print(f"\n{'='*55}", file=sys.stderr)
        print(f"[임포트 오류 ✗] {fname}", file=sys.stderr)
        print(f"  {output}", file=sys.stderr)
        if result.stderr:
            print(f"  {result.stderr.strip()[:300]}", file=sys.stderr)
        print(f"{'='*55}\n", file=sys.stderr)

except Exception as e:
    print(f"[임포트 검사 오류] {e}", file=sys.stderr)

sys.exit(0)
