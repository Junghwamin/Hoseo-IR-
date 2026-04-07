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
설정 페이지 모듈

앱의 일반 설정, API 연동 상태, 환경 정보를 표시한다.
Amplitude Organization Settings 패턴을 따라 카드 레이아웃으로 구성한다.
"""

from __future__ import annotations
import sys
import streamlit as st
from report_app.config import (
    UNIVERSITY, COMPARE_GROUP, COMPARE_GROUP_NAME,
    GPT_MODEL, GPT_MAX_TOKENS, GPT_TEMPERATURE,
)


def render_settings():
    """설정 페이지를 렌더링한다.

    대학명·비교군 등 일반 설정, OpenAI API 연동 상태, 앱 버전/환경 정보를
    카드 형태로 표시한다. Amplitude Organization Settings 패턴 적용.

    표시 항목:
        - 일반 설정: 대학명, 비교 대학군 목록, GPT 모델/파라미터
        - API 연동: OpenAI API Key 마스킹 표시 (session_state["api_key"] 참조)
        - 앱 정보: 버전, Streamlit 버전, Python 버전

    Note:
        - API Key는 앞 7자 + "..." + 뒤 4자 형태로 마스킹하여 표시
        - 카드 스타일은 app.py에서 주입한 ir-chart-card CSS 클래스에 의존
    """

    # 페이지 헤더
    st.markdown("""
    <div style="margin-bottom:1.5rem;">
        <h2 style="font-size:1.25rem; font-weight:700; color:#18181B; margin:0 0 0.25rem;">설정</h2>
        <p style="font-size:0.875rem; color:#71717A; margin:0;">앱 설정 및 환경 정보를 확인합니다.</p>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 카드 1: 일반 설정
    # -------------------------------------------------------------------------
    st.markdown('<div class="ir-chart-card" style="margin-bottom:1rem;">', unsafe_allow_html=True)
    st.markdown('<div class="ir-chart-header"><div class="ir-chart-title">일반 설정</div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**대학명**")
        st.code(UNIVERSITY, language=None)

        st.markdown(f"**비교 대학군** ({COMPARE_GROUP_NAME})")
        for univ in COMPARE_GROUP:
            # 대상 대학에 마커 표시
            marker = " ← 대상" if univ == UNIVERSITY else ""
            st.markdown(f"- {univ}{marker}")

    with col2:
        st.markdown("**GPT 설정**")
        st.markdown(f"- 모델: `{GPT_MODEL}`")
        st.markdown(f"- Max Tokens: `{GPT_MAX_TOKENS}`")
        st.markdown(f"- Temperature: `{GPT_TEMPERATURE}`")

    st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 카드 2: API 연동
    # -------------------------------------------------------------------------
    st.markdown('<div class="ir-chart-card" style="margin-bottom:1rem;">', unsafe_allow_html=True)
    st.markdown('<div class="ir-chart-header"><div class="ir-chart-title">API 연동</div></div>', unsafe_allow_html=True)

    api_key = st.session_state.get("api_key", "")
    if api_key:
        # 보안을 위해 앞 7자 + "..." + 뒤 4자 형태로 마스킹
        masked = api_key[:7] + "..." + api_key[-4:] if len(api_key) > 15 else "***"
        st.success(f"✅ OpenAI API Key 설정됨: `{masked}`")
    else:
        st.warning("⚠️ OpenAI API Key가 설정되지 않았습니다. 사이드바에서 설정하세요.")

    st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 카드 3: 앱 정보
    # -------------------------------------------------------------------------
    st.markdown('<div class="ir-chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="ir-chart-header"><div class="ir-chart-title">앱 정보</div></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.markdown("**버전**\n\nv5.0")
    col2.markdown(f"**Streamlit**\n\n{st.__version__}")
    col3.markdown(f"**Python**\n\n{sys.version.split()[0]}")

    st.markdown('</div>', unsafe_allow_html=True)
