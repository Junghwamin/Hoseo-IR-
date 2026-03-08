"""Home 화면 렌더링 모듈.

분석 모듈 선택 카드와 환영 메시지를 표시한다.
CSS 클래스(ir-module-card, ir-badge-coming 등)는 styles.py에서 정의됨.
"""
from __future__ import annotations

import streamlit as st


def render_home() -> str | None:
    """Home 화면을 렌더링한다.

    분석 모듈 선택 카드를 3열 레이아웃으로 표시하며,
    사용자가 모듈 카드의 '시작하기' 버튼을 클릭하면 해당 모듈 ID를 반환한다.
    비활성화된 모듈(준비 중)은 '준비 중' 뱃지를 표시하고 버튼을 비활성화한다.

    Returns:
        선택된 모듈 ID ("research" 등) 또는 None (선택 안 함)

    Note:
        - ir-module-card, ir-badge-coming 등 CSS 클래스는 styles.py에서 정의
        - 새 모듈 추가 시 col 블록을 복사하고 key와 반환값을 수정
    """
    selected = None

    # 환영 메시지 배너
    st.markdown("""
    <div style="text-align:center; padding:2rem 0 1.5rem;">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">📊</div>
        <h2 style="font-size:1.5rem; font-weight:800; color:#1a56db; margin:0 0 0.5rem;">
            호서대학교 IR센터 분석 포털
        </h2>
        <p style="font-size:0.9375rem; color:#71717A; margin:0;">
            분석할 지표를 선택하세요
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 모듈 선택 카드 3개 — 3열 레이아웃
    col1, col2, col3 = st.columns(3)

    # --- 모듈 1: 전임교원 연구실적 (활성) ---
    with col1:
        st.markdown("""
        <div class="ir-module-card">
            <div class="ir-module-icon">📊</div>
            <div class="ir-module-title">전임교원 연구실적</div>
            <div class="ir-module-desc">
                SCI/SCOPUS 논문 현황 분석<br>
                전국·충청권·비교군 비교<br>
                GPT 보고서 자동 생성
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("시작하기 →", key="home_research", type="primary", use_container_width=True):
            selected = "research"

    # --- 모듈 2: 교육비환원율 (준비 중) ---
    with col2:
        st.markdown("""
        <div class="ir-module-card disabled">
            <div class="ir-module-icon" style="opacity:0.3;">📈</div>
            <div class="ir-module-title">교육비환원율</div>
            <div class="ir-module-desc" style="color:#A1A1AA;">
                교육비환원율 현황 분석<br>
                대학별 비교 분석<br>
                <br>
            </div>
            <span class="ir-badge-coming">준비 중</span>
        </div>
        """, unsafe_allow_html=True)
        st.button("Coming Soon", key="home_edu", disabled=True, use_container_width=True)

    # --- 모듈 3: 취업률 (준비 중) ---
    with col3:
        st.markdown("""
        <div class="ir-module-card disabled">
            <div class="ir-module-icon" style="opacity:0.3;">💼</div>
            <div class="ir-module-title">취업률</div>
            <div class="ir-module-desc" style="color:#A1A1AA;">
                졸업생 취업률 분석<br>
                학과별·권역별 비교<br>
                <br>
            </div>
            <span class="ir-badge-coming">준비 중</span>
        </div>
        """, unsafe_allow_html=True)
        st.button("Coming Soon", key="home_emp", disabled=True, use_container_width=True)

    # 구분선 + 하단 안내 메시지
    st.divider()
    st.markdown("""
    <div class="ir-empty-state" style="padding:1.5rem;">
        <div class="ir-empty-title" style="font-size:0.9375rem;">
            💡 새로운 분석 모듈이 추가되면 이곳에 표시됩니다
        </div>
        <div class="ir-empty-desc">config.py에서 향후 지표를 설정할 수 있습니다</div>
    </div>
    """, unsafe_allow_html=True)

    return selected
