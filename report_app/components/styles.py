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

# report_app/components/styles.py
"""
Amplitude 디자인 시스템 기반 전체 CSS 제공 모듈.

Streamlit 앱에서 다음과 같이 사용한다:
    from report_app.components.styles import get_css
    st.markdown(get_css(), unsafe_allow_html=True)
"""


def get_css() -> str:
    """전체 CSS를 <style> 태그로 감싸서 반환한다.

    Amplitude 디자인 시스템을 반영한 CSS를 포함한다:
    - Noto Sans KR / Noto Serif KR 폰트
    - Tailwind Zinc 기반 CSS 토큰 (:root)
    - 툴바, 사이드바, 버튼, 카드, 차트, GPT 섹션 등 전체 컴포넌트 스타일
    - fadeInUp / shimmer 애니메이션

    Returns:
        <style>...</style> 형태의 HTML 문자열
    """
    return """
<style>

/* =====================================================
   0. 폰트 로딩
   ===================================================== */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&family=Noto+Serif+KR:wght@400;600&display=swap');


/* =====================================================
   1. CSS 토큰 (:root) — Tailwind Zinc + 시맨틱 컬러
   ===================================================== */
:root {
    /* Zinc 스케일 */
    --zinc-50:  #fafafa;
    --zinc-100: #f4f4f5;
    --zinc-200: #e4e4e7;
    --zinc-300: #d4d4d8;
    --zinc-400: #a1a1aa;
    --zinc-500: #71717a;
    --zinc-600: #52525b;
    --zinc-700: #3f3f46;
    --zinc-800: #27272a;
    --zinc-900: #18181b;
    --zinc-950: #09090b;

    /* Amplitude 블루 프라이머리 */
    --amp-blue: #1a56db;
    --amp-blue-light: #e8f0fe;
    --amp-blue-hover: #1e40af;
    --amp-blue-50: #eff6ff;
    --amp-blue-100: #dbeafe;
    --amp-blue-600: #2563eb;
    --amp-blue-700: #1d4ed8;

    /* 시맨틱 컬러 */
    --green-600: #16a34a;
    --green-50:  #f0fdf4;
    --green-200: #bbf7d0;
    --red-600:   #dc2626;
    --red-50:    #fef2f2;
    --amber-600: #d97706;
    --amber-50:  #fffbeb;

    /* 카드 공통 토큰 */
    --card-radius:  8px;
    --card-border:  1px solid var(--zinc-200);
    --card-padding: 20px;

    /* 트랜지션 */
    --transition: all 0.15s ease;
}


/* =====================================================
   2. 전체 배경 및 기본 폰트
   ===================================================== */
.stApp {
    background: var(--zinc-50) !important;
    font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont,
                 'Segoe UI', sans-serif !important;
    color: var(--zinc-900) !important;
}


/* =====================================================
   3. Streamlit 상단 헤더 / 데코레이션 숨김
   ===================================================== */
[data-testid="stHeader"],
[data-testid="stDecoration"] {
    display: none !important;
}


/* =====================================================
   4. 메인 컨테이너
   ===================================================== */
.main .block-container {
    max-width: 1280px !important;
    padding-top: 0.5rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
}


/* =====================================================
   5. 슬림 툴바 (.ir-toolbar)
   — 앱 최상단 고정 헤더 영역
   ===================================================== */
.ir-toolbar {
    height: 52px;
    background: #ffffff;
    border-bottom: 1px solid var(--zinc-200);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.5rem;
    position: sticky;
    top: 0;
    z-index: 100;
}


/* =====================================================
   6. 사이드바 — Amplitude 좌측 네비게이션
   ===================================================== */

/* 사이드바 컨테이너 */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid var(--zinc-200) !important;
}

[data-testid="stSidebar"] > div:first-child {
    background: #ffffff !important;
}

/* 섹션 레이블 (UPPERCASE 카테고리 구분자) */
.ir-nav-label {
    font-size: 0.6875rem;
    font-weight: 600;
    color: var(--zinc-500);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 0.5rem 1rem;
    margin-top: 0.75rem;
}

/* 네비 항목 기본 */
.ir-nav-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    color: var(--zinc-600);
    border-radius: 6px;
    margin: 2px 0.5rem;
    cursor: pointer;
    transition: var(--transition);
    border-left: 3px solid transparent;
}

/* 활성 항목 */
.ir-nav-item.active {
    background: var(--amp-blue-light);
    color: var(--amp-blue);
    font-weight: 600;
    border-left: 3px solid var(--amp-blue);
    padding-left: calc(1rem - 3px);
}

/* hover */
.ir-nav-item:hover {
    background: var(--zinc-50);
}

/* 완료된 항목 */
.ir-nav-item.done {
    color: var(--zinc-500);
}

/* 비활성화 항목 */
.ir-nav-item.disabled {
    opacity: 0.4;
    pointer-events: none;
}

/* Coming Soon 뱃지 */
.ir-badge-coming {
    display: inline-block;
    background: var(--zinc-100);
    color: var(--zinc-500);
    font-size: 0.6875rem;
    padding: 1px 6px;
    border-radius: 3px;
    margin-left: auto;
}


/* =====================================================
   7. 버튼
   ===================================================== */

/* Primary 버튼 */
button[kind="primary"],
.stButton > button[data-baseweb="button"]:not([kind="secondary"]) {
    background: var(--amp-blue) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.5rem 1.25rem !important;
    transition: var(--transition) !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}

button[kind="primary"]:hover,
.stButton > button[data-baseweb="button"]:not([kind="secondary"]):hover {
    background: var(--amp-blue-hover) !important;
}

/* Secondary 버튼 */
button[kind="secondary"],
.stButton > button[kind="secondary"] {
    background: #ffffff !important;
    color: var(--zinc-700) !important;
    border: 1px solid var(--zinc-200) !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.5rem 1.25rem !important;
    transition: var(--transition) !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}

button[kind="secondary"]:hover,
.stButton > button[kind="secondary"]:hover {
    border-color: var(--zinc-400) !important;
}

/* 클릭 피드백 */
.stButton > button:active {
    transform: scale(0.98) !important;
}


/* =====================================================
   8. 메트릭 카드 (.ir-metric-card)
   ===================================================== */
.ir-metric-card {
    background: #ffffff;
    border: 1px solid var(--zinc-200);
    border-radius: var(--card-radius);
    padding: var(--card-padding);
    transition: var(--transition);
}

.ir-metric-card:hover {
    border-color: var(--zinc-300);
}

/* 레이블 (UPPERCASE 소제목) */
.ir-metric-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--zinc-500);
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* 메인 수치 */
.ir-metric-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--zinc-950);
    font-variant-numeric: tabular-nums;
    margin: 0.25rem 0;
    line-height: 1.2;
}

/* 증감 뱃지 */
.ir-metric-delta {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.8125rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
}

.ir-metric-delta.up {
    background: var(--green-50);
    color: var(--green-600);
}

.ir-metric-delta.down {
    background: var(--red-50);
    color: var(--red-600);
}

.ir-metric-delta.neutral {
    background: var(--zinc-100);
    color: var(--zinc-500);
}


/* =====================================================
   9. 차트 카드 (.ir-chart-card)
   ===================================================== */
.ir-chart-card {
    background: #ffffff;
    border: 1px solid var(--zinc-200);
    border-radius: var(--card-radius);
    overflow: hidden;
}

.ir-chart-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 16px 20px;
    border-bottom: 1px solid var(--zinc-100);
}

.ir-chart-title {
    font-size: 0.9375rem;
    font-weight: 700;
    color: var(--zinc-900);
}

.ir-chart-subtitle {
    font-size: 0.8125rem;
    color: var(--zinc-500);
    margin-top: 2px;
}

.ir-chart-actions {
    display: flex;
    gap: 8px;
}

.ir-chart-body {
    padding: 16px 20px;
}

.ir-chart-breakdown {
    border-top: 1px solid var(--zinc-100);
    padding: 12px 20px;
    font-size: 0.8125rem;
    color: var(--zinc-600);
}


/* =====================================================
   10. GPT 섹션 카드 (.ir-gpt-card)
   ===================================================== */
.ir-gpt-card {
    background: #ffffff;
    border: 1px solid var(--zinc-200);
    border-radius: var(--card-radius);
    margin-bottom: 12px;
    overflow: hidden;
}

.ir-gpt-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 20px;
    cursor: pointer;
}

.ir-gpt-title {
    font-size: 0.9375rem;
    font-weight: 700;
    color: var(--zinc-900);
}

.ir-gpt-hint {
    font-size: 0.8125rem;
    color: var(--zinc-500);
    margin-top: 2px;
}

/* 완료 상태 표시 점 */
.ir-gpt-status {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

.ir-gpt-status.done {
    background: var(--green-600);
}

.ir-gpt-status.empty {
    background: var(--zinc-300);
}

/* 카드 하단 메타 정보 */
.ir-gpt-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 20px;
    border-top: 1px solid var(--zinc-100);
    font-size: 0.8125rem;
    color: var(--zinc-500);
}


/* =====================================================
   11. 텍스트 에어리어 — 세리프 폰트 (보고서 서술)
   ===================================================== */
.stTextArea textarea {
    font-family: 'Noto Serif KR', Georgia, 'Times New Roman', serif !important;
    line-height: 1.875 !important;
    border: 1px solid var(--zinc-200) !important;
    border-radius: 6px !important;
    color: var(--zinc-900) !important;
    transition: var(--transition) !important;
}

.stTextArea textarea:focus {
    border-color: var(--amp-blue) !important;
    box-shadow: 0 0 0 3px rgba(26, 86, 219, 0.12) !important;
    outline: none !important;
}


/* =====================================================
   12. 데이터프레임 (테이블)
   ===================================================== */

/* 헤더 행 */
[data-testid="stDataFrame"] th,
.dataframe thead th {
    background: var(--zinc-100) !important;
    text-transform: uppercase !important;
    font-size: 0.8125rem !important;
    font-weight: 600 !important;
    color: var(--zinc-600) !important;
    letter-spacing: 0.03em !important;
    border-bottom: 1px solid var(--zinc-200) !important;
}

/* 데이터 행 */
[data-testid="stDataFrame"] td,
.dataframe tbody td {
    font-size: 0.875rem !important;
    color: var(--zinc-800) !important;
    border-bottom: 1px solid var(--zinc-100) !important;
}

/* 행 hover */
[data-testid="stDataFrame"] tr:hover td,
.dataframe tbody tr:hover td {
    background: var(--zinc-50) !important;
}


/* =====================================================
   13. 탭
   ===================================================== */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 1px solid var(--zinc-200) !important;
    gap: 0 !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab"] {
    color: var(--zinc-500) !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    padding: 0.625rem 1rem !important;
    transition: var(--transition) !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--zinc-700) !important;
}

.stTabs [aria-selected="true"] {
    color: var(--amp-blue) !important;
    border-bottom: 2px solid var(--amp-blue) !important;
    font-weight: 600 !important;
    background: transparent !important;
}

/* 탭 패널 배경 */
[data-baseweb="tab-panel"] {
    background: transparent !important;
    padding-top: 1rem !important;
}


/* =====================================================
   14. Selectbox
   ===================================================== */
[data-testid="stSelectbox"] > div > div {
    border: 1px solid var(--zinc-200) !important;
    border-radius: 6px !important;
    background: #ffffff !important;
    font-size: 0.875rem !important;
    color: var(--zinc-800) !important;
    transition: var(--transition) !important;
}

[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: var(--amp-blue) !important;
    box-shadow: 0 0 0 3px rgba(26, 86, 219, 0.12) !important;
}


/* =====================================================
   15. File Uploader
   ===================================================== */
[data-testid="stFileUploader"] {
    border: 1px dashed var(--zinc-300) !important;
    border-radius: var(--card-radius) !important;
    background: var(--zinc-50) !important;
    transition: var(--transition) !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: var(--zinc-500) !important;
    background: #ffffff !important;
}

[data-testid="stFileUploader"] label {
    font-size: 0.875rem !important;
    color: var(--zinc-600) !important;
}


/* =====================================================
   16. 알림 박스 (success / warning / error / info)
   ===================================================== */
[data-testid="stAlert"] {
    border-radius: 6px !important;
    border-left-width: 3px !important;
}

/* success */
[data-testid="stAlert"][data-baseweb="notification"][kind="positive"] {
    border-left-color: var(--green-600) !important;
    background: var(--green-50) !important;
}

/* warning */
[data-testid="stAlert"][data-baseweb="notification"][kind="warning"] {
    border-left-color: var(--amber-600) !important;
    background: var(--amber-50) !important;
}

/* error */
[data-testid="stAlert"][data-baseweb="notification"][kind="negative"] {
    border-left-color: var(--red-600) !important;
    background: var(--red-50) !important;
}

/* info */
[data-testid="stAlert"][data-baseweb="notification"][kind="info"] {
    border-left-color: var(--zinc-400) !important;
    background: var(--zinc-50) !important;
}


/* =====================================================
   17. 빈 상태 (.ir-empty-state)
   ===================================================== */
.ir-empty-state {
    text-align: center;
    padding: 3rem 2rem;
}

.ir-empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.3;
    display: block;
}

.ir-empty-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--zinc-700);
}

.ir-empty-desc {
    font-size: 0.875rem;
    color: var(--zinc-500);
    margin-top: 0.5rem;
    line-height: 1.6;
}


/* =====================================================
   18. 완료 카드 (.ir-success-card)
   ===================================================== */
.ir-success-card {
    background: #ffffff;
    border: 1px solid var(--green-200);
    border-radius: var(--card-radius);
    padding: 2rem;
    text-align: center;
}

.ir-success-icon {
    font-size: 2.5rem;
    margin-bottom: 0.75rem;
    display: block;
}

.ir-success-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--zinc-900);
}


/* =====================================================
   19. 온보딩 카드 (.ir-onboard-card)
   ===================================================== */
.ir-onboard-card {
    background: #ffffff;
    border: 1px solid var(--zinc-200);
    border-radius: var(--card-radius);
    padding: 1.5rem;
    text-align: center;
    cursor: pointer;
    transition: var(--transition);
}

.ir-onboard-card:hover {
    border-color: var(--zinc-400);
}

.ir-onboard-card.active {
    border-color: var(--amp-blue);
    border-width: 2px;
}

.ir-onboard-card.disabled {
    opacity: 0.5;
    pointer-events: none;
}


/* =====================================================
   20. skeleton 로딩 (.ir-skeleton)
   ===================================================== */
@keyframes shimmer {
    0%   { background-position: -200px 0; }
    100% { background-position: calc(200px + 100%) 0; }
}

.ir-skeleton {
    background: linear-gradient(
        90deg,
        var(--zinc-100) 25%,
        var(--zinc-200) 50%,
        var(--zinc-100) 75%
    );
    background-size: 200px 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
    height: 1rem;
}

/* 사이즈 변형 */
.ir-skeleton.lg  { height: 1.5rem; }
.ir-skeleton.xl  { height: 2rem; border-radius: 6px; }
.ir-skeleton.card {
    height: 120px;
    border-radius: var(--card-radius);
}


/* =====================================================
   21. fadeInUp 애니메이션
   ===================================================== */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.ir-fade-in {
    animation: fadeInUp 0.25s ease both;
}


/* =====================================================
   22. 푸터 (.ir-footer)
   ===================================================== */
.ir-footer {
    text-align: center;
    color: var(--zinc-400);
    font-size: 0.8125rem;
    padding: 1.25rem 0 0.5rem;
    border-top: 1px solid var(--zinc-200);
    margin-top: 1rem;
}


/* =====================================================
   23. Home 모듈 카드 (.ir-module-card)
   ===================================================== */
.ir-module-card {
    background: #ffffff;
    border: 1px solid var(--zinc-200);
    border-radius: var(--card-radius);
    padding: 1.5rem;
    transition: var(--transition);
}

.ir-module-card:hover {
    border-color: var(--amp-blue);
    transform: translateY(-2px);
}

.ir-module-icon {
    font-size: 2rem;
    margin-bottom: 0.75rem;
    display: block;
}

.ir-module-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--zinc-900);
}

.ir-module-desc {
    font-size: 0.8125rem;
    color: var(--zinc-500);
    margin-top: 0.5rem;
    line-height: 1.5;
}


/* =====================================================
   24. Streamlit 기본 위젯 최소 오버라이드
   — stMetric, stExpander는 커스텀 HTML로 대체 예정이므로 최소화
   ===================================================== */

/* stMetric 기본 숨김 방지 (커스텀 대체 전까지 기본 유지) */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid var(--zinc-200);
    border-radius: var(--card-radius);
    padding: 1rem;
}

/* stExpander 테두리 통일 */
[data-testid="stExpander"] {
    border: 1px solid var(--zinc-200) !important;
    border-radius: var(--card-radius) !important;
    overflow: hidden;
}

[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: var(--zinc-800) !important;
    font-size: 0.9375rem !important;
}


/* =====================================================
   25. Amplitude 뱃지 (.ir-badge)
   ===================================================== */
.ir-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}

.ir-badge-blue {
    background: var(--amp-blue-light);
    color: var(--amp-blue);
}

.ir-badge-green {
    background: #d1fae5;
    color: #065f46;
}

.ir-badge-amber {
    background: #fef3c7;
    color: #92400e;
}

.ir-badge-red {
    background: #fee2e2;
    color: #991b1b;
}

</style>
"""
