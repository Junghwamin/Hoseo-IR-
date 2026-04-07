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
PreToolUse 훅: .py 파일 편집 직전 자동 백업

Claude가 Write/Edit 도구로 .py 파일을 수정하기 전에 실행됩니다.
backups/ 폴더에 타임스탬프가 붙은 백업 파일을 생성합니다.

[수정 이력]
- v1.1: stdin을 bytes로 읽어 UTF-8 명시 디코딩 (Windows 한글 경로 깨짐 수정)
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR   = PROJECT_ROOT / "backups"
BACKUP_EXTS  = {".py"}

try:
    # ── 핵심 수정: sys.stdin.buffer 로 raw bytes 읽기 후 UTF-8 디코딩
    #    (sys.stdin 직접 사용 시 Windows CP949 콘솔 인코딩 충돌로 한글 경로 깨짐)
    raw  = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    data = json.loads(raw)

    tool_input = data.get("tool_input", {})
    file_path  = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    src = Path(file_path)

    if src.suffix not in BACKUP_EXTS or not src.exists():
        sys.exit(0)

    BACKUP_DIR.mkdir(exist_ok=True)

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{timestamp}_{src.name}"
    backup_path = BACKUP_DIR / backup_name

    shutil.copy2(src, backup_path)
    print(f"[백업 완료] {src.name} → backups/{backup_name}", file=sys.stderr)

except Exception as e:
    print(f"[백업 오류] {type(e).__name__}: {e}", file=sys.stderr)

sys.exit(0)
