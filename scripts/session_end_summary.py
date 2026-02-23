#!/usr/bin/env python3
"""
Stop 훅: 세션 종료 시 변경사항 요약 + 체크리스트 출력

Claude 응답이 끝날 때마다 실행됩니다.
이번 세션에서 변경된 파일 목록과 다음 할 일을 보여줍니다.
"""

import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/정화민/Desktop/IR센터 MCP")
CHANGE_LOG   = PROJECT_ROOT / "change_log.txt"
BACKUP_DIR   = PROJECT_ROOT / "backups"

try:
    # 오늘 날짜 기준 변경된 파일 목록
    today = datetime.now().strftime("%Y-%m-%d")

    today_changes = []
    if CHANGE_LOG.exists():
        lines = CHANGE_LOG.read_text(encoding="utf-8").splitlines()
        today_changes = [l for l in lines if l.startswith(today)]

    # 오늘 생성된 백업 수
    backup_count = 0
    if BACKUP_DIR.exists():
        today_str = datetime.now().strftime("%Y%m%d")
        backup_count = len(list(BACKUP_DIR.glob(f"{today_str}_*.py")))

    if today_changes:
        print("\n" + "─" * 50, file=sys.stderr)
        print(f"📋 오늘 변경된 파일 ({len(today_changes)}건):", file=sys.stderr)
        seen = set()
        for line in today_changes[-10:]:  # 최근 10건
            parts = line.split(" | ")
            if len(parts) >= 3:
                fname = parts[2].strip()
                if fname not in seen:
                    print(f"   • {fname}", file=sys.stderr)
                    seen.add(fname)
        print(f"💾 오늘 백업 생성: {backup_count}개  →  backups/ 폴더", file=sys.stderr)
        print("─" * 50, file=sys.stderr)
        print("✅ 체크리스트:", file=sys.stderr)
        print("   □ CLAUDE.md 작업 로그 최신 상태인지 확인", file=sys.stderr)
        print("   □ 앱 실행 테스트: streamlit run report_app/app.py", file=sys.stderr)
        print("─" * 50 + "\n", file=sys.stderr)

except Exception as e:
    print(f"[세션 요약 오류] {e}", file=sys.stderr)

sys.exit(0)
