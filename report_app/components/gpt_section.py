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

"""GPT 서술 생성/편집 섹션 컴포넌트.

@st.fragment으로 감싸 부분 리렌더링을 지원하는 재사용 가능한 컴포넌트.
4단계(GPT 서술 생성)에서 각 섹션별로 독립적으로 호출된다.
"""

import streamlit as st
from typing import Callable


@st.fragment
def render_gpt_section(
    section_key: str,
    title: str,
    hint: str,
    generate_fn: Callable | None = None,
    generate_args: tuple = (),
    generate_kwargs: dict | None = None,
):
    """GPT 서술 섹션 하나를 렌더링한다. @st.fragment로 부분 리렌더링 지원.

    카드 구조:
    - 헤더: 제목 + 힌트 + 상태 dot (초록=완료, 회색=미작성)
    - 본문: text_area (key=section_key, Streamlit이 session_state 자동 관리)
    - 하단: [🤖 GPT 생성] 버튼 + 글자수 표시

    Args:
        section_key: session_state 키이자 text_area의 key
                     (예: "narrative_trend"). 두 개를 일치시켜야
                     Streamlit이 위젯 값을 자동으로 session_state에 반영한다.
        title: 섹션 제목 (예: "섹션 1. 연도별 추이")
        hint: 힌트 텍스트 (예: "연도별 호서대 수치 변화 및 평균 대비 분석")
        generate_fn: GPT 생성 함수. None이면 [🤖 GPT 생성] 버튼 비활성화.
        generate_args: generate_fn에 전달할 인자 튜플.
                       예: (client, hoseo_df, avgs_dict)

    Note:
        - @st.fragment 내부에서는 st.rerun() 불필요 — 버튼 클릭 시 fragment만 재실행.
        - generate_fn 결과를 session_state[section_key]에 저장하면
          text_area가 다음 렌더링 시 자동으로 해당 값을 표시한다.
        - generate_fn 내부에서 발생하는 RerunException은 fragment 경계에서 처리되므로
          별도 예외 처리 불필요.
    """
    # 현재 저장된 서술 텍스트 조회 (없으면 빈 문자열)
    current_text = st.session_state.get(section_key, "")
    is_done = bool(current_text)

    # 상태 dot CSS 클래스 — done: 초록, empty: 회색
    status_cls = "done" if is_done else "empty"

    # 카드 헤더: 제목 + 힌트 + 완료 상태 dot
    st.markdown(
        f"""
        <style>
        .ir-gpt-card {{
            background: #FFFFFF;
            border: 1px solid #E4E4E7;
            border-radius: 0.75rem;
            padding: 1rem 1.25rem 0.5rem 1.25rem;
            margin-bottom: 0.5rem;
        }}
        .ir-gpt-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        .ir-gpt-title {{
            font-size: 0.9375rem;
            font-weight: 600;
            color: #18181B;
            margin-bottom: 0.2rem;
        }}
        .ir-gpt-hint {{
            font-size: 0.8125rem;
            color: #71717A;
        }}
        .ir-gpt-status {{
            width: 0.625rem;
            height: 0.625rem;
            border-radius: 50%;
            margin-top: 0.2rem;
            flex-shrink: 0;
        }}
        .ir-gpt-status.done {{
            background: #22C55E;
        }}
        .ir-gpt-status.empty {{
            background: #D4D4D8;
        }}
        </style>
        <div class="ir-gpt-card">
            <div class="ir-gpt-header">
                <div>
                    <div class="ir-gpt-title">{title}</div>
                    <div class="ir-gpt-hint">{hint}</div>
                </div>
                <div class="ir-gpt-status {status_cls}"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # [🤖 GPT 생성] 버튼 + 글자수 표시 행
    col_btn, col_info = st.columns([1, 3])

    with col_btn:
        # generate_fn이 None이면 버튼 비활성화
        gen_disabled = generate_fn is None
        if st.button(
            "🤖 GPT 생성",
            key=f"gen_{section_key}",
            disabled=gen_disabled,
            help="GPT-4o로 서술을 자동 생성합니다." if not gen_disabled else "GPT 생성 함수가 연결되지 않았습니다.",
        ):
            with st.spinner(f"{title} 생성 중..."):
                try:
                    # generate_fn 호출 — 결과 문자열을 session_state에 저장
                    _kw = generate_kwargs or {}
                    result = generate_fn(*generate_args, **_kw)
                    st.session_state[section_key] = result
                except Exception as e:
                    st.error(f"GPT 오류: {e}")

    with col_info:
        # 생성된 텍스트가 있을 때만 글자수 표시
        char_count = len(current_text)
        if char_count > 0:
            st.markdown(
                f'<div style="font-size:0.8125rem; color:#71717A; padding-top:0.5rem;">'
                f"글자수: {char_count}자</div>",
                unsafe_allow_html=True,
            )

    # 텍스트 에어리어 — key = section_key로 session_state와 자동 연동
    # 주의: value= 파라미터를 함께 쓰면 GPT 결과가 화면에 반영되지 않으므로 사용 금지
    st.text_area(
        "내용 직접 편집 가능",
        key=section_key,
        height=160,
        placeholder="[🤖 GPT 생성] 버튼을 누르거나 직접 입력하세요.",
        label_visibility="collapsed",
    )
