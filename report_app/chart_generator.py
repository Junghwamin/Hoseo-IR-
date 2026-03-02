"""
그래프 생성 모듈 (matplotlib)

각 함수는 BytesIO 이미지 객체를 반환한다 (Word 파일 삽입 및 Streamlit 미리보기용).
"""

from __future__ import annotations

from io import BytesIO

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

from report_app.config import COMPARE_GROUP, UNIVERSITY

# 한글 폰트 설정 (OS별 자동 감지)
import platform as _platform
import matplotlib.font_manager as _fm

def _setup_korean_font():
    """OS별 한글 폰트를 자동 감지하여 설정한다."""
    system = _platform.system()
    if system == "Windows":
        font_name = "Malgun Gothic"
    elif system == "Darwin":  # macOS
        available = {f.name for f in _fm.fontManager.ttflist}
        if "Apple SD Gothic Neo" in available:
            font_name = "Apple SD Gothic Neo"
        else:
            font_name = "AppleGothic"
    else:  # Linux
        font_name = "NanumGothic"
    matplotlib.rcParams["font.family"] = font_name
    matplotlib.rcParams["axes.unicode_minus"] = False

_setup_korean_font()

# 색상 팔레트
COLOR_HOSEO = "#1f77b4"      # 호서대 강조 파란색
COLOR_OTHERS = "#aec7e8"     # 기타 연한 파란색
COLOR_NATIONAL = "#ff7f0e"   # 전국 주황
COLOR_REGIONAL = "#2ca02c"   # 충청권 초록
COLOR_COMPARE = "#9467bd"    # 비교군 보라


def _save_fig(fig: plt.Figure) -> BytesIO:
    """Figure를 PNG BytesIO로 저장하고 반환한다."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf


# ---------------------------------------------------------------------------
# 1. 연도별 1인당논문수 추이 라인차트
# ---------------------------------------------------------------------------

def create_trend_chart(
    hoseo_trend: dict[int, dict],
    averages: dict[int, dict],
) -> BytesIO:
    """
    호서대 vs 전국·충청권·비교군 평균의 연도별 1인당논문수 추이 라인차트.

    Args:
        hoseo_trend: get_hoseo_trend() 반환값
        averages: get_averages() 반환값
    """
    years = sorted(hoseo_trend.keys())
    hoseo_vals = [hoseo_trend[y]["1인당논문수"] for y in years]
    nat_avg = [averages[y]["전국평균"] for y in years]
    reg_avg = [averages[y]["충청권평균"] for y in years]
    cmp_avg = [averages[y]["비교군평균"] for y in years]

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(years, hoseo_vals, "o-", color=COLOR_HOSEO, linewidth=2.5, markersize=7, label=UNIVERSITY, zorder=5)
    ax.plot(years, nat_avg, "s--", color=COLOR_NATIONAL, linewidth=1.5, markersize=5, label="전국 평균", alpha=0.8)
    ax.plot(years, reg_avg, "^--", color=COLOR_REGIONAL, linewidth=1.5, markersize=5, label="충청권 평균", alpha=0.8)
    ax.plot(years, cmp_avg, "D--", color=COLOR_COMPARE, linewidth=1.5, markersize=5, label=f"{UNIVERSITY[:-2]}비교군 평균", alpha=0.8)

    # 데이터 레이블 (호서대만)
    for x, y in zip(years, hoseo_vals):
        ax.annotate(f"{y:.4f}", (x, y), textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=9, color=COLOR_HOSEO, fontweight="bold")

    ax.set_title("전임교원 1인당 SCI/SCOPUS 논문수 연도별 추이", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("연도", fontsize=11)
    ax.set_ylabel("1인당 논문수 (편)", fontsize=11)
    ax.set_xticks(years)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.4f"))
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_facecolor("#f9f9f9")
    fig.tight_layout()

    return _save_fig(fig)


# ---------------------------------------------------------------------------
# 2. 충청권 최신연도 막대차트
# ---------------------------------------------------------------------------

def create_comparison_bar(
    regional_df: pd.DataFrame,
    year: int,
) -> BytesIO:
    """
    충청권 대학의 1인당논문수 막대차트 (호서대 강조).

    Args:
        regional_df: 충청권_순위.csv 전체 DataFrame
        year: 기준 연도
    """
    df_year = regional_df[regional_df["연도"] == year].sort_values("1인당논문수", ascending=False)

    names = df_year["학교명"].tolist()
    values = df_year["1인당논문수"].tolist()
    colors = [COLOR_HOSEO if n == UNIVERSITY else COLOR_OTHERS for n in names]

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(names, values, color=colors, edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.002,
            f"{val:.4f}",
            ha="center", va="bottom", fontsize=8,
        )

    ax.set_title(f"{year}년 충청권 대학 전임교원 1인당 SCI/SCOPUS 논문수", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("1인당 논문수 (편)", fontsize=11)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_facecolor("#f9f9f9")
    fig.tight_layout()

    return _save_fig(fig)


# ---------------------------------------------------------------------------
# 3. 호서대 vs 전국/충청권/비교군 평균 비교 바차트
# ---------------------------------------------------------------------------

def create_avg_comparison(
    hoseo_trend: dict[int, dict],
    averages: dict[int, dict],
    year: int,
) -> BytesIO:
    """
    특정 연도에서 호서대 vs 전국/충청권/비교군 평균 수평 바차트.
    """
    hoseo_val = hoseo_trend[year]["1인당논문수"]
    nat_val = averages[year]["전국평균"]
    reg_val = averages[year]["충청권평균"]
    cmp_val = averages[year]["비교군평균"]

    labels = [UNIVERSITY, "전국 평균", "충청권 평균", "비교군 평균"]
    values = [hoseo_val, nat_val, reg_val, cmp_val]
    colors = [COLOR_HOSEO, COLOR_NATIONAL, COLOR_REGIONAL, COLOR_COMPARE]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.barh(labels, values, color=colors, height=0.5, edgecolor="white")

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + 0.001,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.4f}",
            va="center", ha="left", fontsize=10,
        )

    ax.set_title(f"{year}년 1인당 논문수 평균 비교", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("1인당 논문수 (편)", fontsize=11)
    ax.set_xlim(0, max(values) * 1.3)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.set_facecolor("#f9f9f9")
    fig.tight_layout()

    return _save_fig(fig)


# ---------------------------------------------------------------------------
# 4. 충청권·전국 순위 변화 라인차트
# ---------------------------------------------------------------------------

def create_rank_trend_chart(rank_changes: dict[int, dict]) -> BytesIO:
    """
    호서대의 충청권·전국 순위 연도별 변화 라인차트.
    순위는 낮을수록 좋으므로 Y축을 역전시킨다.

    Args:
        rank_changes: get_rank_changes() 반환값
    """
    years = sorted(rank_changes.keys())
    reg_ranks = [rank_changes[y]["충청권순위"] for y in years]
    nat_ranks = [rank_changes[y]["전국순위"] for y in years]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # 충청권 순위
    ax1.plot(years, reg_ranks, "o-", color=COLOR_REGIONAL, linewidth=2.5, markersize=8)
    for x, y in zip(years, reg_ranks):
        ax1.annotate(f"{y}위", (x, y), textcoords="offset points", xytext=(0, 10),
                     ha="center", fontsize=10, color=COLOR_REGIONAL, fontweight="bold")
    ax1.set_title(f"{UNIVERSITY} 충청권 순위 변화", fontsize=12, fontweight="bold")
    ax1.set_xlabel("연도")
    ax1.set_ylabel("충청권 순위")
    ax1.invert_yaxis()
    ax1.set_xticks(years)
    ax1.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax1.grid(linestyle="--", alpha=0.4)
    ax1.set_facecolor("#f9f9f9")

    # 전국 순위
    ax2.plot(years, nat_ranks, "o-", color=COLOR_NATIONAL, linewidth=2.5, markersize=8)
    for x, y in zip(years, nat_ranks):
        ax2.annotate(f"{y}위", (x, y), textcoords="offset points", xytext=(0, 10),
                     ha="center", fontsize=10, color=COLOR_NATIONAL, fontweight="bold")
    ax2.set_title(f"{UNIVERSITY} 전국 순위 변화", fontsize=12, fontweight="bold")
    ax2.set_xlabel("연도")
    ax2.set_ylabel("전국 순위")
    ax2.invert_yaxis()
    ax2.set_xticks(years)
    ax2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax2.grid(linestyle="--", alpha=0.4)
    ax2.set_facecolor("#f9f9f9")

    fig.suptitle(f"{UNIVERSITY} 순위 추이", fontsize=13, fontweight="bold")
    fig.tight_layout()

    return _save_fig(fig)


# ---------------------------------------------------------------------------
# 5. 비교군 막대차트 (비교 5개교)
# ---------------------------------------------------------------------------

def create_compare_group_bar(
    compare_data: list[dict],
    year: int,
) -> BytesIO:
    """
    비교 5개 대학의 1인당논문수 비교 막대차트.

    Args:
        compare_data: get_compare_group_data() 반환값
        year: 기준 연도
    """
    names = [d["학교명"] for d in compare_data]
    values = [d["1인당논문수"] for d in compare_data]
    colors = [COLOR_HOSEO if n == UNIVERSITY else COLOR_OTHERS for n in names]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(names, values, color=colors, edgecolor="white", linewidth=0.5, width=0.5)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.002,
            f"{val:.4f}",
            ha="center", va="bottom", fontsize=10,
        )

    ax.set_title(f"{year}년 {UNIVERSITY[:-2]}비교군 1인당 SCI/SCOPUS 논문수", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("1인당 논문수 (편)", fontsize=11)
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_facecolor("#f9f9f9")
    fig.tight_layout()

    return _save_fig(fig)
