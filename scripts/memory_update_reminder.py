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
Stop 훅: 메모리 파일 업데이트 리마인더

Claude가 작업을 완료하려 할 때 실행된다.
이번 세션에서 report_app/ 하위 파일이 수정되었으면
관련 메모리 파일 업데이트를 요청하는 메시지를 stdout으로 출력한다.
(stdout 출력 → Claude에게 system-reminder로 전달됨)
"""

import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/정화민/Desktop/IR센터 MCP")
MEMORY_DIR = Path("C:/Users/정화민/.claude/projects/C--Users-----Desktop-IR---MCP/memory")
CHANGE_LOG = PROJECT_ROOT / "change_log.txt"

# 파일→메모리 매핑: 어떤 파일이 수정되면 어떤 메모리를 업데이트해야 하는지
FILE_MEMORY_MAP = {
    "app.py":              ["architecture.md", "session-state.md"],
    "config.py":           ["architecture.md", "data-pipeline.md", "gpt-prompts.md"],
    "data_loader.py":      ["data-pipeline.md", "session-state.md"],
    "chart_generator.py":  ["data-pipeline.md"],
    "gpt_reporter.py":     ["gpt-prompts.md"],
    "report_builder.py":   ["data-pipeline.md"],
    "styles.py":           ["components.md"],
    "sidebar.py":          ["components.md", "architecture.md"],
    "toolbar.py":          ["components.md"],
    "metric_card.py":      ["components.md"],
    "chart_card.py":       ["components.md"],
    "gpt_section.py":      ["components.md", "session-state.md"],
    "research.py":         ["architecture.md", "session-state.md", "design-patterns.md"],
    "home.py":             ["architecture.md"],
    "settings.py":         ["architecture.md"],
    "전처리":              ["data-pipeline.md"],
}

try:
    today = datetime.now().strftime("%Y-%m-%d")
    today_changes = []

    if CHANGE_LOG.exists():
        lines = CHANGE_LOG.read_text(encoding="utf-8").splitlines()
        today_changes = [l for l in lines if l.startswith(today)]

    if not today_changes:
        sys.exit(0)

    # 수정된 파일에서 업데이트 필요한 메모리 파일 추출
    memory_to_update = set()
    changed_files = []

    for line in today_changes:
        parts = line.split(" | ")
        if len(parts) >= 3:
            fname = parts[2].strip()
            changed_files.append(fname)
            for key, memories in FILE_MEMORY_MAP.items():
                if key in fname:
                    memory_to_update.update(memories)

    # MEMORY.md는 항상 업데이트 대상
    if memory_to_update:
        memory_to_update.add("MEMORY.md")

    if memory_to_update:
        # stdout으로 출력 → Claude에게 system-reminder로 전달
        print("[MEMORY UPDATE REQUIRED]")
        print(f"이번 세션에서 수정된 파일: {', '.join(set(changed_files))}")
        print(f"업데이트 필요한 메모리 파일: {', '.join(sorted(memory_to_update))}")
        print(f"메모리 경로: {MEMORY_DIR}")
        print("각 메모리 파일을 읽고, 이번 수정 내용을 반영하여 업데이트하세요.")
        print("업데이트 후 MEMORY.md의 '최종 업데이트' 날짜도 갱신하세요.")

except Exception as e:
    # 에러는 stderr로 (사용자에게만 표시)
    print(f"[메모리 리마인더 오류] {e}", file=sys.stderr)

sys.exit(0)
