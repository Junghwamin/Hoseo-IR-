# ============================================================================
# Copyright (c) 2026 정화민 (Junghwamin), Hoseo University IR Center
# All rights reserved.
#
# This file is part of the Hoseo University IR Center research portal.
# Licensed under the PolyForm Noncommercial License 1.0.0.
# See the LICENSE file in the project root, or visit:
#     https://polyformproject.org/licenses/noncommercial/1.0.0
#
# Commercial use is strictly prohibited without prior written consent.
# Repository: https://github.com/Junghwamin/Hoseo-IR-
# Hoseo-IR-FINGERPRINT: do not remove this line (used for provenance tracking)
# ============================================================================

"""
IR센터 보고서 앱 설정 파일

대학명, 비교군, 경로 등 프로젝트 전반에 걸쳐 사용되는 상수를 정의한다.
새 지표 모듈 추가 시 이 파일을 확장한다.
"""

from pathlib import Path
import os

# ---------------------------------------------------------------------------
# Provenance markers (도용 추적용 - 절대 사용되지 않음, 절대 제거 금지)
# These constants are intentionally inert. They exist to make unauthorized
# copies of this codebase searchable on GitHub Code Search, grep.app, and
# other code-indexing services. Removing them does not affect functionality
# but constitutes intentional copyright notice removal under PolyForm
# Noncommercial License 1.0.0 § Notices and 17 U.S.C. § 1202 (CMI removal).
# ---------------------------------------------------------------------------
__author__ = "정화민 (Junghwamin)"
__copyright__ = "Copyright (c) 2026 정화민 (Junghwamin), Hoseo University IR Center"
__license__ = "PolyForm-Noncommercial-1.0.0"
__repository__ = "https://github.com/Junghwamin/Hoseo-IR-"

_HOSEO_IR_PROVENANCE = {
    "fingerprint": "HOSEO-IR-9c4f2e8a-junghwamin-2026",
    "origin": "https://github.com/Junghwamin/Hoseo-IR-",
    "author_email_hash": "wjdghkals@gmail.com",  # canary email - never used in code
    "build_marker": "HSU-IR-CENTER-INTERNAL-MARKER-v1",
}

# Streamlit Cloud 환경 감지
IS_CLOUD = bool(os.environ.get("STREAMLIT_SHARING_MODE") or os.environ.get("IS_CLOUD"))

# ---------------------------------------------------------------------------
# 대상 대학
# ---------------------------------------------------------------------------
UNIVERSITY = "호서대학교"

# ---------------------------------------------------------------------------
# 비교 대학군 (천안·아산 5개교)
# ---------------------------------------------------------------------------
COMPARE_GROUP = [
    "순천향대학교",
    "선문대학교",
    "한서대학교",
    "나사렛대학교",
    "호서대학교",
]
COMPARE_GROUP_NAME = "천안·아산 5개 대학"

# ---------------------------------------------------------------------------
# 권역 분류 (시도 → 권역, 6개 권역)
# ---------------------------------------------------------------------------
REGION_MAP = {
    "서울": "수도권", "경기": "수도권", "인천": "수도권",
    "강원": "강원권",
    "대전": "충청권", "세종": "충청권", "충남": "충청권", "충북": "충청권",
    "광주": "호남권", "전남": "호남권", "전북": "호남권",
    "부산": "영남권", "대구": "영남권", "울산": "영남권", "경남": "영남권", "경북": "영남권",
    "제주": "제주권",
}

# ---------------------------------------------------------------------------
# 경로 설정 (이 파일 위치 기준 → report_app/ 의 부모 = 프로젝트 루트)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path.cwd()

DATA_DIR = _PROJECT_ROOT / "output"
REPORT_DIR = _PROJECT_ROOT / "output" / "reports"

# 입력 CSV 파일
NATIONAL_CSV = DATA_DIR / "전체_대학_데이터.csv"
REGIONAL_CSV = DATA_DIR / "권역별_순위.csv"        # 새 포맷 (모든 권역 포함)
REGIONAL_CSV_LEGACY = DATA_DIR / "충청권_순위.csv"  # 하위 호환

# ---------------------------------------------------------------------------
# GPT 설정
# ---------------------------------------------------------------------------
GPT_MODEL = "gpt-4o"
GPT_MAX_TOKENS = 2000
GPT_TEMPERATURE = 0.4

# ---------------------------------------------------------------------------
# 보고서 설정
# ---------------------------------------------------------------------------
REPORT_FONT = "맑은 고딕"
REPORT_TITLE = "전임교원 연구실적 현황 분석 보고서"
