"""
호서대학교 IR센터 - 연구실적 분석 포털 v3.0

5단계 Step-by-Step 워크플로우:
  1단계: 데이터 설정   (파일 업로드 or 기존 파일 사용)
  2단계: 통계 확인     (수치 검토 및 연도 선택)
  3단계: 그래프 검토   (차트 5종 확인)
  4단계: GPT 서술 편집 (섹션별 생성 + 직접 편집)
  5단계: 보고서 생성   (Word 파일 다운로드)

실행 방법:
    streamlit run report_app/app.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io as _io
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv, set_key
from openai import OpenAI

from report_app import chart_generator as cg
from report_app import data_loader as dl
from report_app import gpt_reporter as gpt
from report_app import report_builder as rb
from report_app.config import NATIONAL_CSV, REGIONAL_CSV, REPORT_DIR, UNIVERSITY

# 전처리 스크립트 동적 임포트
# 번들 내부(macOS) 또는 CWD(개발자/Windows) 양쪽 지원
_PREPROCESS_PATH = Path(__file__).parent.parent / "전임교원_연구실적_전처리.py"
if not _PREPROCESS_PATH.exists():
    _PREPROCESS_PATH = Path.cwd() / "전임교원_연구실적_전처리.py"

def _load_preprocessor():
    spec = importlib.util.spec_from_file_location("preprocessor", str(_PREPROCESS_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# ---------------------------------------------------------------------------
# 경로 상수
# ---------------------------------------------------------------------------
_ENV_PATH = Path.cwd() / ".env"

# ---------------------------------------------------------------------------
# .env 로드
# ---------------------------------------------------------------------------
load_dotenv(_ENV_PATH)

# ---------------------------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=f"{UNIVERSITY} 연구실적 분석 포털",
    page_icon="📊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# ■ GLOBAL CSS — 디자인 시스템
# ---------------------------------------------------------------------------
_TODAY = datetime.now().strftime("%Y년 %m월 %d일")

st.markdown("""
<style>
/* ── 디자인 토큰 ─────────────────────────────────────────── */
:root {
  --blue-900: #0F2D5C;
  --blue-800: #1B4F8A;
  --blue-700: #1D5EA8;
  --blue-500: #2563EB;
  --blue-100: #DBEAFE;
  --blue-50:  #EFF6FF;
  --amber-500: #F59E0B;
  --amber-100: #FEF3C7;
  --green-500: #10B981;
  --green-100: #D1FAE5;
  --red-500:   #EF4444;
  --gray-900:  #111827;
  --gray-700:  #374151;
  --gray-500:  #6B7280;
  --gray-300:  #D1D5DB;
  --gray-100:  #F3F4F6;
  --gray-50:   #F9FAFB;
  --white:     #FFFFFF;
  --shadow-sm: 0 1px 3px rgba(0,0,0,.10), 0 1px 2px rgba(0,0,0,.06);
  --shadow-md: 0 4px 6px rgba(0,0,0,.07), 0 2px 4px rgba(0,0,0,.06);
  --shadow-lg: 0 10px 25px rgba(0,0,0,.10), 0 4px 10px rgba(0,0,0,.05);
  --radius:    10px;
  --radius-lg: 16px;
}

/* ── 전체 배경 ────────────────────────────────────────────── */
.stApp {
  background: #F0F4F9;
  font-family: 'Malgun Gothic', '맑은 고딕', -apple-system, sans-serif !important;
}

/* ── 메인 컨테이너 패딩 ───────────────────────────────────── */
.main .block-container {
  padding-top: 1.2rem !important;
  padding-bottom: 2.5rem !important;
  max-width: 1280px !important;
}

/* ── Streamlit 상단 헤더 숨김 ─────────────────────────────── */
[data-testid="stHeader"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── 사이드바 ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--blue-900) !important;
  border-right: none !important;
}
[data-testid="stSidebar"] * {
  color: #E0E7EF !important;
}
[data-testid="stSidebar"] .stTextInput input {
  background: rgba(255,255,255,0.12) !important;
  border: 1px solid rgba(255,255,255,0.25) !important;
  color: white !important;
  border-radius: 8px !important;
}
[data-testid="stSidebar"] .stTextInput input::placeholder {
  color: rgba(255,255,255,0.45) !important;
}
[data-testid="stSidebar"] hr {
  border-color: rgba(255,255,255,0.15) !important;
}
[data-testid="stSidebar"] .stButton > button {
  background: rgba(255,255,255,0.12) !important;
  border: 1px solid rgba(255,255,255,0.25) !important;
  color: white !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  transition: all .2s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(255,255,255,0.22) !important;
  border-color: rgba(255,255,255,0.45) !important;
}
/* 사이드바 성공/경고 메시지 */
[data-testid="stSidebar"] .stSuccess {
  background: rgba(16,185,129,0.2) !important;
  color: #6EE7B7 !important;
  border: 1px solid rgba(16,185,129,0.35) !important;
}
[data-testid="stSidebar"] .stWarning {
  background: rgba(245,158,11,0.2) !important;
  color: #FCD34D !important;
  border: 1px solid rgba(245,158,11,0.35) !important;
}

/* ── 버튼 스타일 ───────────────────────────────────────────── */
.stButton > button {
  border-radius: 8px !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  padding: 0.45rem 1.2rem !important;
  transition: all .2s ease !important;
  border: 1px solid var(--gray-300) !important;
}
.stButton > button[kind="primary"] {
  background: var(--blue-800) !important;
  border-color: var(--blue-800) !important;
  color: white !important;
  box-shadow: var(--shadow-sm) !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--blue-700) !important;
  box-shadow: var(--shadow-md) !important;
  transform: translateY(-1px) !important;
}
.stButton > button:not([kind="primary"]):hover {
  border-color: var(--blue-800) !important;
  color: var(--blue-800) !important;
  background: var(--blue-50) !important;
}

/* ── 탭 스타일 ─────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: white !important;
  border-radius: var(--radius) var(--radius) 0 0 !important;
  padding: 0 1rem !important;
  border-bottom: 2px solid var(--gray-100) !important;
  gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 0 !important;
  padding: 0.7rem 1.1rem !important;
  font-size: 0.88rem !important;
  font-weight: 500 !important;
  color: var(--gray-500) !important;
  border-bottom: 2px solid transparent !important;
  margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] {
  color: var(--blue-800) !important;
  border-bottom: 2px solid var(--blue-800) !important;
  background: transparent !important;
  font-weight: 700 !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background: white !important;
  border-radius: 0 0 var(--radius) var(--radius) !important;
  padding: 1.5rem !important;
  box-shadow: var(--shadow-sm) !important;
}

/* ── Expander ─────────────────────────────────────────────── */
.stExpander {
  border: 1px solid var(--gray-200) !important;
  border-radius: var(--radius) !important;
  background: white !important;
  box-shadow: var(--shadow-sm) !important;
  margin-bottom: 0.8rem !important;
}
.stExpander summary {
  font-weight: 600 !important;
  color: var(--gray-700) !important;
}

/* ── 텍스트 에어리어 ───────────────────────────────────────── */
.stTextArea textarea {
  border: 1.5px solid var(--gray-300) !important;
  border-radius: 8px !important;
  font-family: 'Malgun Gothic', '맑은 고딕', sans-serif !important;
  font-size: 0.9rem !important;
  line-height: 1.7 !important;
  transition: border-color .2s !important;
}
.stTextArea textarea:focus {
  border-color: var(--blue-500) !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
}

/* ── 메트릭 카드 ───────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: white !important;
  border-radius: var(--radius) !important;
  padding: 1rem 1.2rem !important;
  box-shadow: var(--shadow-sm) !important;
  border: 1px solid var(--gray-100) !important;
  transition: box-shadow .2s !important;
}
[data-testid="stMetric"]:hover {
  box-shadow: var(--shadow-md) !important;
}
[data-testid="stMetricLabel"] {
  font-size: 0.78rem !important;
  font-weight: 600 !important;
  color: var(--gray-500) !important;
  letter-spacing: .03em !important;
  text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
  font-size: 1.7rem !important;
  font-weight: 700 !important;
  color: var(--blue-800) !important;
}

/* ── 데이터프레임 헤더 ─────────────────────────────────────── */
[data-testid="stDataFrame"] th {
  background: var(--blue-800) !important;
  color: white !important;
  font-weight: 600 !important;
  font-size: 0.82rem !important;
}
[data-testid="stDataFrame"] tr:hover td {
  background: var(--blue-50) !important;
}

/* ── 알림 박스 ─────────────────────────────────────────────── */
.stSuccess {
  border-radius: 8px !important;
  border-left: 4px solid var(--green-500) !important;
}
.stWarning {
  border-radius: 8px !important;
  border-left: 4px solid var(--amber-500) !important;
}
.stError {
  border-radius: 8px !important;
  border-left: 4px solid var(--red-500) !important;
}
.stInfo {
  border-radius: 8px !important;
  border-left: 4px solid var(--blue-500) !important;
}

/* ── Selectbox ─────────────────────────────────────────────── */
.stSelectbox [data-baseweb="select"] {
  border-radius: 8px !important;
}

/* ── File uploader ─────────────────────────────────────────── */
[data-testid="stFileUploader"] {
  border-radius: 8px !important;
  border: 2px dashed var(--gray-300) !important;
  background: var(--gray-50) !important;
  transition: all .2s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--blue-500) !important;
  background: var(--blue-50) !important;
}

/* ── 구분선 ────────────────────────────────────────────────── */
hr {
  border-color: var(--gray-200) !important;
  margin: 1.2rem 0 !important;
}

/* ── 커스텀 헬퍼 클래스 ────────────────────────────────────── */

/* 카드 컨테이너 */
.ir-card {
  background: white;
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--gray-100);
  margin-bottom: 1rem;
}

/* 섹션 타이틀 */
.ir-section-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--gray-900);
  padding: 0.7rem 1rem;
  background: white;
  border-left: 4px solid var(--blue-800);
  border-radius: 0 var(--radius) var(--radius) 0;
  box-shadow: var(--shadow-sm);
  margin: 1.2rem 0 0.8rem 0;
}

/* 페이지 헤더 배너 */
.ir-header {
  background: linear-gradient(135deg, var(--blue-900) 0%, var(--blue-700) 60%, #1E40AF 100%);
  border-radius: var(--radius-lg);
  padding: 1.6rem 2rem;
  margin-bottom: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
}
.ir-header::before {
  content: '';
  position: absolute;
  top: -40px; right: -40px;
  width: 180px; height: 180px;
  background: rgba(255,255,255,0.06);
  border-radius: 50%;
}
.ir-header::after {
  content: '';
  position: absolute;
  bottom: -60px; left: 40%;
  width: 240px; height: 240px;
  background: rgba(255,255,255,0.04);
  border-radius: 50%;
}
.ir-header-left h1 {
  color: white !important;
  font-size: 1.45rem !important;
  font-weight: 800 !important;
  margin: 0 0 0.25rem 0 !important;
  letter-spacing: -0.02em !important;
}
.ir-header-left p {
  color: rgba(255,255,255,0.72) !important;
  font-size: 0.85rem !important;
  margin: 0 !important;
}
.ir-header-right {
  text-align: right;
  color: rgba(255,255,255,0.7);
  font-size: 0.82rem;
  line-height: 1.6;
}
.ir-header-badge {
  display: inline-block;
  background: rgba(245,158,11,0.85);
  color: white;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.18rem 0.6rem;
  border-radius: 20px;
  letter-spacing: .04em;
  margin-bottom: 0.4rem;
}

/* 스텝 프로그레스 바 */
.ir-steps {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  background: white;
  border-radius: var(--radius-lg);
  padding: 1.2rem 1.5rem 1rem;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--gray-100);
  margin-bottom: 1.2rem;
  position: relative;
}
.ir-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
  z-index: 1;
}
.ir-step:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 20px;
  left: calc(50% + 20px);
  right: calc(-50% + 20px);
  height: 2px;
  background: var(--gray-200);
  z-index: 0;
}
.ir-step.done:not(:last-child)::after  { background: var(--blue-800); }
.ir-step.active:not(:last-child)::after { background: var(--gray-200); }

.ir-step-circle {
  width: 40px; height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  border: 2px solid var(--gray-300);
  background: white;
  color: var(--gray-400);
  transition: all .3s;
  z-index: 2;
  position: relative;
}
.ir-step.done  .ir-step-circle {
  background: var(--blue-800);
  border-color: var(--blue-800);
  color: white;
}
.ir-step.active .ir-step-circle {
  background: white;
  border-color: var(--blue-800);
  border-width: 2.5px;
  color: var(--blue-800);
  box-shadow: 0 0 0 4px var(--blue-100);
}
.ir-step-label {
  font-size: 0.72rem;
  font-weight: 600;
  margin-top: 0.45rem;
  color: var(--gray-400);
  text-align: center;
  line-height: 1.3;
  max-width: 76px;
}
.ir-step.done  .ir-step-label { color: var(--blue-800); }
.ir-step.active .ir-step-label { color: var(--blue-800); }

/* GPT 섹션 헤더 (버튼 포함) */
.ir-gpt-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--blue-50);
  border: 1px solid var(--blue-100);
  border-radius: var(--radius);
  padding: 0.75rem 1.1rem;
  margin: 1.2rem 0 0.5rem 0;
}
.ir-gpt-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--blue-900);
}
.ir-gpt-hint {
  font-size: 0.78rem;
  color: var(--gray-500);
  margin-top: 0.15rem;
}

/* 완료 뱃지 */
.ir-badge-done {
  display: inline-block;
  background: var(--green-100);
  color: #065F46;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.18rem 0.7rem;
  border-radius: 20px;
  border: 1px solid #A7F3D0;
}
.ir-badge-empty {
  display: inline-block;
  background: var(--gray-100);
  color: var(--gray-500);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.18rem 0.7rem;
  border-radius: 20px;
  border: 1px solid var(--gray-200);
}

/* 푸터 */
.ir-footer {
  text-align: center;
  color: var(--gray-400);
  font-size: 0.78rem;
  padding: 1rem 0 0.5rem;
  border-top: 1px solid var(--gray-200);
  margin-top: 0.5rem;
}

/* 통계 요약 배너 */
.ir-stat-banner {
  background: linear-gradient(90deg, var(--blue-50) 0%, white 100%);
  border: 1px solid var(--blue-100);
  border-radius: var(--radius);
  padding: 0.9rem 1.2rem;
  margin-bottom: 1rem;
  font-size: 0.88rem;
  color: var(--gray-700);
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session State 초기화
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "step": 1,
    "national_df": None,
    "regional_df": None,
    "selected_year": None,
    "hoseo_trend": None,
    "averages": None,
    "rank_changes": None,
    "yoy_changes": None,
    "compare_data": None,
    "charts": {},
    "narrative_trend": "",
    "narrative_comparison": "",
    "narrative_regional": "",
    "narrative_yoy": "",
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "report_buf": None,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.api_key.startswith("sk-여기에"):
    st.session_state.api_key = ""


# ---------------------------------------------------------------------------
# 헬퍼: API Key 저장
# ---------------------------------------------------------------------------
def _save_api_key(key: str):
    _ENV_PATH.touch(exist_ok=True)
    set_key(str(_ENV_PATH), "OPENAI_API_KEY", key)
    st.session_state.api_key = key


# ---------------------------------------------------------------------------
# 헬퍼: 스텝 이동
# ---------------------------------------------------------------------------
def _go(step: int):
    # text_area 위젯 값을 비-위젯 키에 백업
    # (Streamlit은 미렌더 위젯의 session_state key를 다음 rerun에서 삭제하므로)
    _narrative_keys = ("narrative_trend", "narrative_comparison",
                       "narrative_regional", "narrative_yoy")
    for k in _narrative_keys:
        val = st.session_state.get(k, "")
        if val:
            st.session_state[f"_saved_{k}"] = val

    # 4단계로 돌아올 때 저장된 값 복원 (위젯이 다시 렌더되므로 key에 재설정)
    if step == 4:
        for k in _narrative_keys:
            saved = st.session_state.get(f"_saved_{k}", "")
            if saved:
                st.session_state[k] = saved

    st.session_state.step = step


# ---------------------------------------------------------------------------
# 헬퍼: 통계 계산
# ---------------------------------------------------------------------------
def _calc_stats():
    nat = st.session_state.national_df
    reg = st.session_state.regional_df
    year = st.session_state.selected_year
    st.session_state.hoseo_trend   = dl.get_hoseo_trend(nat, reg)
    st.session_state.averages      = dl.get_averages(nat, reg)
    st.session_state.rank_changes  = dl.get_rank_changes(nat, reg)
    st.session_state.yoy_changes   = dl.get_yoy_changes(reg, year)
    st.session_state.compare_data  = dl.get_compare_group_data(nat, reg, year)


# ===========================================================================
# ■ 사이드바
# ===========================================================================
with st.sidebar:
    st.markdown("""
    <div style="padding:1.2rem 0 1rem; text-align:center; border-bottom:1px solid rgba(255,255,255,0.12); margin-bottom:1rem;">
      <div style="font-size:1.4rem; margin-bottom:0.3rem;">📊</div>
      <div style="font-size:0.95rem; font-weight:700; color:white; letter-spacing:-0.01em;">IR 분석 포털</div>
      <div style="font-size:0.72rem; color:rgba(255,255,255,0.5); margin-top:0.2rem;">호서대학교 IR센터</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:0.78rem; font-weight:700; color:rgba(255,255,255,0.6); letter-spacing:.08em; text-transform:uppercase; margin-bottom:0.5rem;">🔑 OpenAI API Key</div>', unsafe_allow_html=True)

    key_input = st.text_input(
        "API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="sk-...",
        key="key_input_box",
        label_visibility="collapsed",
    )

    col_save, col_clear = st.columns(2)
    with col_save:
        if st.button("💾 저장", use_container_width=True, help=".env에 영구 저장"):
            if key_input.startswith("sk-") and len(key_input) > 20:
                _save_api_key(key_input)
                st.success("저장 완료!")
            else:
                st.error("올바른 키를 입력하세요.")
    with col_clear:
        if st.button("🗑 초기화", use_container_width=True):
            _save_api_key("sk-여기에_실제_API_키를_입력하세요")
            st.session_state.api_key = ""
            st.rerun()

    if st.session_state.api_key:
        st.success("✅ API Key 설정됨")
    else:
        st.warning("API Key 미설정")

    st.markdown('<hr style="margin:1.2rem 0;"/>', unsafe_allow_html=True)

    # --- 진행 단계 표시 ---
    st.markdown('<div style="font-size:0.78rem; font-weight:700; color:rgba(255,255,255,0.6); letter-spacing:.08em; text-transform:uppercase; margin-bottom:0.7rem;">📋 진행 단계</div>', unsafe_allow_html=True)

    step_icons = ["📂", "📋", "📈", "🤖", "📄"]
    step_names = ["데이터 설정", "통계 확인", "그래프 검토", "GPT 서술", "보고서 생성"]
    cur = st.session_state.step
    for i, (icon, name) in enumerate(zip(step_icons, step_names), start=1):
        if i < cur:
            style = "opacity:.65; color:rgba(255,255,255,0.8) !important;"
            prefix = "✓"
            weight = "500"
        elif i == cur:
            style = "background:rgba(255,255,255,0.12); border-radius:8px; padding:0.3rem 0.5rem;"
            prefix = "▶"
            weight = "700"
        else:
            style = "opacity:.4;"
            prefix = f"{i}."
            weight = "400"
        st.markdown(
            f'<div style="{style} font-size:0.88rem; font-weight:{weight}; color:rgba(255,255,255,0.9); padding:0.25rem 0.3rem; display:flex; align-items:center; gap:0.4rem;">'
            f'<span style="font-size:0.8rem; min-width:1.1rem;">{prefix}</span>'
            f'<span>{icon} {name}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr style="margin:1.2rem 0;"/>', unsafe_allow_html=True)

    if st.button("🔄 처음부터 다시", use_container_width=True):
        for k, v in _DEFAULTS.items():
            st.session_state[k] = v
        st.session_state.api_key = os.getenv("OPENAI_API_KEY", "")
        st.rerun()


# ===========================================================================
# ■ 페이지 헤더 배너
# ===========================================================================
st.markdown(f"""
<div class="ir-header">
  <div class="ir-header-left">
    <div class="ir-header-badge">IR Analytics Portal</div>
    <h1>📊 {UNIVERSITY} 연구실적 분석 포털</h1>
    <p>전임교원 SCI/SCOPUS 논문수 현황 · 충청권·전국 비교 분석 · 보고서 자동생성</p>
  </div>
  <div class="ir-header-right">
    <div style="font-size:0.78rem; color:rgba(255,255,255,0.55);">기준일</div>
    <div style="font-size:0.92rem; font-weight:600; color:white;">{_TODAY}</div>
    <div style="margin-top:0.6rem; font-size:0.78rem; color:rgba(255,255,255,0.5);">v3.0  ·  GPT-4o</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ===========================================================================
# ■ 스텝 프로그레스 인디케이터
# ===========================================================================
_step_labels = ["1. 데이터<br>설정", "2. 통계<br>확인", "3. 그래프<br>검토", "4. GPT<br>서술", "5. 보고서<br>생성"]
_step_icons_done = ["✓", "✓", "✓", "✓", "✓"]
cur = st.session_state.step

steps_html = '<div class="ir-steps">'
for i, lbl in enumerate(_step_labels, start=1):
    if i < cur:
        cls = "ir-step done"
        circle = "✓"
    elif i == cur:
        cls = "ir-step active"
        circle = str(i)
    else:
        cls = "ir-step"
        circle = str(i)
    steps_html += f"""
    <div class="{cls}">
      <div class="ir-step-circle">{circle}</div>
      <div class="ir-step-label">{lbl}</div>
    </div>"""
steps_html += "</div>"
st.markdown(steps_html, unsafe_allow_html=True)


# ===========================================================================
# ■ STEP 1: 전처리 + 데이터 설정
# ===========================================================================
if st.session_state.step == 1:
    st.markdown('<div class="ir-section-title">📂 1단계: 원시 데이터 전처리 / 데이터 설정</div>', unsafe_allow_html=True)
    st.markdown('<div class="ir-stat-banner">대학알리미 Raw Excel을 전처리하거나, 이미 전처리된 CSV 파일을 불러옵니다.</div>', unsafe_allow_html=True)

    _RAW_DIR = Path.cwd() / "Raw data"

    tab_preprocess, tab_csv_upload, tab_existing = st.tabs([
        "🔧 원시 데이터 전처리",
        "📂 전처리 결과 CSV 업로드",
        "📁 기존 output/ 폴더 사용",
    ])

    # ── 탭 1: 원시 데이터 전처리 ────────────────────────────────────────────
    with tab_preprocess:
        st.markdown("**대학알리미에서 받은 Raw Excel 파일을 업로드하면 자동으로 전처리합니다.**")
        st.caption("파일명에 연도가 포함되어야 합니다. 예: `2024년_전임교원연구실적.xlsx`")

        _RAW_DIR.mkdir(exist_ok=True)
        existing_raws = sorted(_RAW_DIR.glob("*.xlsx"))
        if existing_raws:
            with st.expander(f"📁 현재 Raw data/ 폴더 파일 ({len(existing_raws)}개)", expanded=False):
                for f in existing_raws:
                    st.markdown(f"- `{f.name}`")

        uploaded_raws = st.file_uploader(
            "새 Raw Excel 파일 업로드 (여러 개 선택 가능)",
            type=["xlsx"],
            accept_multiple_files=True,
            key="upload_raw_xlsx",
            help="대학알리미에서 다운로드한 연도별 xlsx 파일",
        )

        if uploaded_raws:
            st.info(f"**{len(uploaded_raws)}개 파일** 선택됨: {', '.join(f.name for f in uploaded_raws)}")
            if st.button("💾 Raw data/ 에 저장", key="save_raw"):
                for uf in uploaded_raws:
                    save_path = _RAW_DIR / uf.name
                    save_path.write_bytes(uf.read())
                st.success(f"✅ {len(uploaded_raws)}개 파일 저장 완료 → Raw data/ 폴더")
                st.rerun()

        st.divider()

        all_raws = sorted(_RAW_DIR.glob("*.xlsx"))
        if not all_raws:
            st.warning("⚠️ Raw data/ 폴더에 Excel 파일이 없습니다. 위에서 업로드하세요.")
        else:
            st.markdown(f"전처리 대상: **{len(all_raws)}개** 파일")
            for f in all_raws:
                st.markdown(f"  - `{f.name}`")

            if st.button("⚙️ 전처리 실행", type="primary", use_container_width=True, key="run_preprocess"):
                log_area = st.empty()
                try:
                    with st.spinner("전처리 실행 중..."):
                        buf = _io.StringIO()
                        with contextlib.redirect_stdout(buf):
                            mod = _load_preprocessor()
                            mod.main()
                        log_text = buf.getvalue()

                    st.success("✅ 전처리 완료! output/ 폴더에 CSV 파일이 생성되었습니다.")
                    with st.expander("📋 전처리 로그 보기", expanded=True):
                        st.code(log_text, language=None)

                    if NATIONAL_CSV.exists() and REGIONAL_CSV.exists():
                        nat_df, reg_df = dl.load_all_data()
                        years = sorted(nat_df["연도"].unique().tolist(), reverse=True)
                        st.session_state.national_df = nat_df
                        st.session_state.regional_df = reg_df
                        st.session_state.selected_year = years[0]
                        _calc_stats()
                        st.success(f"📊 데이터 자동 로드 완료 — {years}년 데이터 준비됨")
                        if st.button("▶ 2단계 통계 확인으로 이동", type="primary"):
                            _go(2)
                            st.rerun()

                except Exception as e:
                    st.error(f"전처리 오류: {e}")
                    with st.expander("🔍 오류 상세"):
                        import traceback
                        st.code(traceback.format_exc())

    # ── 탭 2: CSV 직접 업로드 ───────────────────────────────────────────────
    with tab_csv_upload:
        st.markdown("**전처리 결과 CSV 2개를 업로드하세요.**")
        col1, col2 = st.columns(2)
        with col1:
            nat_file = st.file_uploader(
                "전체_대학_데이터.csv",
                type=["csv"],
                key="upload_national",
                help="연도, 학교명, 전임교원수, SCI/SCOPUS논문수, 1인당논문수, 전국순위",
            )
        with col2:
            reg_file = st.file_uploader(
                "충청권_순위.csv",
                type=["csv"],
                key="upload_regional",
                help="연도, 학교명, 전임교원수, SCI/SCOPUS논문수, 1인당논문수, 충청권순위, 전국순위",
            )

        if nat_file and reg_file:
            try:
                nat_df = pd.read_csv(nat_file, encoding="utf-8-sig")
                reg_df = pd.read_csv(reg_file, encoding="utf-8-sig")
                st.success(f"✅ 업로드 완료 — 전국 **{len(nat_df)}행** / 충청권 **{len(reg_df)}행**")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**전국 데이터 미리보기**")
                    st.dataframe(nat_df.head(5), use_container_width=True)
                with col_b:
                    st.markdown("**충청권 데이터 미리보기**")
                    st.dataframe(reg_df.head(5), use_container_width=True)

                years = sorted(nat_df["연도"].unique().tolist(), reverse=True)
                selected = st.selectbox("기준 연도 선택", years, key="year_sel_upload")

                if st.button("✅ 이 데이터로 분석 시작", type="primary", use_container_width=True):
                    st.session_state.national_df = nat_df
                    st.session_state.regional_df = reg_df
                    st.session_state.selected_year = selected
                    _calc_stats()
                    _go(2)
                    st.rerun()
            except Exception as e:
                st.error(f"파일 읽기 오류: {e}")

    # ── 탭 3: 기존 output/ 폴더 사용 ────────────────────────────────────────
    with tab_existing:
        nat_exists = NATIONAL_CSV.exists()
        reg_exists = REGIONAL_CSV.exists()

        if nat_exists and reg_exists:
            nat_df_ex = pd.read_csv(NATIONAL_CSV, encoding="utf-8-sig")
            reg_df_ex = pd.read_csv(REGIONAL_CSV, encoding="utf-8-sig")
            years_ex = sorted(nat_df_ex["연도"].unique().tolist(), reverse=True)

            st.success(f"✅ output/ 폴더 파일 확인됨 — **{years_ex}**년 데이터")

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**전국 데이터 미리보기**")
                st.dataframe(nat_df_ex.head(5), use_container_width=True)
            with col_b:
                st.markdown("**충청권 데이터 미리보기**")
                st.dataframe(reg_df_ex.head(5), use_container_width=True)

            selected_ex = st.selectbox("기준 연도 선택", years_ex, key="year_sel_existing")

            if st.button("✅ 기존 파일로 분석 시작", type="primary", use_container_width=True):
                st.session_state.national_df = nat_df_ex
                st.session_state.regional_df = reg_df_ex
                st.session_state.selected_year = selected_ex
                _calc_stats()
                _go(2)
                st.rerun()
        else:
            missing = []
            if not nat_exists:
                missing.append("전체_대학_데이터.csv")
            if not reg_exists:
                missing.append("충청권_순위.csv")
            st.warning(f"⚠️ output/ 폴더에 파일 없음: {', '.join(missing)}")
            st.info("🔧 원시 데이터 전처리 탭에서 전처리를 먼저 실행하세요.")


# ===========================================================================
# ■ STEP 2: 통계 확인
# ===========================================================================
elif st.session_state.step == 2:
    year = st.session_state.selected_year
    hoseo = st.session_state.hoseo_trend
    avgs  = st.session_state.averages
    ranks = st.session_state.rank_changes
    yoy   = st.session_state.yoy_changes
    cmpd  = st.session_state.compare_data

    st.markdown(f'<div class="ir-section-title">📋 2단계: 통계 확인 — {year}년 기준</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ir-stat-banner">계산된 수치를 검토하세요. 이상이 없으면 다음 단계로 진행합니다.</div>', unsafe_allow_html=True)

    # --- 핵심 지표 카드 ---
    if year in hoseo:
        d = hoseo[year]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "📝 1인당 논문수",
            f"{d['1인당논문수']:.4f}",
            delta=f"{yoy['호서']['증감률']:+.1f}%" if yoy.get("호서") else None,
        )
        rc = ranks.get(year, {})
        c2.metric(
            "🏅 충청권 순위",
            f"{d['충청권순위']}위" if d.get("충청권순위") else "-",
            delta=f"{rc.get('충청권순위_변화', 0):+d}계단" if rc.get("충청권순위_변화") else None,
            delta_color="inverse",
        )
        c3.metric(
            "🌐 전국 순위",
            f"{d['전국순위']}위",
            delta=f"{rc.get('전국순위_변화', 0):+d}계단" if rc.get("전국순위_변화") else None,
            delta_color="inverse",
        )
        c4.metric("👥 전임교원수", f"{d['전임교원수']:,}명")

    st.divider()

    with st.expander("📋 연도별 상세 수치", expanded=True):
        rows = []
        for y, d in sorted(hoseo.items()):
            r = ranks.get(y, {})
            rows.append({
                "연도": y,
                "전임교원수": d["전임교원수"],
                "SCI/SCOPUS 논문수": d["논문수"],
                "1인당 논문수": d["1인당논문수"],
                "충청권 순위": d.get("충청권순위", "-"),
                "전국 순위": d["전국순위"],
                "충청권 순위 변화": r.get("충청권순위_변화"),
                "전국 순위 변화": r.get("전국순위_변화"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("📊 연도별 평균 비교", expanded=True):
        avg_rows = []
        for y, a in sorted(avgs.items()):
            h = hoseo.get(y, {})
            avg_rows.append({
                "연도": y,
                f"{UNIVERSITY}": h.get("1인당논문수"),
                "전국 평균": a["전국평균"],
                "충청권 평균": a["충청권평균"],
                "비교군 평균": a["비교군평균"],
            })
        st.dataframe(pd.DataFrame(avg_rows), use_container_width=True, hide_index=True)

    with st.expander(f"🏫 비교군 현황 ({year}년)", expanded=True):
        st.dataframe(pd.DataFrame(cmpd), use_container_width=True, hide_index=True)

    with st.expander(f"📈 전년대비 증감 ({year-1}→{year}년)", expanded=False):
        if yoy.get("상위") or yoy.get("하위"):
            col_top, col_bot = st.columns(2)
            with col_top:
                st.markdown("**📈 증감 상위 3개 대학**")
                st.dataframe(pd.DataFrame(yoy.get("상위", [])), use_container_width=True, hide_index=True)
            with col_bot:
                st.markdown("**📉 증감 하위 3개 대학**")
                st.dataframe(pd.DataFrame(yoy.get("하위", [])), use_container_width=True, hide_index=True)
            if yoy.get("호서"):
                st.info(
                    f"**{UNIVERSITY}**: {yoy['호서']['기준연도']:.4f} → {yoy['호서']['비교연도']:.4f}"
                    f"  증감률 **{yoy['호서']['증감률']:+.1f}%**"
                )
        else:
            st.info("전년도 데이터 없음")

    st.divider()
    col_prev, _, col_next = st.columns([1, 4, 1])
    col_prev.button("← 1단계로", on_click=_go, args=(1,), use_container_width=True)
    col_next.button("다음: 그래프 검토 →", type="primary", on_click=_go, args=(3,), use_container_width=True)


# ===========================================================================
# ■ STEP 3: 그래프 검토
# ===========================================================================
elif st.session_state.step == 3:
    year   = st.session_state.selected_year
    hoseo  = st.session_state.hoseo_trend
    avgs   = st.session_state.averages
    ranks  = st.session_state.rank_changes
    cmpd   = st.session_state.compare_data
    reg_df = st.session_state.regional_df

    st.markdown('<div class="ir-section-title">📈 3단계: 그래프 검토</div>', unsafe_allow_html=True)
    st.markdown('<div class="ir-stat-banner">5종 차트를 확인하세요. 보고서에 그대로 삽입됩니다.</div>', unsafe_allow_html=True)

    if not st.session_state.charts:
        with st.spinner("차트 생성 중..."):
            st.session_state.charts = {
                "trend":   cg.create_trend_chart(hoseo, avgs),
                "bar":     cg.create_comparison_bar(reg_df, year),
                "avg":     cg.create_avg_comparison(hoseo, avgs, year),
                "rank":    cg.create_rank_trend_chart(ranks),
                "compare": cg.create_compare_group_bar(cmpd, year),
            }

    charts = st.session_state.charts

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 연도별 추이", "🏫 충청권 비교", "📊 평균 비교", "🏆 순위 변화", "🔍 비교군"
    ])

    def _chart_tab(tab, key: str, title: str):
        with tab:
            st.markdown(f"**{title}**")
            buf = charts[key]
            buf.seek(0)
            st.image(buf, use_container_width=True)
            buf.seek(0)
            st.download_button(
                "⬇️ 이미지 저장",
                data=buf.read(),
                file_name=f"{key}_{year}.png",
                mime="image/png",
                key=f"dl_{key}",
            )

    _chart_tab(tab1, "trend",   f"연도별 1인당논문수 추이 (호서 vs 전국/충청권/비교군 평균)")
    _chart_tab(tab2, "bar",     f"{year}년 충청권 대학 전체 비교")
    _chart_tab(tab3, "avg",     f"{year}년 1인당논문수 평균 비교")
    _chart_tab(tab4, "rank",    f"충청권·전국 순위 변화 추이")
    _chart_tab(tab5, "compare", f"{year}년 비교군 5개교 비교")

    st.divider()
    col_prev, _, col_next = st.columns([1, 4, 1])
    col_prev.button("← 2단계로", on_click=_go, args=(2,), use_container_width=True)
    col_next.button("다음: GPT 서술 →", type="primary", on_click=_go, args=(4,), use_container_width=True)


# ===========================================================================
# ■ STEP 4: GPT 서술 생성 및 편집
# ===========================================================================
elif st.session_state.step == 4:
    year  = st.session_state.selected_year
    hoseo = st.session_state.hoseo_trend
    avgs  = st.session_state.averages
    ranks = st.session_state.rank_changes
    yoy   = st.session_state.yoy_changes
    cmpd  = st.session_state.compare_data

    st.markdown('<div class="ir-section-title">🤖 4단계: GPT 서술 생성 및 편집</div>', unsafe_allow_html=True)
    st.markdown('<div class="ir-stat-banner">각 섹션 우측 <strong>[🤖 GPT 생성]</strong> 버튼을 누르면 AI가 보고서 텍스트를 자동 작성합니다. 생성 후 직접 편집도 가능합니다.</div>', unsafe_allow_html=True)

    if not st.session_state.api_key:
        st.error("⛔ 사이드바에서 OpenAI API Key를 입력하고 [💾 저장] 버튼을 누르세요.")
        st.stop()

    def _get_client() -> OpenAI:
        return OpenAI(api_key=st.session_state.api_key)

    # ── GPT 버튼 처리 (text_area 렌더 전에 먼저 실행) ──────────────────────
    if st.button("🤖 섹션 1 생성: 연도별 추이", key="gen_trend"):
        with st.spinner("GPT 생성 중... (10~20초 소요)"):
            try:
                st.session_state.narrative_trend = gpt.generate_trend_narrative(
                    _get_client(), hoseo, avgs
                )
                st.rerun()
            except Exception as e:
                st.error(f"GPT 오류: {e}")

    if st.button("🤖 섹션 2 생성: 비교군 분석", key="gen_comparison"):
        with st.spinner("GPT 생성 중... (10~20초 소요)"):
            try:
                st.session_state.narrative_comparison = gpt.generate_comparison_narrative(
                    _get_client(), cmpd, avgs, year
                )
                st.rerun()
            except Exception as e:
                st.error(f"GPT 오류: {e}")

    if st.button("🤖 섹션 3 생성: 충청권 순위", key="gen_regional"):
        with st.spinner("GPT 생성 중... (10~20초 소요)"):
            try:
                st.session_state.narrative_regional = gpt.generate_regional_narrative(
                    _get_client(), hoseo, ranks
                )
                st.rerun()
            except Exception as e:
                st.error(f"GPT 오류: {e}")

    if st.button("🤖 섹션 4 생성: 전년대비 증감", key="gen_yoy"):
        with st.spinner("GPT 생성 중... (10~20초 소요)"):
            try:
                st.session_state.narrative_yoy = gpt.generate_yoy_narrative(
                    _get_client(), yoy, year
                )
                st.rerun()
            except Exception as e:
                st.error(f"GPT 오류: {e}")

    st.divider()

    # ── 섹션 1 ─────────────────────────────────────────────────────────────
    _badge1 = '<span class="ir-badge-done">✓ 작성 완료</span>' if st.session_state.narrative_trend else '<span class="ir-badge-empty">미작성</span>'
    st.markdown(f"""
    <div class="ir-gpt-header">
      <div>
        <div class="ir-gpt-title">섹션 1. 연도별 1인당논문수 추이</div>
        <div class="ir-gpt-hint">연도별 호서대 수치 변화 및 평균 대비 분석</div>
      </div>
      {_badge1}
    </div>
    """, unsafe_allow_html=True)
    st.text_area(
        "내용 직접 편집 가능",
        key="narrative_trend",
        height=160,
        placeholder="위의 [🤖 섹션 1 생성] 버튼을 누르거나 직접 입력하세요.",
        label_visibility="collapsed",
    )

    # ── 섹션 2 ─────────────────────────────────────────────────────────────
    _badge2 = '<span class="ir-badge-done">✓ 작성 완료</span>' if st.session_state.narrative_comparison else '<span class="ir-badge-empty">미작성</span>'
    st.markdown(f"""
    <div class="ir-gpt-header">
      <div>
        <div class="ir-gpt-title">섹션 2. 전국·충청권·비교군 평균 비교 ({year}년)</div>
        <div class="ir-gpt-hint">전국/충청권/비교군 평균 대비 호서대 위치 분석</div>
      </div>
      {_badge2}
    </div>
    """, unsafe_allow_html=True)
    st.text_area(
        "내용 직접 편집 가능",
        key="narrative_comparison",
        height=160,
        placeholder="위의 [🤖 섹션 2 생성] 버튼을 누르거나 직접 입력하세요.",
        label_visibility="collapsed",
    )

    # ── 섹션 3 ─────────────────────────────────────────────────────────────
    _badge3 = '<span class="ir-badge-done">✓ 작성 완료</span>' if st.session_state.narrative_regional else '<span class="ir-badge-empty">미작성</span>'
    st.markdown(f"""
    <div class="ir-gpt-header">
      <div>
        <div class="ir-gpt-title">섹션 3. 충청권 순위 변화</div>
        <div class="ir-gpt-hint">충청권·전국 순위 추이 및 순위 변동 해석</div>
      </div>
      {_badge3}
    </div>
    """, unsafe_allow_html=True)
    st.text_area(
        "내용 직접 편집 가능",
        key="narrative_regional",
        height=160,
        placeholder="위의 [🤖 섹션 3 생성] 버튼을 누르거나 직접 입력하세요.",
        label_visibility="collapsed",
    )

    # ── 섹션 4 ─────────────────────────────────────────────────────────────
    _badge4 = '<span class="ir-badge-done">✓ 작성 완료</span>' if st.session_state.narrative_yoy else '<span class="ir-badge-empty">미작성</span>'
    st.markdown(f"""
    <div class="ir-gpt-header">
      <div>
        <div class="ir-gpt-title">섹션 4. 전년대비 증감 ({year-1}→{year}년)</div>
        <div class="ir-gpt-hint">충청권 대학별 증감률 및 호서대 변화 해석</div>
      </div>
      {_badge4}
    </div>
    """, unsafe_allow_html=True)
    st.text_area(
        "내용 직접 편집 가능",
        key="narrative_yoy",
        height=160,
        placeholder="위의 [🤖 섹션 4 생성] 버튼을 누르거나 직접 입력하세요.",
        label_visibility="collapsed",
    )

    st.divider()

    # --- 완료 상태 요약 ---
    filled_count = sum([
        bool(st.session_state.narrative_trend),
        bool(st.session_state.narrative_comparison),
        bool(st.session_state.narrative_regional),
        bool(st.session_state.narrative_yoy),
    ])
    if filled_count < 4:
        st.warning(f"서술 작성 현황: **{filled_count}/4** 섹션 완료. 빈 섹션은 보고서에서 생략됩니다.")
    else:
        st.success("✅ 4개 섹션 모두 완료! 다음 단계로 진행하세요.")

    col_prev, _, col_next = st.columns([1, 4, 1])
    col_prev.button("← 3단계로", on_click=_go, args=(3,), use_container_width=True)
    col_next.button("다음: 보고서 생성 →", type="primary", on_click=_go, args=(5,), use_container_width=True)


# ===========================================================================
# ■ STEP 5: 보고서 최종 생성
# ===========================================================================
elif st.session_state.step == 5:
    year   = st.session_state.selected_year
    hoseo  = st.session_state.hoseo_trend
    avgs   = st.session_state.averages
    ranks  = st.session_state.rank_changes
    yoy    = st.session_state.yoy_changes
    cmpd   = st.session_state.compare_data
    charts = st.session_state.charts

    # _saved_ 키에서 읽기 (위젯 키는 5단계에서 Streamlit이 삭제하므로)
    narratives = {
        "trend":      st.session_state.get("_saved_narrative_trend", st.session_state.get("narrative_trend", "")),
        "comparison": st.session_state.get("_saved_narrative_comparison", st.session_state.get("narrative_comparison", "")),
        "regional":   st.session_state.get("_saved_narrative_regional", st.session_state.get("narrative_regional", "")),
        "yoy":        st.session_state.get("_saved_narrative_yoy", st.session_state.get("narrative_yoy", "")),
    }

    st.markdown('<div class="ir-section-title">📄 5단계: 보고서 최종 생성</div>', unsafe_allow_html=True)
    st.markdown('<div class="ir-stat-banner">아래 내용을 최종 확인 후 Word 파일을 생성하세요.</div>', unsafe_allow_html=True)

    with st.expander("📋 포함 내용 확인", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**기본 정보**")
            st.markdown(f"- 대학: **{UNIVERSITY}**")
            st.markdown(f"- 기준 연도: **{year}년**")
            st.markdown(f"- 그래프: **{len([c for c in charts.values() if c])}종**")
        with col_b:
            st.markdown("**GPT 서술 포함 여부**")
            for lbl, key in [("연도별 추이", "trend"), ("비교군 분석", "comparison"),
                              ("충청권 순위", "regional"), ("전년대비 증감", "yoy")]:
                icon = "✅" if narratives[key] else "⬜"
                st.markdown(f"- {icon} {lbl}")

    if st.button("📄 Word 보고서 생성", type="primary", use_container_width=True):
        with st.spinner("Word 파일 생성 중..."):
            try:
                REPORT_DIR.mkdir(parents=True, exist_ok=True)
                buf = rb.build_report(
                    year=year,
                    hoseo_trend=hoseo,
                    averages=avgs,
                    compare_data=cmpd,
                    yoy_changes=yoy,
                    rank_changes=ranks,
                    charts=charts,
                    narratives=narratives,
                )
                st.session_state.report_buf = buf
            except Exception as e:
                st.error(f"오류 발생: {e}")
                raise

    if st.session_state.report_buf:
        st.success("✅ 보고서 생성 완료!")
        fname = f"{UNIVERSITY}_연구실적_보고서_{year}.docx"
        st.session_state.report_buf.seek(0)
        st.download_button(
            label=f"⬇️ {fname} 다운로드",
            data=st.session_state.report_buf,
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
        )

    st.divider()
    col_prev, _, col_restart = st.columns([1, 3, 1])
    col_prev.button("← 4단계로", on_click=_go, args=(4,), use_container_width=True)
    if col_restart.button("🔄 처음부터", use_container_width=True):
        for k, v in _DEFAULTS.items():
            st.session_state[k] = v
        st.session_state.api_key = os.getenv("OPENAI_API_KEY", "")
        st.rerun()


# ===========================================================================
# ■ 푸터
# ===========================================================================
st.markdown(f"""
<div class="ir-footer">
  호서대학교 IR센터 · 연구실적 분석 포털 v3.0 &nbsp;|&nbsp;
  현재 단계: {st.session_state.step}/5 &nbsp;|&nbsp;
  Powered by GPT-4o &amp; Streamlit
</div>
""", unsafe_allow_html=True)
