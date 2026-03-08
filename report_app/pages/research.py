"""
전임교원 연구실적 분석 모듈

5단계 워크플로우:
  1단계: 데이터 설정 (파일 업로드 or 기존 파일 사용)
  2단계: 통계 확인 (수치 검토 및 연도 선택)
  3단계: 그래프 검토 (차트 5종 확인)
  4단계: GPT 서술 편집 (섹션별 생성 + 직접 편집)
  5단계: 보고서 생성 (Word 파일 다운로드)
"""

from __future__ import annotations

import contextlib
import importlib.util
import io as _io
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from openai import OpenAI

from report_app import chart_generator as cg
from report_app import data_loader as dl
from report_app import gpt_reporter as gpt
from report_app import report_builder as rb
from report_app.config import NATIONAL_CSV, REGIONAL_CSV, REPORT_DIR, UNIVERSITY, IS_CLOUD, COMPARE_GROUP, COMPARE_GROUP_NAME

# 컴포넌트 import
from report_app.components.metric_card import render_metric_cards
from report_app.components.chart_card import render_chart_card
from report_app.components.gpt_section import render_gpt_section


# ===========================================================================
# 전처리 스크립트 동적 임포트 경로 탐색
# ===========================================================================
# 번들 내부(macOS) 또는 CWD(개발자/Windows) 양쪽 지원
_PREPROCESS_PATH = Path(__file__).parent.parent.parent / "전임교원_연구실적_전처리.py"
if not _PREPROCESS_PATH.exists():
    _PREPROCESS_PATH = Path.cwd() / "전임교원_연구실적_전처리.py"


def _load_preprocessor():
    """전처리 스크립트를 동적으로 로드한다.

    한글 파일명(전임교원_연구실적_전처리.py)은 일반 import로 불러올 수 없으므로
    importlib.util.spec_from_file_location을 사용해 동적으로 임포트한다.

    Returns:
        모듈 객체 (preprocessor): main() 또는 process_in_memory() 함수 포함
    """
    spec = importlib.util.spec_from_file_location("preprocessor", str(_PREPROCESS_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ===========================================================================
# 스텝 이동 헬퍼
# ===========================================================================
# text_area 위젯 키 목록 — 4단계에서만 렌더되므로
# 다른 단계로 이동 시 Streamlit이 위젯 키를 삭제한다.
# _saved_ 접두사 키에 백업하여 값을 보존한다.
_NARRATIVE_KEYS = (
    "narrative_trend",
    "narrative_comparison",
    "narrative_regional",
    "narrative_yoy",
)


def _go(step: int):
    """스텝 이동 헬퍼. narrative 값을 _saved_ 키에 백업한다.

    Streamlit은 렌더되지 않는 위젯의 session_state 키를 다음 rerun에서
    삭제하므로, 4단계 text_area 값을 _saved_ 접두사 키에 백업해야 한다.
    4단계로 돌아올 때는 백업된 값을 위젯 키에 복원한다.

    Args:
        step: 이동할 단계 번호 (1~5)
    """
    for k in _NARRATIVE_KEYS:
        val = st.session_state.get(k, "")
        st.session_state[f"_saved_{k}"] = val

    # 4단계로 돌아올 때 저장된 값 복원 (위젯이 다시 렌더되므로 key에 재설정)
    if step == 4:
        for k in _NARRATIVE_KEYS:
            saved = st.session_state.get(f"_saved_{k}", "")
            if saved:
                st.session_state[k] = saved

    st.session_state.step = step


def _calc_stats():
    """통계를 계산하여 session_state에 저장한다.

    data_loader 모듈의 5개 함수를 호출하여 호서대 추이, 평균, 순위 변화,
    전년대비 증감, 비교군 데이터를 계산하고 session_state에 저장한다.
    데이터 로드 직후 또는 연도/필터 변경 시 호출해야 한다.

    Note:
        - 커스텀 비교군이 설정된 경우 (_custom_compare_group) 해당 목록을 사용한다.
        - 미설정 시 config.COMPARE_GROUP 기본값을 사용한다.
    """
    nat = st.session_state.national_df
    reg = st.session_state.regional_df
    year = st.session_state.selected_year
    cmp = st.session_state.get("_custom_compare_group", None)
    st.session_state.hoseo_trend = dl.get_hoseo_trend(nat, reg)
    st.session_state.averages = dl.get_averages(nat, reg, compare_group=cmp)
    st.session_state.rank_changes = dl.get_rank_changes(nat, reg)
    st.session_state.yoy_changes = dl.get_yoy_changes(reg, year)
    st.session_state.compare_data = dl.get_compare_group_data(nat, reg, year, compare_group=cmp)


# ===========================================================================
# 메인 라우터
# ===========================================================================

def render_research(step: int):
    """연구실적 분석 워크플로우를 렌더링한다.

    step 값에 따라 해당 단계의 UI를 렌더링한다.
    각 단계는 독립적인 _render_stepN() 함수로 분리되어 있다.

    Args:
        step: 현재 단계 (1~5)
    """
    if step == 1:
        _render_step1()
    elif step == 2:
        _render_step2()
    elif step == 3:
        _render_step3()
    elif step == 4:
        _render_step4()
    elif step == 5:
        _render_step5()


# ===========================================================================
# STEP 1: 전처리 + 데이터 설정
# ===========================================================================

def _render_step1():
    """1단계: 데이터 설정 화면을 렌더링한다.

    3개 데이터 소스 중 하나를 온보딩 카드로 선택한 뒤
    해당 소스의 상세 UI를 표시한다.

    데이터 소스:
        - "raw": 대학알리미 Raw Excel 업로드 → 전처리 실행
        - "csv": 전처리 완료된 CSV 2개 직접 업로드
        - "existing": 기존 output/ 폴더 CSV 사용 (로컬 전용)

    Note:
        - IS_CLOUD 환경에서는 "existing" 소스가 표시되지 않는다.
        - 전처리 스크립트는 _load_preprocessor()로 동적 임포트한다.
        - 클라우드 모드에서는 process_in_memory()로 메모리 내 전처리한다.
    """
    st.markdown(
        '<div class="ir-section-title">📂 1단계: 원시 데이터 전처리 / 데이터 설정</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ir-stat-banner">대학알리미 Raw Excel을 전처리하거나, '
        '이미 전처리된 CSV 파일을 불러옵니다.</div>',
        unsafe_allow_html=True,
    )

    # --- 온보딩 카드: 데이터 소스 선택 ---
    st.markdown(
        '<div style="margin-bottom:1rem;"><strong>데이터 소스를 선택하세요</strong></div>',
        unsafe_allow_html=True,
    )

    source = st.session_state.get("data_source", None)
    col1, col2, col3 = st.columns(3)

    # 카드 1: Raw Excel 전처리
    with col1:
        active1 = "active" if source == "raw" else ""
        st.markdown(
            f'<div class="ir-onboard-card {active1}">'
            '<div style="font-size:1.5rem;">🔧</div>'
            '<div style="font-weight:600;margin-top:0.5rem;">Raw Excel 전처리</div>'
            '<div style="font-size:0.8125rem;color:#71717A;margin-top:0.25rem;">'
            '대학알리미 원본 xlsx</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("선택", key="src_raw", use_container_width=True):
            st.session_state.data_source = "raw"
            st.rerun()

    # 카드 2: CSV 직접 업로드
    with col2:
        active2 = "active" if source == "csv" else ""
        st.markdown(
            f'<div class="ir-onboard-card {active2}">'
            '<div style="font-size:1.5rem;">📂</div>'
            '<div style="font-weight:600;margin-top:0.5rem;">CSV 직접 업로드</div>'
            '<div style="font-size:0.8125rem;color:#71717A;margin-top:0.25rem;">'
            '전처리 완료된 CSV 2개</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("선택", key="src_csv", use_container_width=True):
            st.session_state.data_source = "csv"
            st.rerun()

    # 카드 3: 기존 output/ 폴더 사용 (로컬 전용)
    with col3:
        if IS_CLOUD:
            # 클라우드에서는 비활성 카드로 표시
            st.markdown(
                '<div class="ir-onboard-card" style="opacity:0.4;">'
                '<div style="font-size:1.5rem;">📁</div>'
                '<div style="font-weight:600;margin-top:0.5rem;">기존 output/ 사용</div>'
                '<div style="font-size:0.8125rem;color:#71717A;margin-top:0.25rem;">'
                '클라우드에서는 사용 불가</div></div>',
                unsafe_allow_html=True,
            )
            st.button("선택", key="src_existing", disabled=True, use_container_width=True)
        else:
            active3 = "active" if source == "existing" else ""
            st.markdown(
                f'<div class="ir-onboard-card {active3}">'
                '<div style="font-size:1.5rem;">📁</div>'
                '<div style="font-weight:600;margin-top:0.5rem;">기존 output/ 사용</div>'
                '<div style="font-size:0.8125rem;color:#71717A;margin-top:0.25rem;">'
                '이미 생성된 CSV 파일</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("선택", key="src_existing", use_container_width=True):
                st.session_state.data_source = "existing"
                st.rerun()

    st.divider()

    # --- 선택된 소스에 따른 상세 UI ---
    if source == "raw":
        _render_source_raw()
    elif source == "csv":
        _render_source_csv()
    elif source == "existing":
        _render_source_existing()
    else:
        st.info("위에서 데이터 소스를 선택하세요.")

    # --- 데이터 필터링 (데이터 로드 후 표시) ---
    if st.session_state.get("data_loaded"):
        st.divider()
        _render_data_filter()

        # --- 하단 다음 단계 버튼 ---
        st.divider()
        _, _, col_next = st.columns([1, 4, 1])
        col_next.button(
            "다음: 통계 확인 →",
            type="primary",
            on_click=_go,
            args=(2,),
            use_container_width=True,
        )


def _render_data_filter():
    """데이터 필터링 UI를 렌더링한다.

    로드된 전체 데이터를 인터랙티브 테이블로 보여주고,
    체크박스로 분석에 포함할 대학을 직접 선택할 수 있다.

    필터 항목:
        - 분석 연도: 전체 연도 중 원하는 연도만 선택 (multiselect)
        - 기준 연도: 선택된 연도 중 보고서 기준 연도 (selectbox)
        - 충청권 대학 선택: 체크박스로 분석 포함/제외 (data_editor)
        - 비교 대학: 비교군 대학 커스텀 선택 (multiselect)

    Note:
        - 호서대학교는 항상 선택 상태 유지 (체크 해제 불가)
        - 필터가 변경되면 통계를 재계산한다
    """
    nat_df = st.session_state.national_df
    reg_df = st.session_state.regional_df

    if nat_df is None or reg_df is None:
        return

    # 원본 DataFrame 보관 (필터 변경 시 원본에서 다시 필터링)
    if "_raw_national_df" not in st.session_state:
        st.session_state["_raw_national_df"] = nat_df.copy()
        st.session_state["_raw_regional_df"] = reg_df.copy()

    # 필터링은 항상 원본 기준으로 수행
    nat_df = st.session_state["_raw_national_df"]
    reg_df = st.session_state["_raw_regional_df"]

    st.markdown(
        '<div class="ir-chart-card" style="margin-bottom:1rem;">'
        '<div class="ir-chart-header">'
        '<div class="ir-chart-title">🔍 데이터 필터링</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption("로드된 데이터에서 분석에 사용할 연도, 대학을 직접 선택하세요.")

    # ── 1. 연도 필터 ──────────────────────────────────────────────────────
    all_years = sorted(nat_df["연도"].unique().tolist())
    prev_years = st.session_state.get("_filter_years", all_years)
    prev_years = [y for y in prev_years if y in all_years] or all_years

    col_year, col_base = st.columns([3, 1])
    with col_year:
        selected_years = st.multiselect(
            "분석 연도 선택",
            options=all_years,
            default=prev_years,
            key="_filter_years_widget",
            help="분석에 포함할 연도를 선택하세요.",
        )
    with col_base:
        if selected_years:
            year_options = sorted(selected_years, reverse=True)
            prev_base = st.session_state.get("selected_year", year_options[0])
            default_idx = year_options.index(prev_base) if prev_base in year_options else 0
            base_year = st.selectbox(
                "기준 연도",
                options=year_options,
                index=default_idx,
                key="_filter_base_year",
                help="보고서 기준 연도",
            )
        else:
            st.warning("연도를 1개 이상 선택하세요.")
            base_year = None

    if not selected_years or not base_year:
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── 2. 충청권 대학 직접 선택 (체크박스 테이블) ─────────────────────────
    st.markdown("---")
    st.markdown("**충청권 대학 선택** — 분석에 포함할 대학을 체크하세요")
    st.caption(f"✅ {UNIVERSITY}는 분석 대상이므로 항상 포함됩니다.")

    # 기준 연도의 충청권 데이터로 대학 목록 생성
    reg_base = reg_df[reg_df["연도"] == base_year].sort_values("충청권순위")
    if reg_base.empty:
        # 기준 연도 데이터가 없으면 전체 연도에서 대학 목록 추출
        reg_base = reg_df[reg_df["연도"].isin(selected_years)].drop_duplicates("학교명").sort_values("학교명")

    # 이전 선택 상태 복원
    prev_selected_univs = st.session_state.get("_filter_selected_univs", None)

    # 체크박스용 DataFrame 구성
    univ_rows = []
    for _, row in reg_base.iterrows():
        name = row["학교명"]
        is_hoseo = (name == UNIVERSITY)
        # 이전 선택이 있으면 복원, 없으면 기본 비교군 + 호서대만 선택
        if prev_selected_univs is not None:
            checked = name in prev_selected_univs
        else:
            checked = name in COMPARE_GROUP
        univ_rows.append({
            "선택": True if is_hoseo else checked,
            "학교명": name,
            "전임교원수": int(row["전임교원수"]) if pd.notna(row.get("전임교원수")) else 0,
            "SCI/SCOPUS논문수": round(float(row["SCI/SCOPUS논문수"]), 1) if pd.notna(row.get("SCI/SCOPUS논문수")) else 0,
            "1인당논문수": round(float(row["1인당논문수"]), 4) if pd.notna(row.get("1인당논문수")) else 0,
            "충청권순위": int(row["충청권순위"]) if pd.notna(row.get("충청권순위")) else "-",
        })

    check_df = pd.DataFrame(univ_rows)

    # st.data_editor로 인터랙티브 테이블 표시
    edited_df = st.data_editor(
        check_df,
        column_config={
            "선택": st.column_config.CheckboxColumn(
                "선택",
                help="분석에 포함할 대학을 체크하세요",
                default=False,
                width="small",
            ),
            "학교명": st.column_config.TextColumn("학교명", disabled=True, width="medium"),
            "전임교원수": st.column_config.NumberColumn("전임교원수", disabled=True, format="%d명"),
            "SCI/SCOPUS논문수": st.column_config.NumberColumn("논문수", disabled=True, format="%.1f"),
            "1인당논문수": st.column_config.NumberColumn("1인당논문수", disabled=True, format="%.4f"),
            "충청권순위": st.column_config.TextColumn("충청권순위", disabled=True, width="small"),
        },
        disabled=["학교명", "전임교원수", "SCI/SCOPUS논문수", "1인당논문수", "충청권순위"],
        hide_index=True,
        use_container_width=True,
        key="_univ_selector",
    )

    # 호서대 강제 포함
    selected_univs = edited_df[edited_df["선택"] == True]["학교명"].tolist()  # noqa: E712
    if UNIVERSITY not in selected_univs:
        selected_univs.append(UNIVERSITY)

    selected_count = len(selected_univs)
    total_count = len(check_df)
    st.markdown(f"**{selected_count}개교 선택됨** / 전체 {total_count}개교")

    # ── 3. 비교군 선택 (선택된 대학 중에서) ────────────────────────────────
    st.markdown("---")
    st.markdown("**비교군 설정** — 선택된 대학 중 직접 비교할 대학을 지정하세요")
    st.caption("비교군은 평균 계산, 비교 차트에 사용됩니다.")

    compare_candidates = [u for u in selected_univs if u != UNIVERSITY]
    default_compare = [u for u in COMPARE_GROUP if u != UNIVERSITY and u in compare_candidates]
    prev_compare = st.session_state.get("_filter_compare", default_compare)
    prev_compare = [u for u in prev_compare if u in compare_candidates] or default_compare

    selected_compare = st.multiselect(
        f"비교군 대학 (기본: {COMPARE_GROUP_NAME})",
        options=compare_candidates,
        default=prev_compare,
        key="_filter_compare_widget",
        help=f"{UNIVERSITY}는 자동 포함. 직접 비교할 대학을 선택하세요.",
    )
    compare_group_final = list(set([UNIVERSITY] + selected_compare))

    # ── 4. 필터 요약 + 미리보기 ────────────────────────────────────────────
    st.markdown("---")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("분석 연도", f"{len(selected_years)}개")
    col_s2.metric("기준 연도", f"{base_year}년")
    col_s3.metric("충청권 대학", f"{selected_count}개교")
    col_s4.metric("비교군", f"{len(compare_group_final)}개교")

    # 연도 + 대학 필터 적용된 DataFrame
    filtered_nat = nat_df[nat_df["연도"].isin(selected_years)]
    filtered_reg = reg_df[
        (reg_df["연도"].isin(selected_years)) & (reg_df["학교명"].isin(selected_univs))
    ]

    with st.expander("📋 필터링된 데이터 미리보기", expanded=False):
        tab_reg, tab_nat = st.tabs(["충청권 데이터 (필터 적용)", "전국 데이터"])
        with tab_reg:
            st.dataframe(
                filtered_reg.sort_values(["연도", "충청권순위"]),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(f"총 {len(filtered_reg)}행 — {selected_count}개 대학 × {len(selected_years)}개 연도")
        with tab_nat:
            # 전국 데이터는 전체 유지 (전국 평균/순위 계산 필요)
            st.dataframe(
                filtered_nat.sort_values(["연도", "전국순위"]).head(50),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(f"총 {len(filtered_nat)}행 (전국 평균 계산을 위해 전체 유지, 상위 50행 표시)")

    # ── 5. 필터 적용 버튼 ──────────────────────────────────────────────────
    if st.button(
        "✅ 이 데이터로 분석 시작",
        type="primary",
        use_container_width=True,
        key="apply_filter",
    ):
        # 필터 상태 저장
        st.session_state["_filter_years"] = selected_years
        st.session_state["_filter_compare"] = selected_compare
        st.session_state["_filter_selected_univs"] = selected_univs
        st.session_state["_filter_compare_group"] = compare_group_final

        # 필터링된 DataFrame 적용
        # 전국 데이터: 연도만 필터 (전국 평균/순위 계산에 전체 대학 필요)
        st.session_state.national_df = filtered_nat
        # 충청권 데이터: 연도 + 선택된 대학만 필터
        st.session_state.regional_df = filtered_reg
        st.session_state.selected_year = base_year

        # 비교군 동적 변경
        st.session_state["_custom_compare_group"] = compare_group_final

        # 통계 재계산 + 차트 캐시 초기화
        _calc_stats()
        st.session_state.charts = {}
        st.success("✅ 필터 적용 완료!")
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def _render_source_raw():
    """1단계 - Raw Excel 전처리 소스 UI를 렌더링한다.

    로컬 환경에서는 Raw data/ 폴더의 기존 파일을 표시하고,
    업로드된 파일을 폴더에 저장할 수 있다. 전처리 실행 시
    파일시스템 기반으로 처리한다.

    클라우드 환경에서는 업로드된 파일을 메모리 내에서
    process_in_memory()로 직접 처리한다.
    """
    _RAW_DIR = Path.cwd() / "Raw data"

    st.markdown("**대학알리미에서 받은 Raw Excel 파일을 업로드하면 자동으로 전처리합니다.**")
    st.caption("파일명에 연도가 포함되어야 합니다. 예: `2024년_전임교원연구실적.xlsx`")

    # 로컬 환경: Raw data/ 폴더 관리 UI 표시
    if not IS_CLOUD:
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
        # 로컬 환경에서만 Raw data/ 폴더에 저장 버튼 표시
        if not IS_CLOUD:
            if st.button("💾 Raw data/ 에 저장", key="save_raw"):
                for uf in uploaded_raws:
                    save_path = _RAW_DIR / uf.name
                    save_path.write_bytes(uf.read())
                st.success(f"✅ {len(uploaded_raws)}개 파일 저장 완료 → Raw data/ 폴더")
                st.rerun()

    st.divider()

    if IS_CLOUD:
        # --- 클라우드 모드: 업로드된 파일을 메모리 내에서 전처리 ---
        if not uploaded_raws:
            st.warning("⚠️ 위에서 Raw Excel 파일을 업로드하세요.")
        else:
            if st.button("⚙️ 전처리 실행", type="primary", use_container_width=True, key="run_preprocess"):
                try:
                    with st.spinner("전처리 실행 중... (클라우드 모드)"):
                        mod = _load_preprocessor()
                        uploaded_dict = {f.name: f.getvalue() for f in uploaded_raws}
                        nat_df, reg_df = mod.process_in_memory(uploaded_dict)

                    st.session_state.national_df = nat_df
                    st.session_state.regional_df = reg_df
                    years = sorted(nat_df["연도"].unique().tolist(), reverse=True)
                    st.session_state.selected_year = years[0]
                    _calc_stats()
                    st.session_state["data_loaded"] = True
                    st.success("✅ 전처리 완료! (클라우드 모드)")
                    st.rerun()

                except Exception as e:
                    st.error(f"전처리 오류: {e}")
                    with st.expander("🔍 오류 상세"):
                        import traceback
                        st.code(traceback.format_exc())
    else:
        # --- 로컬 모드: 기존 방식 (파일시스템 기반) ---
        all_raws = sorted(_RAW_DIR.glob("*.xlsx"))
        if not all_raws:
            st.warning("⚠️ Raw data/ 폴더에 Excel 파일이 없습니다. 위에서 업로드하세요.")
        else:
            st.markdown(f"전처리 대상: **{len(all_raws)}개** 파일")
            for f in all_raws:
                st.markdown(f"  - `{f.name}`")

            if st.button("⚙️ 전처리 실행", type="primary", use_container_width=True, key="run_preprocess"):
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
                        st.session_state["data_loaded"] = True
                        st.success(f"📊 데이터 자동 로드 완료 — {years}년 데이터 준비됨")
                        if st.button("▶ 2단계 통계 확인으로 이동", type="primary"):
                            _go(2)
                            st.rerun()

                except Exception as e:
                    st.error(f"전처리 오류: {e}")
                    with st.expander("🔍 오류 상세"):
                        import traceback
                        st.code(traceback.format_exc())


def _render_source_csv():
    """1단계 - CSV 직접 업로드 소스 UI를 렌더링한다.

    전처리가 완료된 전체_대학_데이터.csv와 충청권_순위.csv를
    직접 업로드하여 분석에 사용한다.
    """
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
                st.session_state["data_loaded"] = True
                _go(2)
                st.rerun()
        except Exception as e:
            st.error(f"파일 읽기 오류: {e}")


def _render_source_existing():
    """1단계 - 기존 output/ 폴더 CSV 사용 소스 UI를 렌더링한다.

    output/ 폴더에 이미 존재하는 전체_대학_데이터.csv와
    충청권_순위.csv를 확인하고 바로 사용한다.
    로컬 환경에서만 사용 가능하다.

    Note:
        IS_CLOUD가 True이면 이 함수가 호출되지 않는다 (카드 비활성화).
    """
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
            st.session_state["data_loaded"] = True
            _go(2)
            st.rerun()
    else:
        missing = []
        if not nat_exists:
            missing.append("전체_대학_데이터.csv")
        if not reg_exists:
            missing.append("충청권_순위.csv")
        st.warning(f"⚠️ output/ 폴더에 파일 없음: {', '.join(missing)}")
        st.info("🔧 Raw Excel 전처리 소스에서 전처리를 먼저 실행하세요.")


# ===========================================================================
# STEP 2: 통계 확인
# ===========================================================================

def _render_step2():
    """2단계: 통계 확인 화면을 렌더링한다.

    호서대 핵심 지표를 메트릭 카드로 표시하고,
    연도별 상세/평균 비교/비교군 현황/전년대비 증감을 탭으로 구분하여 보여준다.

    메트릭 카드:
        - 1인당 논문수 (전년대비 증감률 포함)
        - 충청권 순위 (순위 변화 포함)
        - 전국 순위 (순위 변화 포함)
        - 전임교원수

    Note:
        - 순위 변화의 delta_type이 반전되어 있다(순위는 낮을수록 좋으므로).
          음수 변화(순위 하락) → "up" 표시, 양수 변화(순위 상승) → "down" 표시.
    """
    year = st.session_state.selected_year
    hoseo = st.session_state.hoseo_trend
    avgs = st.session_state.averages
    ranks = st.session_state.rank_changes
    yoy = st.session_state.yoy_changes
    cmpd = st.session_state.compare_data

    st.markdown(
        f'<div class="ir-section-title">📋 2단계: 통계 확인 — {year}년 기준</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ir-stat-banner">계산된 수치를 검토하세요. '
        '이상이 없으면 다음 단계로 진행합니다.</div>',
        unsafe_allow_html=True,
    )

    # --- 핵심 지표 메트릭 카드 ---
    if year in hoseo:
        d = hoseo[year]
        rc = ranks.get(year, {})

        # 순위 delta_type: 순위는 숫자가 작을수록 좋으므로
        # 음수 변화(순위 올라감) → "up", 양수 변화(순위 내려감) → "down"
        def _rank_delta_type(val):
            """순위 변화 값에 따른 delta_type을 결정한다. 순위는 inverse이므로 부호 반전."""
            if val is None or val == 0:
                return None
            return "up" if val < 0 else "down"

        metrics = [
            {
                "label": "1인당 논문수",
                "value": f"{d['1인당논문수']:.4f}",
                "delta": f"{yoy['호서']['증감률']:+.1f}%" if yoy.get("호서") else None,
                "delta_type": (
                    "up" if yoy.get("호서") and yoy["호서"]["증감률"] > 0
                    else "down" if yoy.get("호서") and yoy["호서"]["증감률"] < 0
                    else None
                ),
                "icon": "📝",
            },
            {
                "label": "충청권 순위",
                "value": f"{d['충청권순위']}위" if d.get("충청권순위") else "-",
                "delta": (
                    f"{rc.get('충청권순위_변화', 0):+d}계단"
                    if rc.get("충청권순위_변화") else None
                ),
                "delta_type": _rank_delta_type(rc.get("충청권순위_변화")),
                "icon": "🏅",
            },
            {
                "label": "전국 순위",
                "value": f"{d['전국순위']}위",
                "delta": (
                    f"{rc.get('전국순위_변화', 0):+d}계단"
                    if rc.get("전국순위_변화") else None
                ),
                "delta_type": _rank_delta_type(rc.get("전국순위_변화")),
                "icon": "🌐",
            },
            {
                "label": "전임교원수",
                "value": f"{d['전임교원수']:,}명",
                "delta": None,
                "delta_type": None,
                "icon": "👥",
            },
        ]
        render_metric_cards(metrics)

    st.divider()

    # --- 탭별 상세 데이터 ---
    tab_detail, tab_avg, tab_compare, tab_yoy = st.tabs([
        "📋 연도별 상세", "📊 평균 비교", "🏫 비교군 현황", "📈 전년대비 증감"
    ])

    with tab_detail:
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

    with tab_avg:
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

    with tab_compare:
        st.dataframe(pd.DataFrame(cmpd), use_container_width=True, hide_index=True)

    with tab_yoy:
        if yoy.get("상위") or yoy.get("하위"):
            col_top, col_bot = st.columns(2)
            with col_top:
                st.markdown("**📈 증감 상위 3개 대학**")
                st.dataframe(
                    pd.DataFrame(yoy.get("상위", [])),
                    use_container_width=True,
                    hide_index=True,
                )
            with col_bot:
                st.markdown("**📉 증감 하위 3개 대학**")
                st.dataframe(
                    pd.DataFrame(yoy.get("하위", [])),
                    use_container_width=True,
                    hide_index=True,
                )
            if yoy.get("호서"):
                st.info(
                    f"**{UNIVERSITY}**: {yoy['호서']['기준연도']:.4f} → "
                    f"{yoy['호서']['비교연도']:.4f}  "
                    f"증감률 **{yoy['호서']['증감률']:+.1f}%**"
                )
        else:
            st.info("전년도 데이터 없음")

    # --- 하단 이전/다음 버튼 ---
    st.divider()
    col_prev, _, col_next = st.columns([1, 4, 1])
    col_prev.button("← 1단계로", on_click=_go, args=(1,), use_container_width=True)
    col_next.button(
        "다음: 그래프 검토 →", type="primary",
        on_click=_go, args=(3,), use_container_width=True,
    )


# ===========================================================================
# STEP 3: 그래프 검토
# ===========================================================================

def _render_step3():
    """3단계: 그래프 검토 화면을 렌더링한다.

    5종 차트를 탭으로 구분하여 표시한다. 차트가 아직 생성되지 않았으면
    chart_generator 모듈을 호출하여 session_state에 캐시한다.

    차트 종류:
        - trend: 연도별 1인당논문수 추이 (호서 vs 전국/충청권/비교군 평균)
        - bar: 충청권 대학 전체 비교 막대차트
        - avg: 1인당논문수 평균 비교 수평 바차트
        - rank: 충청권/전국 순위 변화 추이
        - compare: 비교군 5개교 비교 막대차트

    Note:
        - render_chart_card() 컴포넌트를 사용하여 확대/저장 기능을 제공한다.
        - breakdown_df를 전달하여 차트 하단에 데이터 테이블을 표시한다.
    """
    year = st.session_state.selected_year
    hoseo = st.session_state.hoseo_trend
    avgs = st.session_state.averages
    ranks = st.session_state.rank_changes
    cmpd = st.session_state.compare_data
    reg_df = st.session_state.regional_df

    st.markdown(
        '<div class="ir-section-title">📈 3단계: 그래프 검토</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ir-stat-banner">5종 차트를 확인하세요. 보고서에 그대로 삽입됩니다.</div>',
        unsafe_allow_html=True,
    )

    # --- 차트 생성 (캐시) ---
    if not st.session_state.charts:
        with st.spinner("차트 생성 중..."):
            st.session_state.charts = {
                "trend": cg.create_trend_chart(hoseo, avgs),
                "bar": cg.create_comparison_bar(reg_df, year),
                "avg": cg.create_avg_comparison(hoseo, avgs, year),
                "rank": cg.create_rank_trend_chart(ranks),
                "compare": cg.create_compare_group_bar(cmpd, year),
            }

    charts = st.session_state.charts

    # --- Breakdown DataFrame 생성 ---
    # trend 차트: 연도별 호서/전국/충청권/비교군 평균
    trend_rows = []
    for y, a in sorted(avgs.items()):
        h = hoseo.get(y, {})
        trend_rows.append({
            "연도": y,
            f"{UNIVERSITY}": h.get("1인당논문수"),
            "전국 평균": a.get("전국평균"),
            "충청권 평균": a.get("충청권평균"),
            "비교군 평균": a.get("비교군평균"),
        })
    trend_df = pd.DataFrame(trend_rows) if trend_rows else None

    # bar 차트: 충청권 대학 순위 (해당 연도)
    bar_df = reg_df[reg_df["연도"] == year][
        ["학교명", "1인당논문수", "충청권순위"]
    ].sort_values("충청권순위") if "충청권순위" in reg_df.columns else None

    # avg 차트: 4개 비교값
    avg_data = avgs.get(year, {})
    h_data = hoseo.get(year, {})
    avg_df = pd.DataFrame([{
        f"{UNIVERSITY}": h_data.get("1인당논문수"),
        "전국 평균": avg_data.get("전국평균"),
        "충청권 평균": avg_data.get("충청권평균"),
        "비교군 평균": avg_data.get("비교군평균"),
    }]) if avg_data else None

    # rank 차트: 순위 변화
    rank_rows = []
    for y, r in sorted(ranks.items()):
        rank_rows.append({
            "연도": y,
            "충청권 순위": r.get("충청권순위"),
            "전국 순위": r.get("전국순위"),
            "충청권 변화": r.get("충청권순위_변화"),
            "전국 변화": r.get("전국순위_변화"),
        })
    rank_df = pd.DataFrame(rank_rows) if rank_rows else None

    # compare 차트: 비교군 5개교
    compare_df = pd.DataFrame(cmpd) if cmpd else None

    # --- 탭별 차트 표시 ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 연도별 추이", "🏫 충청권 비교", "📊 평균 비교",
        "🏆 순위 변화", "🔍 비교군",
    ])

    with tab1:
        render_chart_card(
            title="연도별 1인당논문수 추이",
            subtitle="호서대 vs 전국/충청권/비교군 평균",
            chart_buf=charts["trend"],
            breakdown_df=trend_df,
            chart_key="trend",
            year=year,
        )

    with tab2:
        render_chart_card(
            title=f"{year}년 충청권 대학 비교",
            subtitle="충청권 대학 1인당논문수 전체 비교",
            chart_buf=charts["bar"],
            breakdown_df=bar_df,
            chart_key="bar",
            year=year,
        )

    with tab3:
        render_chart_card(
            title=f"{year}년 1인당논문수 평균 비교",
            subtitle="전국/충청권/비교군 평균 대비 호서대 위치",
            chart_buf=charts["avg"],
            breakdown_df=avg_df,
            chart_key="avg",
            year=year,
        )

    with tab4:
        render_chart_card(
            title="충청권/전국 순위 변화 추이",
            subtitle="연도별 순위 변동 추이",
            chart_buf=charts["rank"],
            breakdown_df=rank_df,
            chart_key="rank",
            year=year,
        )

    with tab5:
        render_chart_card(
            title=f"{year}년 비교군 5개교 비교",
            subtitle="천안·아산 5개 대학 1인당논문수 비교",
            chart_buf=charts["compare"],
            breakdown_df=compare_df,
            chart_key="compare",
            year=year,
        )

    # --- 하단 이전/다음 버튼 ---
    st.divider()
    col_prev, _, col_next = st.columns([1, 4, 1])
    col_prev.button("← 2단계로", on_click=_go, args=(2,), use_container_width=True)
    col_next.button(
        "다음: GPT 서술 →", type="primary",
        on_click=_go, args=(4,), use_container_width=True,
    )


# ===========================================================================
# STEP 4: GPT 서술 생성 및 편집
# ===========================================================================

def _render_step4():
    """4단계: GPT 서술 생성 및 편집 화면을 렌더링한다.

    4개 섹션별로 GPT 서술을 자동 생성하거나 직접 편집할 수 있다.
    render_gpt_section() 컴포넌트를 사용하며, @st.fragment로
    개별 섹션만 부분 리렌더링된다.

    섹션 구성:
        1. 연도별 1인당논문수 추이
        2. 전국/충청권/비교군 평균 비교
        3. 충청권 순위 변화
        4. 전년대비 증감

    Note:
        - API Key가 없으면 st.stop()으로 중단한다.
        - 전체 일괄 생성 버튼은 progress bar와 함께 4개 섹션을 순차 처리한다.
        - text_area의 key= 파라미터만 사용하고 value= 혼용 금지 (GPT 결과 갱신 이슈).
    """
    year = st.session_state.selected_year
    hoseo = st.session_state.hoseo_trend
    avgs = st.session_state.averages
    ranks = st.session_state.rank_changes
    yoy = st.session_state.yoy_changes
    cmpd = st.session_state.compare_data

    st.markdown(
        '<div class="ir-section-title">🤖 4단계: GPT 서술 생성 및 편집</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ir-stat-banner">각 섹션의 <strong>[🤖 GPT 생성]</strong> 버튼을 누르면 '
        'AI가 보고서 텍스트를 자동 작성합니다. 생성 후 직접 편집도 가능합니다.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.api_key:
        st.error("⛔ 사이드바에서 OpenAI API Key를 입력하고 [💾 저장] 버튼을 누르세요.")
        st.stop()

    client = OpenAI(api_key=st.session_state.api_key)

    # --- 전체 일괄 생성 버튼 ---
    if st.button("🤖 전체 섹션 일괄 생성", type="primary", use_container_width=True, key="gen_all"):
        progress = st.progress(0, "GPT 서술 생성 준비 중...")
        sections = [
            ("narrative_trend", gpt.generate_trend_narrative, (client, hoseo, avgs)),
            ("narrative_comparison", gpt.generate_comparison_narrative, (client, cmpd, avgs, year)),
            ("narrative_regional", gpt.generate_regional_narrative, (client, hoseo, ranks)),
            ("narrative_yoy", gpt.generate_yoy_narrative, (client, yoy, year)),
        ]
        _gen_ok = False
        try:
            for i, (key, fn, args) in enumerate(sections):
                if not st.session_state.get(key):
                    progress.progress((i + 1) / 4, f"섹션 {i + 1}/4 생성 중...")
                    st.session_state[key] = fn(*args)
            _gen_ok = True
        except Exception as e:
            st.error(f"GPT 오류: {e}")
        progress.empty()
        if _gen_ok:
            st.rerun()

    st.divider()

    # --- 섹션 1: 연도별 추이 ---
    render_gpt_section(
        section_key="narrative_trend",
        title="섹션 1. 연도별 1인당논문수 추이",
        hint="연도별 호서대 수치 변화 및 평균 대비 분석",
        generate_fn=gpt.generate_trend_narrative,
        generate_args=(client, hoseo, avgs),
    )

    # --- 섹션 2: 평균 비교 ---
    render_gpt_section(
        section_key="narrative_comparison",
        title=f"섹션 2. 전국·충청권·비교군 평균 비교 ({year}년)",
        hint="전국/충청권/비교군 평균 대비 호서대 위치 분석",
        generate_fn=gpt.generate_comparison_narrative,
        generate_args=(client, cmpd, avgs, year),
    )

    # --- 섹션 3: 충청권 순위 ---
    render_gpt_section(
        section_key="narrative_regional",
        title="섹션 3. 충청권 순위 변화",
        hint="충청권·전국 순위 추이 및 순위 변동 해석",
        generate_fn=gpt.generate_regional_narrative,
        generate_args=(client, hoseo, ranks),
    )

    # --- 섹션 4: 전년대비 증감 ---
    render_gpt_section(
        section_key="narrative_yoy",
        title=f"섹션 4. 전년대비 증감 ({year - 1}→{year}년)",
        hint="충청권 대학별 증감률 및 호서대 변화 해석",
        generate_fn=gpt.generate_yoy_narrative,
        generate_args=(client, yoy, year),
    )

    st.divider()

    # --- 완료 상태 요약 ---
    filled_count = sum([
        bool(st.session_state.get("narrative_trend")),
        bool(st.session_state.get("narrative_comparison")),
        bool(st.session_state.get("narrative_regional")),
        bool(st.session_state.get("narrative_yoy")),
    ])
    if filled_count < 4:
        st.warning(
            f"서술 작성 현황: **{filled_count}/4** 섹션 완료. "
            "빈 섹션은 보고서에서 생략됩니다."
        )
    else:
        st.success("✅ 4개 섹션 모두 완료! 다음 단계로 진행하세요.")

    # --- 하단 이전/다음 버튼 ---
    col_prev, _, col_next = st.columns([1, 4, 1])
    col_prev.button("← 3단계로", on_click=_go, args=(3,), use_container_width=True)
    col_next.button(
        "다음: 보고서 생성 →", type="primary",
        on_click=_go, args=(5,), use_container_width=True,
    )


# ===========================================================================
# STEP 5: 보고서 최종 생성
# ===========================================================================

def _render_step5():
    """5단계: 보고서 최종 생성 화면을 렌더링한다.

    Word 보고서를 생성하고 다운로드할 수 있다.
    _saved_ 접두사 키에서 narrative 텍스트를 복원하여 사용한다
    (4단계 text_area 위젯 키는 5단계에서 Streamlit이 삭제하므로).

    보고서 구성:
        - 표지: 대학명, 제목, 기준연도, 생성일
        - 섹션 1~4: GPT 서술 + 수치표 + 차트
        - 비교군 현황 테이블

    Note:
        - 클라우드 환경에서는 파일시스템 디렉터리 생성을 건너뛴다 (BytesIO 반환).
        - buf.getvalue()로 다운로드 데이터를 전달한다 (buf.read() 금지).
    """
    year = st.session_state.selected_year
    hoseo = st.session_state.hoseo_trend
    avgs = st.session_state.averages
    ranks = st.session_state.rank_changes
    yoy = st.session_state.yoy_changes
    cmpd = st.session_state.compare_data
    charts = st.session_state.charts

    # _saved_ 키에서 읽기 (위젯 키는 5단계에서 Streamlit이 삭제하므로)
    narratives = {
        "trend": st.session_state.get(
            "_saved_narrative_trend", st.session_state.get("narrative_trend", "")
        ),
        "comparison": st.session_state.get(
            "_saved_narrative_comparison", st.session_state.get("narrative_comparison", "")
        ),
        "regional": st.session_state.get(
            "_saved_narrative_regional", st.session_state.get("narrative_regional", "")
        ),
        "yoy": st.session_state.get(
            "_saved_narrative_yoy", st.session_state.get("narrative_yoy", "")
        ),
    }

    st.markdown(
        '<div class="ir-section-title">📄 5단계: 보고서 최종 생성</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ir-stat-banner">아래 내용을 최종 확인 후 Word 파일을 생성하세요.</div>',
        unsafe_allow_html=True,
    )

    # --- 포함 내용 확인 ---
    with st.expander("📋 포함 내용 확인", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**기본 정보**")
            st.markdown(f"- 대학: **{UNIVERSITY}**")
            st.markdown(f"- 기준 연도: **{year}년**")
            st.markdown(f"- 그래프: **{len([c for c in charts.values() if c])}종**")
        with col_b:
            st.markdown("**GPT 서술 포함 여부**")
            for lbl, key in [
                ("연도별 추이", "trend"),
                ("비교군 분석", "comparison"),
                ("충청권 순위", "regional"),
                ("전년대비 증감", "yoy"),
            ]:
                icon = "✅" if narratives[key] else "⬜"
                st.markdown(f"- {icon} {lbl}")

    # --- Word 보고서 생성 버튼 ---
    if st.button("📄 Word 보고서 생성", type="primary", use_container_width=True):
        progress = st.progress(0, "Word 파일 생성 준비 중...")
        try:
            progress.progress(0.3, "보고서 조립 중...")
            # 클라우드 환경에서는 파일시스템 디렉터리 생성 불필요 (BytesIO 반환)
            if not IS_CLOUD:
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
            progress.progress(1.0, "완료!")
            st.session_state.report_buf = buf
        except Exception as e:
            st.error(f"오류 발생: {e}")
        progress.empty()

    # --- 보고서 생성 완료 시 ---
    if st.session_state.get("report_buf"):
        fname = f"{UNIVERSITY}_연구실적_보고서_{year}.docx"

        # 성공 카드
        st.markdown(
            f"""
            <div class="ir-success-card">
                <div class="ir-success-icon">✅</div>
                <div class="ir-success-title">보고서가 성공적으로 생성되었습니다!</div>
                <div style="font-size:0.875rem; color:#71717A; margin-top:0.5rem;">
                    📄 {fname} · {year}년 기준 · 5개 섹션 포함
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.session_state.report_buf.seek(0)
        st.download_button(
            label=f"⬇️ {fname} 다운로드",
            data=st.session_state.report_buf,
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
        )

    # --- 하단 이전/처음부터 버튼 ---
    st.divider()
    col_prev, _, col_restart = st.columns([1, 3, 1])
    col_prev.button("← 4단계로", on_click=_go, args=(4,), use_container_width=True)
    if col_restart.button("🔄 처음부터", use_container_width=True):
        # 기본값으로 초기화 — step, 데이터, 차트, 서술 모두 리셋
        reset_keys = {
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
            "report_buf": None,
            "data_loaded": False,
            "data_source": None,
            "_raw_national_df": None,
            "_raw_regional_df": None,
            "_filter_years": None,
            "_filter_compare": None,
            "_custom_compare_group": None,
        }
        for k, v in reset_keys.items():
            st.session_state[k] = v
        st.rerun()
