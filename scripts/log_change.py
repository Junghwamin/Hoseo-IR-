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
# Repository: https://github.com/Junghwamin/Hoseo-Research
# HOSEO-RESEARCH-FINGERPRINT: do not remove this line (used for provenance tracking)
# ============================================================================
"""
PostToolUse 훅: .py 파일 변경 후 change_log.txt + CLAUDE.md 작업 로그 자동 기록

Claude가 Write/Edit 도구로 .py 파일을 수정한 직후 실행됩니다.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHANGE_LOG = PROJECT_ROOT / "change_log.txt"
CLAUDE_MD   = PROJECT_ROOT / "CLAUDE.md"

# 기록 대상 확장자 (CLAUDE.md 자체는 제외 → 무한루프 방지)
LOG_EXTS = {".py"}

try:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    tool_name  = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path  = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    src = Path(file_path)

    if src.suffix not in LOG_EXTS:
        sys.exit(0)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today     = datetime.now().strftime("%Y-%m-%d")
    action    = "신규 생성" if tool_name == "Write" else "수정"
    log_line  = f"{timestamp} | {action} | {src.name} ({src.parent.name}/)\n"

    # ── 1. change_log.txt 에 추가 ──────────────────────────────────────
    with open(CHANGE_LOG, "a", encoding="utf-8") as f:
        f.write(log_line)

    # ── 2. CLAUDE.md 작업 로그 섹션에 추가 ────────────────────────────
    # "## 작업 로그" 섹션의 테이블 마지막 행 뒤에 오늘 날짜 항목 추가
    # 동일 날짜+파일 중복 방지
    if CLAUDE_MD.exists():
        content = CLAUDE_MD.read_text(encoding="utf-8")
        entry = f"| {today} | {action}: `{src.name}` |"

        if entry not in content:
            # 테이블 마지막 줄 찾아 그 뒤에 삽입
            lines = content.splitlines(keepends=True)
            insert_idx = None
            in_log_section = False

            for i, line in enumerate(lines):
                if "## 작업 로그" in line:
                    in_log_section = True
                if in_log_section and line.startswith("| "):
                    insert_idx = i  # 마지막 테이블 행 위치 갱신

            if insert_idx is not None:
                lines.insert(insert_idx + 1, entry + "\n")
                CLAUDE_MD.write_text("".join(lines), encoding="utf-8")
                print(f"[로그 기록] CLAUDE.md 작업 로그 업데이트: {src.name}", file=sys.stderr)

except Exception as e:
    print(f"[로그 오류] {e}", file=sys.stderr)

sys.exit(0)
