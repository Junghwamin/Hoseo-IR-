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

"""상단 툴바 컴포넌트 모듈.

Amplitude 스타일의 슬림 화이트 툴바를 Streamlit HTML로 렌더링한다.
로고, 브레드크럼, 날짜/버전 정보를 단일 수평 바로 표시한다.
"""

import streamlit as st
from datetime import datetime


def render_toolbar(module_name: str, step_name: str | None = None):
    """상단 툴바를 렌더링한다.

    Amplitude 스타일의 슬림 화이트 툴바를 st.markdown()으로 출력한다.
    왼쪽에 로고+타이틀, 가운데에 브레드크럼, 오른쪽에 날짜+버전을 배치한다.

    Args:
        module_name: 현재 모듈 표시명 (예: "홈", "전임교원 연구실적 분석")
        step_name: 현재 단계명 (예: "2단계: 통계 확인").
                   None이면 브레드크럼에 단계 미표시.

    Note:
        - CSS 클래스(ir-toolbar 등)는 styles.py에서 별도 정의해야 한다.
        - 날짜는 렌더링 시점의 실제 날짜를 사용한다 (datetime.now()).
        - 버전 문자열은 config.py에서 가져오지 않고 이 파일에 상수로 고정한다.
    """
    # 현재 날짜 문자열 생성 (YYYY-MM-DD 형식)
    today = datetime.now().strftime("%Y-%m-%d")

    # 버전 상수
    version = "v5.0"

    # 브레드크럼 텍스트 조립
    # - step_name이 있으면: 홈 / module_name / step_name
    # - step_name이 없으면: 홈 / module_name
    if step_name:
        breadcrumb_html = (
            f'<span class="ir-toolbar-breadcrumb-item">홈</span>'
            f'<span class="ir-toolbar-breadcrumb-sep">/</span>'
            f'<span class="ir-toolbar-breadcrumb-item">{module_name}</span>'
            f'<span class="ir-toolbar-breadcrumb-sep">/</span>'
            f'<span class="ir-toolbar-breadcrumb-item">{step_name}</span>'
        )
    else:
        breadcrumb_html = (
            f'<span class="ir-toolbar-breadcrumb-item">홈</span>'
            f'<span class="ir-toolbar-breadcrumb-sep">/</span>'
            f'<span class="ir-toolbar-breadcrumb-item">{module_name}</span>'
        )

    # 툴바 HTML 구조 렌더링
    # 레이아웃: [로고+타이틀 | 브레드크럼 | 날짜+버전]
    toolbar_html = f"""
<div class="ir-toolbar">
  <div class="ir-toolbar-left">
    <span class="ir-toolbar-logo">📊</span>
    <span class="ir-toolbar-title" style="color:#1a56db;font-weight:700;">IR 분석 포털</span>
  </div>
  <div class="ir-toolbar-center">
    <span class="ir-toolbar-breadcrumb">
      {breadcrumb_html}
    </span>
  </div>
  <div class="ir-toolbar-right">
    <span class="ir-toolbar-date">{today}</span>
    <span class="ir-toolbar-version" style="background:#e8f0fe;color:#1a56db;padding:2px 8px;border-radius:12px;font-size:0.75rem;font-weight:500;">{version}</span>
  </div>
</div>
"""

    st.markdown(toolbar_html, unsafe_allow_html=True)
