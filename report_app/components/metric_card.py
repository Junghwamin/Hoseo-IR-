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

# report_app/components/metric_card.py
# Amplitude 스타일 KPI 메트릭 카드 컴포넌트
# CSS 클래스 정의는 report_app/styles.py 에서 관리됨

import streamlit as st


def render_metric_cards(metrics: list[dict]):
    """메트릭 카드 여러 개를 가로로 배치하여 렌더링한다.

    Amplitude 스타일의 KPI 카드를 st.columns()를 사용해 균등 분할하고,
    각 컬럼에 HTML 카드를 삽입한다. delta_type에 따라 색상 및 화살표가
    자동으로 결정된다.

    Args:
        metrics: 각 카드 정보 딕셔너리의 리스트.
            필수 키:
                - "label" (str): 카드 상단에 표시되는 지표명.
                                 예: "1인당 논문수"
                - "value" (str): 굵게 표시되는 핵심 수치.
                                 예: "0.2847"
            선택 키:
                - "delta" (str | None): 전기 대비 증감 문자열.
                                        예: "+12.3%", "-0.05편"
                - "delta_type" (str | None): "up", "down", "neutral" 중 하나.
                                             None이면 "neutral" 처리.
                - "icon" (str | None): 카드 레이블 앞에 붙는 이모지 또는 아이콘.
                                       예: "📝", "🏫"

    Returns:
        None: streamlit에 직접 렌더링하며 반환값 없음.

    Example:
        >>> render_metric_cards([
        ...     {"label": "1인당 논문수", "value": "0.2847",
        ...      "delta": "+12.3%", "delta_type": "up", "icon": "📄"},
        ...     {"label": "충청권 순위",  "value": "3위",
        ...      "delta": "▼ 1단계", "delta_type": "down"},
        ... ])

    Note:
        - CSS 클래스 (.ir-metric-card, .ir-metric-label, .ir-metric-value,
          .ir-metric-delta.up / .down / .neutral) 는 styles.py 에서 정의한다.
        - metrics 리스트가 비어 있으면 아무것도 렌더링하지 않는다.
        - delta_type이 "up"이면 초록색 ▲, "down"이면 빨간색 ▼, 그 외 회색 표시.
    """
    if not metrics:
        return

    # 카드 개수만큼 균등 컬럼 분할
    cols = st.columns(len(metrics))

    for col, m in zip(cols, metrics):
        with col:
            # === delta HTML 구성 ===
            # delta_type: "up" → 초록 ▲ / "down" → 빨강 ▼ / "neutral" → 회색 (화살표 없음)
            delta_html = ""
            if m.get("delta"):
                cls = m.get("delta_type") or "neutral"
                if cls == "up":
                    arrow = "▲"
                elif cls == "down":
                    arrow = "▼"
                else:
                    arrow = ""
                delta_html = (
                    f'<div class="ir-metric-delta {cls}">'
                    f'{arrow} {m["delta"]}'
                    f'</div>'
                )

            # === 아이콘 HTML 구성 ===
            # 아이콘이 있으면 레이블 텍스트 앞에 약간의 여백과 함께 삽입
            icon_html = (
                f'<span style="margin-right:4px">{m["icon"]}</span>'
                if m.get("icon")
                else ""
            )

            # === 카드 HTML 렌더링 ===
            # ir-metric-card  : 카드 전체 컨테이너 (border, shadow, padding)
            # ir-metric-label : 지표명 (소문자, 회색)
            # ir-metric-value : 핵심 수치 (크고 굵게)
            # ir-metric-delta : 증감 표시 (delta_type 클래스로 색상 결정)
            st.markdown(
                f"""
                <div class="ir-metric-card">
                    <div class="ir-metric-label">{icon_html}{m["label"]}</div>
                    <div class="ir-metric-value">{m["value"]}</div>
                    {delta_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
