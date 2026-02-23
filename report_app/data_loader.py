"""
데이터 로드 및 통계 계산 모듈

충청권_순위.csv 및 전체_대학_데이터.csv 를 읽어
보고서에 필요한 각종 통계를 산출한다.
"""

from __future__ import annotations

import pandas as pd

from report_app.config import (
    COMPARE_GROUP,
    NATIONAL_CSV,
    REGIONAL_CSV,
    UNIVERSITY,
)


# ---------------------------------------------------------------------------
# 1. 기본 로드
# ---------------------------------------------------------------------------

def load_all_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    CSV 두 개를 읽어 (national_df, regional_df) 를 반환한다.

    Columns:
        national_df : 연도, 학교명, 전임교원수, SCI/SCOPUS논문수, 1인당논문수, 전국순위
        regional_df : 연도, 학교명, 전임교원수, SCI/SCOPUS논문수, 1인당논문수, 충청권순위, 전국순위
    """
    national_df = pd.read_csv(NATIONAL_CSV, encoding="utf-8-sig")
    regional_df = pd.read_csv(REGIONAL_CSV, encoding="utf-8-sig")
    return national_df, regional_df


# ---------------------------------------------------------------------------
# 2. 호서대 연도별 추이
# ---------------------------------------------------------------------------

def get_hoseo_trend(
    national_df: pd.DataFrame,
    regional_df: pd.DataFrame,
) -> dict[int, dict]:
    """
    호서대학교의 연도별 핵심 수치를 반환한다.

    Returns:
        {
            연도(int): {
                "논문수": float,
                "전임교원수": int,
                "1인당논문수": float,
                "충청권순위": int,
                "전국순위": int,
            },
            ...
        }
    """
    result: dict[int, dict] = {}

    national_hoseo = national_df[national_df["학교명"] == UNIVERSITY].copy()
    regional_hoseo = regional_df[regional_df["학교명"] == UNIVERSITY].copy()

    for _, row in national_hoseo.iterrows():
        year = int(row["연도"])
        result[year] = {
            "논문수": round(float(row["SCI/SCOPUS논문수"]), 2),
            "전임교원수": int(row["전임교원수"]),
            "1인당논문수": round(float(row["1인당논문수"]), 4),
            "충청권순위": None,
            "전국순위": int(row["전국순위"]),
        }

    for _, row in regional_hoseo.iterrows():
        year = int(row["연도"])
        if year in result:
            result[year]["충청권순위"] = int(row["충청권순위"])

    return dict(sorted(result.items()))


# ---------------------------------------------------------------------------
# 3. 전국 / 충청권 / 비교군 평균
# ---------------------------------------------------------------------------

def get_averages(
    national_df: pd.DataFrame,
    regional_df: pd.DataFrame,
) -> dict[int, dict]:
    """
    연도별 전국/충청권/비교군 1인당논문수 평균을 반환한다.

    Returns:
        {
            연도(int): {
                "전국평균": float,
                "충청권평균": float,
                "비교군평균": float,
            },
            ...
        }
    """
    result: dict[int, dict] = {}
    years = sorted(national_df["연도"].unique())

    for year in years:
        nat_year = national_df[national_df["연도"] == year]
        reg_year = regional_df[regional_df["연도"] == year]
        cmp_year = national_df[
            (national_df["연도"] == year) & (national_df["학교명"].isin(COMPARE_GROUP))
        ]

        result[int(year)] = {
            "전국평균": round(float(nat_year["1인당논문수"].mean()), 4),
            "충청권평균": round(float(reg_year["1인당논문수"].mean()), 4),
            "비교군평균": round(float(cmp_year["1인당논문수"].mean()), 4) if len(cmp_year) > 0 else 0.0,
        }

    return result


# ---------------------------------------------------------------------------
# 4. 충청권·전국 순위 변화
# ---------------------------------------------------------------------------

def get_rank_changes(
    national_df: pd.DataFrame,
    regional_df: pd.DataFrame,
) -> dict[int, dict]:
    """
    호서대학교의 연도별 충청권·전국 순위 및 전년대비 변화를 반환한다.

    Returns:
        {
            연도(int): {
                "충청권순위": int,
                "전국순위": int,
                "충청권순위_변화": int | None,   # 양수 = 상승, 음수 = 하락
                "전국순위_변화": int | None,
            },
            ...
        }
    """
    hoseo_nat = national_df[national_df["학교명"] == UNIVERSITY].sort_values("연도")
    hoseo_reg = regional_df[regional_df["학교명"] == UNIVERSITY].sort_values("연도")

    result: dict[int, dict] = {}
    prev_nat_rank: int | None = None
    prev_reg_rank: int | None = None

    nat_by_year = {int(r["연도"]): int(r["전국순위"]) for _, r in hoseo_nat.iterrows()}
    reg_by_year = {int(r["연도"]): int(r["충청권순위"]) for _, r in hoseo_reg.iterrows()}

    for year in sorted(nat_by_year.keys()):
        nat_rank = nat_by_year.get(year)
        reg_rank = reg_by_year.get(year)

        nat_change = (prev_nat_rank - nat_rank) if (prev_nat_rank is not None and nat_rank is not None) else None
        reg_change = (prev_reg_rank - reg_rank) if (prev_reg_rank is not None and reg_rank is not None) else None

        result[year] = {
            "충청권순위": reg_rank,
            "전국순위": nat_rank,
            "충청권순위_변화": reg_change,
            "전국순위_변화": nat_change,
        }

        prev_nat_rank = nat_rank
        prev_reg_rank = reg_rank

    return result


# ---------------------------------------------------------------------------
# 5. 전년대비 증감률 상위·하위 대학 (충청권 기준)
# ---------------------------------------------------------------------------

def get_yoy_changes(
    regional_df: pd.DataFrame,
    year: int,
) -> dict:
    """
    충청권 내 대학의 전년대비 1인당논문수 증감률을 계산하여
    상위 3개 / 하위 3개 대학을 반환한다.

    Returns:
        {
            "상위": [{"학교명": str, "증감률": float, "기준연도": float, "비교연도": float}, ...],
            "하위": [...],
            "호서": {"학교명": str, "증감률": float, "기준연도": float, "비교연도": float} | None,
        }
    """
    prev_year = year - 1
    cur = regional_df[regional_df["연도"] == year][["학교명", "1인당논문수"]].copy()
    prv = regional_df[regional_df["연도"] == prev_year][["학교명", "1인당논문수"]].copy()

    if cur.empty or prv.empty:
        return {"상위": [], "하위": [], "호서": None}

    merged = cur.merge(prv, on="학교명", suffixes=("_현재", "_이전"))
    merged["증감률"] = merged.apply(
        lambda r: round(
            (r["1인당논문수_현재"] - r["1인당논문수_이전"]) / r["1인당논문수_이전"] * 100, 1
        )
        if r["1인당논문수_이전"] > 0
        else 0.0,
        axis=1,
    )
    merged = merged.sort_values("증감률", ascending=False).reset_index(drop=True)

    def _row_to_dict(r) -> dict:
        return {
            "학교명": r["학교명"],
            "증감률": r["증감률"],
            "기준연도": round(float(r["1인당논문수_현재"]), 4),
            "비교연도": round(float(r["1인당논문수_이전"]), 4),
        }

    top3 = [_row_to_dict(r) for _, r in merged.head(3).iterrows()]
    bot3 = [_row_to_dict(r) for _, r in merged.tail(3).iterrows()]

    hoseo_rows = merged[merged["학교명"] == UNIVERSITY]
    hoseo = _row_to_dict(hoseo_rows.iloc[0]) if not hoseo_rows.empty else None

    return {"상위": top3, "하위": bot3, "호서": hoseo}


# ---------------------------------------------------------------------------
# 6. 비교군 최신 연도 데이터
# ---------------------------------------------------------------------------

def get_compare_group_data(
    national_df: pd.DataFrame,
    regional_df: pd.DataFrame,
    year: int,
) -> list[dict]:
    """
    비교 5개 대학의 특정 연도 데이터를 반환한다.

    Returns:
        [
            {
                "학교명": str,
                "전임교원수": int,
                "논문수": float,
                "1인당논문수": float,
                "전국순위": int,
                "충청권순위": int | None,
            },
            ...
        ]
    """
    nat_year = national_df[
        (national_df["연도"] == year) & (national_df["학교명"].isin(COMPARE_GROUP))
    ]
    reg_year = regional_df[
        (regional_df["연도"] == year) & (regional_df["학교명"].isin(COMPARE_GROUP))
    ]

    reg_rank_map = {
        r["학교명"]: int(r["충청권순위"])
        for _, r in reg_year.iterrows()
    }

    result = []
    for _, row in nat_year.iterrows():
        name = row["학교명"]
        result.append({
            "학교명": name,
            "전임교원수": int(row["전임교원수"]),
            "논문수": round(float(row["SCI/SCOPUS논문수"]), 2),
            "1인당논문수": round(float(row["1인당논문수"]), 4),
            "전국순위": int(row["전국순위"]),
            "충청권순위": reg_rank_map.get(name),
        })

    result.sort(key=lambda x: x["1인당논문수"], reverse=True)
    return result


# ---------------------------------------------------------------------------
# 7. 사용 가능 연도 목록
# ---------------------------------------------------------------------------

def get_available_years(national_df: pd.DataFrame) -> list[int]:
    """CSV에 존재하는 연도 목록을 반환한다."""
    return sorted(national_df["연도"].unique().tolist())
