"""
chart_card.py — Amplitude 스타일 차트 카드 컴포넌트

matplotlib 차트를 Amplitude 대시보드처럼 카드 형태로 감싸서 렌더링한다.
헤더(제목/서브타이틀), 차트 이미지, 액션 버튼(확대/저장),
하단 Breakdown 테이블을 포함한다.
"""

import streamlit as st
import pandas as pd
from io import BytesIO


# ──────────────────────────────────────────────────────────────
# 모달 다이얼로그 — 모듈 레벨에 정의 (st.dialog 제약)
# title, chart_buf, breakdown_df 는 session_state를 경유해 전달한다.
# ──────────────────────────────────────────────────────────────

@st.dialog("차트 확대", width="large")
def _show_chart_dialog() -> None:
    """세션 상태에서 차트 정보를 읽어 확대 모달을 렌더링한다.

    session_state 키:
        _chart_dialog_title (str): 모달 상단에 표시할 차트 제목
        _chart_dialog_buf (BytesIO): matplotlib 차트 버퍼
        _chart_dialog_df (pd.DataFrame | None): 하단 데이터 테이블 (없으면 None)

    Note:
        - @st.dialog은 함수 정의 시점에 데코레이팅되므로,
          동적 인자는 session_state를 통해 우회해야 한다.
        - chart_buf.seek(0) 필수 — BytesIO 포지션 리셋 후 읽어야 함
    """
    title: str = st.session_state.get("_chart_dialog_title", "")
    chart_buf: BytesIO = st.session_state["_chart_dialog_buf"]
    breakdown_df: pd.DataFrame | None = st.session_state.get("_chart_dialog_df")

    st.markdown(f"**{title}**")

    # BytesIO 포지션 리셋 후 이미지 표시
    chart_buf.seek(0)
    st.image(chart_buf, use_container_width=True)

    if breakdown_df is not None:
        st.divider()
        st.markdown("**데이터**")
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────
# 공개 API
# ──────────────────────────────────────────────────────────────

def render_chart_card(
    title: str,
    subtitle: str,
    chart_buf: BytesIO,
    breakdown_df: pd.DataFrame | None = None,
    chart_key: str = "chart",
    year: int = 2025,
) -> None:
    """차트를 Amplitude 스타일 카드로 렌더링한다.

    카드 구조:
        - 헤더: 제목 + 서브타이틀 (HTML 스타일 적용)
        - 본문: matplotlib 차트 이미지 (use_container_width=True)
        - 액션 버튼: 🔍 확대(모달) / ⬇️ 저장(PNG 다운로드)
        - 하단: Breakdown 데이터 테이블 (breakdown_df 있을 때만 표시)

    Args:
        title: 차트 제목 (헤더 상단 굵은 텍스트)
        subtitle: 차트 부제목 (헤더 하단 작은 텍스트)
        chart_buf: matplotlib 차트가 담긴 BytesIO 객체.
                   내부에서 seek(0) 처리를 하므로 호출 전 seek 불필요.
        breakdown_df: 차트 하단에 표시할 데이터 테이블.
                      None이면 테이블 섹션을 렌더링하지 않는다.
        chart_key: 위젯 중복 방지용 고유 키 문자열.
                   같은 페이지에 여러 카드를 쓸 때 반드시 다르게 지정해야 한다.
        year: 다운로드 PNG 파일명에 포함할 연도 (예: f"{chart_key}_{year}.png")

    Note:
        - buf.getvalue()로 다운로드 데이터를 전달한다.
          buf.read()는 버퍼 소진 문제가 발생하므로 사용 금지.
        - 확대 모달(_show_chart_dialog)은 모듈 레벨에 정의되어 있으며,
          session_state(_chart_dialog_*)를 통해 동적 인자를 전달한다.
    """
    # ── 1. 카드 헤더 (HTML) ──────────────────────────────────
    st.markdown(
        f"""
        <div class="ir-chart-card">
          <div class="ir-chart-header">
            <div>
              <div class="ir-chart-title">{title}</div>
              <div class="ir-chart-subtitle">{subtitle}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── 2. 차트 이미지 ───────────────────────────────────────
    # seek(0): BytesIO 읽기 포지션을 처음으로 리셋해야 이미지를 정상 표시
    chart_buf.seek(0)
    st.image(chart_buf, use_container_width=True)

    # ── 3. 액션 버튼 (확대 / 저장) ──────────────────────────
    col_zoom, col_dl, col_space = st.columns([1, 1, 4])

    with col_zoom:
        if st.button("🔍 확대", key=f"zoom_{chart_key}"):
            # session_state 경유: @st.dialog은 인자를 직접 받을 수 없음
            st.session_state["_chart_dialog_title"] = title
            st.session_state["_chart_dialog_buf"] = chart_buf
            st.session_state["_chart_dialog_df"] = breakdown_df
            _show_chart_dialog()

    with col_dl:
        # getvalue(): 포지션과 무관하게 버퍼 전체 바이트 반환 (read()와 달리 소진 없음)
        st.download_button(
            "⬇️ 저장",
            data=chart_buf.getvalue(),
            file_name=f"{chart_key}_{year}.png",
            mime="image/png",
            key=f"dl_{chart_key}",
        )

    # col_space는 나머지 공간을 채우는 빈 컬럼 (레이아웃 균형용)
    _ = col_space  # noqa: F841

    # ── 4. Breakdown 테이블 (선택) ───────────────────────────
    if breakdown_df is not None:
        st.markdown('<div class="ir-chart-breakdown">', unsafe_allow_html=True)
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
