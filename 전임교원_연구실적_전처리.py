"""
전임교원 연구실적 전처리 도구

대학알리미 원시 데이터(Excel)에서 전임교원수 및 SCI/SCOPUS 논문 실적을
추출하여 대학별로 정리하고, 전국 및 충청권 순위를 산출합니다.

사용법:
    python 전임교원_연구실적_전처리.py
"""

import io
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# 1. 설정 파일 로드
# ---------------------------------------------------------------------------
def load_config(config_dir: Path):
    """
    config/universities.json, config/regions.json을 읽어
    대학 리스트, 이름 매핑(alias -> canonical), 지역 정보를 반환한다.

    Returns:
        universities (list): 대학 정보 리스트 (name, aliases, is_branch)
        name_mapping (dict): {alias 또는 canonical -> canonical_name}
        regions (dict): {"충청권": [...], ...}
    """
    uni_path = config_dir / "universities.json"
    reg_path = config_dir / "regions.json"

    with open(uni_path, encoding="utf-8") as f:
        uni_data = json.load(f)

    with open(reg_path, encoding="utf-8") as f:
        reg_data = json.load(f)

    universities = uni_data["universities"]

    # alias -> canonical name 역매핑 구축
    name_mapping: dict[str, str] = {}
    for uni in universities:
        canonical = uni["name"]
        # canonical 이름 자체도 매핑에 포함
        name_mapping[canonical] = canonical
        for alias in uni.get("aliases", []):
            name_mapping[alias] = canonical

    # regions: description 키 제외, 지역명 -> 대학 리스트만 추출
    regions: dict[str, list[str]] = {}
    for key, value in reg_data.items():
        if key == "description":
            continue
        regions[key] = value

    return universities, name_mapping, regions


# ---------------------------------------------------------------------------
# 2. Raw 파일 스캔
# ---------------------------------------------------------------------------
def scan_raw_files(raw_dir: Path) -> dict[int, Path]:
    """
    raw_dir에서 *.xlsx 파일을 탐색하고 파일명에서 연도를 추출한다.

    macOS는 파일명을 NFD(분해형 유니코드)로 저장하므로,
    '년' 같은 한글이 자모로 분해되어 정규식 매칭이 실패할 수 있다.
    NFC 정규화를 적용하여 크로스플랫폼 호환성을 확보한다.

    Returns:
        {연도(int): 파일경로(Path)} - 연도 오름차순 정렬
    """
    year_files: dict[int, Path] = {}
    pattern = re.compile(r"(\d{4})년")

    for fpath in raw_dir.glob("*.xlsx"):
        # macOS NFD → NFC 정규화 (한글 자모 분해 방지)
        normalized_name = unicodedata.normalize("NFC", fpath.name)
        match = pattern.search(normalized_name)
        if match:
            year = int(match.group(1))
            year_files[year] = fpath

    # 연도 오름차순 정렬
    return dict(sorted(year_files.items()))


# ---------------------------------------------------------------------------
# 3. 컬럼 자동 탐지
# ---------------------------------------------------------------------------
def find_columns(df: pd.DataFrame) -> dict:
    """
    header=None으로 읽은 DataFrame에서 멀티레벨 헤더를 분석하여
    필요한 컬럼 인덱스와 데이터 시작 행을 찾는다.

    Returns:
        {
            "학교명": int,        # 학교명 컬럼 인덱스
            "학교종류": int,      # 학교종류 컬럼 인덱스
            "전임교원수": int,    # 전임교원수(계) 컬럼 인덱스
            "SCI논문수": int,     # SCI/SCOPUS 논문수(계) 컬럼 인덱스
            "data_start_row": int # 실제 데이터 시작 행
        }
    """
    n_rows = min(11, len(df))
    n_cols = df.shape[1]

    school_name_col = None
    school_type_col = None
    faculty_col = None
    sci_col = None

    # --- 학교종류, 학교명 찾기 (row 0~10 범위에서 키워드 검색) ---
    for row_idx in range(n_rows):
        for col_idx in range(n_cols):
            val = df.iloc[row_idx, col_idx]
            if pd.isna(val):
                continue
            val_str = str(val).replace("\n", "").strip()

            # 학교종류
            if school_type_col is None and "학교종류" in val_str:
                school_type_col = col_idx

            # 학교명: "학교"를 포함하되, "학교종류", "학교설립" 등은 제외
            if school_name_col is None:
                if val_str == "학교" or val_str == "학교명":
                    school_name_col = col_idx

    # --- 전임교원수(계) 찾기 ---
    # 전략: "전임" 또는 "전임교원"이 포함된 짧은 헤더 셀을 찾은 뒤,
    # 해당 컬럼 그룹에서 하위 헤더 row에 "계"가 있는 첫 번째 컬럼 선택.
    # 타이틀 행(row 0 등)의 긴 문자열은 제외하기 위해 길이 제한(20자)을 둔다.
    faculty_header_row = None
    faculty_header_col = None

    for row_idx in range(n_rows):
        for col_idx in range(n_cols):
            val = df.iloc[row_idx, col_idx]
            if pd.isna(val):
                continue
            val_str = str(val).replace("\n", "").strip()
            if (len(val_str) <= 20
                    and "전임" in val_str
                    and "교원" in val_str
                    and "1인당" not in val_str):
                faculty_header_row = row_idx
                faculty_header_col = col_idx
                break
        if faculty_header_row is not None:
            break

    if faculty_header_row is not None:
        # faculty_header_col부터 시작하여, 하위 row에서 "계"가 있는 첫 컬럼 탐색
        # 일반적으로 계/남/여 3개 그룹이므로, 바로 해당 col이 "계"
        for row_idx in range(faculty_header_row + 1, n_rows):
            for col_idx in range(faculty_header_col, min(faculty_header_col + 6, n_cols)):
                val = df.iloc[row_idx, col_idx]
                if pd.isna(val):
                    continue
                val_str = str(val).replace("\n", "").strip()
                if val_str == "계":
                    faculty_col = col_idx
                    break
            if faculty_col is not None:
                break

        # "계" 하위 헤더가 없는 구형 포맷(2016년 등)은
        # 헤더 컬럼 자체가 곧 데이터 컬럼이므로 그대로 사용
        if faculty_col is None:
            faculty_col = faculty_header_col

    # --- SCI/SCOPUS 논문수(계) 찾기 ---
    # "SCI" 또는 "SCOPUS"가 포함된 셀을 찾은 뒤,
    # 해당 컬럼 그룹의 하위 row에서 "계"인 첫 번째 컬럼 선택
    # 단, "1인당" 행은 제외
    sci_header_row = None
    sci_header_col = None

    for row_idx in range(n_rows):
        for col_idx in range(n_cols):
            val = df.iloc[row_idx, col_idx]
            if pd.isna(val):
                continue
            val_str = str(val).replace("\n", "").strip()
            # "SCI" 또는 "SCOPUS"가 포함된 짧은 헤더 셀 (타이틀 행 제외)
            if (len(val_str) <= 30
                    and ("SCI" in val_str or "SCOPUS" in val_str)):
                # 해당 컬럼 위쪽에 "1인당"이 있으면 skip
                is_per_capita = False
                for check_row in range(row_idx):
                    check_val = df.iloc[check_row, col_idx]
                    if pd.notna(check_val) and "1인당" in str(check_val):
                        is_per_capita = True
                        break
                if not is_per_capita:
                    sci_header_row = row_idx
                    sci_header_col = col_idx
                    break
        if sci_header_row is not None:
            break

    if sci_header_row is not None:
        # SCI 헤더 컬럼부터 시작해서, 하위 행에서 "계" 찾기
        for row_idx in range(sci_header_row + 1, n_rows):
            for col_idx in range(sci_header_col, min(sci_header_col + 6, n_cols)):
                val = df.iloc[row_idx, col_idx]
                if pd.isna(val):
                    continue
                val_str = str(val).replace("\n", "").strip()
                if val_str == "계":
                    sci_col = col_idx
                    break
            if sci_col is not None:
                break

        # "계" 하위 헤더가 없는 구형 포맷(2016년 등)은
        # SCI/SCOPUS 헤더 컬럼 자체가 곧 데이터 컬럼이므로 그대로 사용
        if sci_col is None:
            sci_col = sci_header_col

    # --- 데이터 시작 행 탐지 ---
    # 헤더 영역 이후, "대학교"/"대학" 값이 학교종류 컬럼에 나타나는 첫 행
    data_start_row = None
    search_start = max(faculty_header_row or 0, sci_header_row or 0, 5)

    for row_idx in range(search_start, min(search_start + 10, len(df))):
        # 학교명 컬럼에 실제 학교명이 있고, 학교종류에 "대학" 포함 여부 확인
        if school_name_col is not None:
            name_val = df.iloc[row_idx, school_name_col]
            if pd.notna(name_val):
                name_str = str(name_val).strip()
                # 실제 대학명은 보통 한글로 시작하고 "대학"을 포함
                if "대학" in name_str or (school_type_col is not None
                        and pd.notna(df.iloc[row_idx, school_type_col])
                        and "대학" in str(df.iloc[row_idx, school_type_col])):
                    data_start_row = row_idx
                    break

    # --- 검증 ---
    errors = []
    if school_name_col is None:
        errors.append("학교명 컬럼을 찾을 수 없습니다.")
    if school_type_col is None:
        errors.append("학교종류 컬럼을 찾을 수 없습니다.")
    if faculty_col is None:
        errors.append("전임교원수(계) 컬럼을 찾을 수 없습니다.")
    if sci_col is None:
        errors.append("SCI/SCOPUS 논문수(계) 컬럼을 찾을 수 없습니다.")
    if data_start_row is None:
        errors.append("데이터 시작 행을 찾을 수 없습니다.")

    if errors:
        # 디버그를 위해 헤더 영역의 모든 값을 출력
        header_info = []
        for row_idx in range(n_rows):
            for col_idx in range(n_cols):
                val = df.iloc[row_idx, col_idx]
                if pd.notna(val):
                    header_info.append(f"  Row {row_idx}, Col {col_idx}: {val}")
        header_dump = "\n".join(header_info)
        raise ValueError(
            "컬럼 탐지 실패:\n"
            + "\n".join(f"  - {e}" for e in errors)
            + f"\n\n헤더 영역 내용:\n{header_dump}"
        )

    return {
        "학교명": school_name_col,
        "학교종류": school_type_col,
        "전임교원수": faculty_col,
        "SCI논문수": sci_col,
        "data_start_row": data_start_row,
    }


# ---------------------------------------------------------------------------
# 4. Excel 읽기
# ---------------------------------------------------------------------------
def read_excel(file_path: Path) -> pd.DataFrame:
    """
    Excel 파일을 읽어 필요한 컬럼만 추출하고 정제된 DataFrame을 반환한다.
    """
    df_raw = pd.read_excel(file_path, header=None)
    cols = find_columns(df_raw)

    data_start = cols["data_start_row"]

    # 필요한 컬럼만 추출
    df = df_raw.iloc[data_start:, [
        cols["학교명"],
        cols["학교종류"],
        cols["전임교원수"],
        cols["SCI논문수"],
    ]].copy()

    df.columns = ["학교명", "학교종류", "전임교원수", "SCI논문수"]

    # 타입 변환
    df["학교명"] = df["학교명"].astype(str).str.strip()
    df["학교종류"] = df["학교종류"].astype(str).str.strip()
    df["전임교원수"] = pd.to_numeric(df["전임교원수"], errors="coerce").fillna(0.0)
    df["SCI논문수"] = pd.to_numeric(df["SCI논문수"], errors="coerce").fillna(0.0)

    df = df.reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# 5. 대학교만 필터링
# ---------------------------------------------------------------------------
def filter_universities(df: pd.DataFrame) -> pd.DataFrame:
    """학교종류가 '대학교'인 행만 남기고, 학교명이 NaN인 행을 제거한다."""
    df = df[df["학교종류"] == "대학교"].copy()
    df = df[df["학교명"].notna() & (df["학교명"] != "nan") & (df["학교명"] != "")].copy()
    df = df.reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# 6. 캠퍼스 합산 (merge)
# ---------------------------------------------------------------------------
def merge_campuses(df: pd.DataFrame, name_mapping: dict[str, str]) -> pd.DataFrame:
    """
    name_mapping을 사용해 각 학교명을 정규명(canonical name)으로 변환하고,
    동일 대학의 캠퍼스 데이터를 합산한다.
    매핑되지 않는 대학은 경고를 출력하고 제외한다.
    """
    canonical_names = []
    unmatched = set()

    for name in df["학교명"]:
        if name in name_mapping:
            canonical_names.append(name_mapping[name])
        else:
            canonical_names.append(None)
            unmatched.add(name)

    # 매칭되지 않은 대학 경고 출력
    for name in sorted(unmatched):
        print(f"  [경고] '{name}'이(가) universities.json에 없습니다. 결과에서 제외됩니다.")

    df = df.copy()
    df["정규명"] = canonical_names

    # 매칭되지 않은 행 제거
    df = df[df["정규명"].notna()].copy()

    # 동일 대학 캠퍼스 합산
    merged = df.groupby("정규명", as_index=False).agg(
        전임교원수=("전임교원수", "sum"),
        SCI논문수=("SCI논문수", "sum"),
    )
    merged = merged.rename(columns={"정규명": "학교명"})
    merged = merged.reset_index(drop=True)
    return merged


# ---------------------------------------------------------------------------
# 7. 1인당 논문수 계산
# ---------------------------------------------------------------------------
def calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """1인당논문수 = SCI논문수 / 전임교원수 (소수점 4자리 반올림)"""
    df = df.copy()
    df["1인당논문수"] = df.apply(
        lambda row: round(row["SCI논문수"] / row["전임교원수"], 4)
        if row["전임교원수"] > 0
        else 0.0,
        axis=1,
    )
    return df


# ---------------------------------------------------------------------------
# 8. 순위 계산
# ---------------------------------------------------------------------------
def calculate_rankings(
    df: pd.DataFrame, region_names: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    전국순위와 충청권순위를 계산한다.

    Args:
        df: 학교명, 전임교원수, SCI논문수, 1인당논문수 컬럼을 가진 DataFrame
        region_names: 충청권 대학 정규명 리스트

    Returns:
        (national_df, region_df)
        - national_df: 전국순위 포함
        - region_df: 충청권순위 + 전국순위 포함
    """
    national_df = df.copy()
    national_df["전국순위"] = national_df["1인당논문수"].rank(
        ascending=False, method="min"
    ).astype(int)

    # 충청권 대학 필터링
    region_df = national_df[national_df["학교명"].isin(region_names)].copy()
    region_df["충청권순위"] = region_df["1인당논문수"].rank(
        ascending=False, method="min"
    ).astype(int)

    # 정렬
    national_df = national_df.sort_values("전국순위").reset_index(drop=True)
    region_df = region_df.sort_values("충청권순위").reset_index(drop=True)

    return national_df, region_df


# ---------------------------------------------------------------------------
# 9. Excel 내보내기
# ---------------------------------------------------------------------------
def export_excel(
    all_national: list[tuple[int, pd.DataFrame]],
    all_region: list[tuple[int, pd.DataFrame]],
    output_path: Path,
):
    """
    전국 데이터와 충청권 데이터를 하나의 Excel 파일(2개 시트)로 저장한다.
    """
    # 전국 데이터 결합
    national_frames = []
    for year, ndf in all_national:
        tmp = ndf[["학교명", "전임교원수", "SCI논문수", "1인당논문수", "전국순위"]].copy()
        tmp.insert(0, "연도", year)
        national_frames.append(tmp)

    national_combined = pd.concat(national_frames, ignore_index=True)
    national_combined = national_combined.rename(columns={"SCI논문수": "SCI/SCOPUS논문수"})
    national_combined = national_combined.sort_values(
        ["연도", "전국순위"], ascending=[True, True]
    ).reset_index(drop=True)

    # 충청권 데이터 결합
    region_frames = []
    for year, rdf in all_region:
        tmp = rdf[["학교명", "전임교원수", "SCI논문수", "1인당논문수", "충청권순위", "전국순위"]].copy()
        tmp.insert(0, "연도", year)
        region_frames.append(tmp)

    region_combined = pd.concat(region_frames, ignore_index=True)
    region_combined = region_combined.rename(columns={"SCI논문수": "SCI/SCOPUS논문수"})
    region_combined = region_combined.sort_values(
        ["연도", "충청권순위"], ascending=[True, True]
    ).reset_index(drop=True)

    # Excel 파일 저장
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        national_combined.to_excel(writer, sheet_name="전체_대학_데이터", index=False)
        region_combined.to_excel(writer, sheet_name="충청권_순위", index=False)

    print(f"  Excel 저장 완료: {output_path}")


# ---------------------------------------------------------------------------
# 10. CSV 내보내기
# ---------------------------------------------------------------------------
def export_csv(
    all_national: list[tuple[int, pd.DataFrame]],
    all_region: list[tuple[int, pd.DataFrame]],
    output_dir: Path,
):
    """
    전국 데이터와 충청권 데이터를 CSV 파일로 저장한다.
    한국어 Excel 호환을 위해 UTF-8 with BOM(utf-8-sig)을 사용한다.
    """
    # 전국 데이터 결합
    national_frames = []
    for year, ndf in all_national:
        tmp = ndf[["학교명", "전임교원수", "SCI논문수", "1인당논문수", "전국순위"]].copy()
        tmp.insert(0, "연도", year)
        national_frames.append(tmp)

    national_combined = pd.concat(national_frames, ignore_index=True)
    national_combined = national_combined.rename(columns={"SCI논문수": "SCI/SCOPUS논문수"})
    national_combined = national_combined.sort_values(
        ["연도", "전국순위"], ascending=[True, True]
    ).reset_index(drop=True)

    # 충청권 데이터 결합
    region_frames = []
    for year, rdf in all_region:
        tmp = rdf[["학교명", "전임교원수", "SCI논문수", "1인당논문수", "충청권순위", "전국순위"]].copy()
        tmp.insert(0, "연도", year)
        region_frames.append(tmp)

    region_combined = pd.concat(region_frames, ignore_index=True)
    region_combined = region_combined.rename(columns={"SCI논문수": "SCI/SCOPUS논문수"})
    region_combined = region_combined.sort_values(
        ["연도", "충청권순위"], ascending=[True, True]
    ).reset_index(drop=True)

    # CSV 저장
    national_csv = output_dir / "전체_대학_데이터.csv"
    region_csv = output_dir / "충청권_순위.csv"

    national_combined.to_csv(national_csv, index=False, encoding="utf-8-sig")
    region_combined.to_csv(region_csv, index=False, encoding="utf-8-sig")

    print(f"  CSV 저장 완료: {national_csv}")
    print(f"  CSV 저장 완료: {region_csv}")


# ---------------------------------------------------------------------------
# 11. 인메모리 전처리 함수 (Streamlit Cloud용)
# ---------------------------------------------------------------------------
def process_in_memory(
    uploaded_files: dict[str, bytes],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    업로드된 Excel 파일들을 메모리 내에서 전처리하여 DataFrame을 반환한다.

    파일 시스템에 쓰기 없이 동작하므로 Streamlit Cloud에서 사용 가능하다.
    기존 main()의 파이프라인을 재사용하되, 파일 I/O를 BytesIO로 대체한다.

    처리 파이프라인:
        1. 파일명에서 연도 추출 (YYYY년 또는 YYYY_ 패턴)
        2. BytesIO를 통해 Excel 파싱 → 컬럼 자동 탐지
        3. 대학교 필터링 → 캠퍼스 합산 → 1인당 논문수 계산
        4. 전국순위 및 충청권순위 계산
        5. 연도별 결과를 통합하여 최종 DataFrame 반환

    Args:
        uploaded_files: {파일명(str): 파일내용(bytes)} 딕셔너리.
            파일명에 연도(YYYY년 또는 YYYY_)가 포함되어야 한다.
            예: {"2024년_전임교원.xlsx": b"...", "2023년_전임교원.xlsx": b"..."}

    Returns:
        (national_df, regional_df) 튜플.
        - national_df 컬럼: 연도, 학교명, 전임교원수, SCI/SCOPUS논문수, 1인당논문수, 전국순위
        - regional_df 컬럼: 연도, 학교명, 전임교원수, SCI/SCOPUS논문수, 1인당논문수, 충청권순위, 전국순위
        두 DataFrame 모두 UTF-8-sig CSV와 동일한 컬럼 구조를 가진다.

    Raises:
        ValueError: 파일명에서 연도를 추출할 수 없는 경우

    Note:
        - config/ 폴더는 읽기 전용으로 참조 (load_config 기존 동작 그대로)
        - export_csv(), export_excel() 호출 없음 (파일 쓰기 불필요)
        - 매핑 실패 대학은 경고 출력 후 결과에서 제외 (기존 merge_campuses 동작)
    """
    # config 디렉토리는 스크립트 위치 기준으로 결정 (읽기 전용, 기존 main()과 동일)
    config_dir = Path(__file__).parent / "config"

    # --- Step 1: 설정 파일 로드 ---
    universities, name_mapping, regions = load_config(config_dir)
    region_names = regions.get("충청권", [])

    # --- Step 2: 연도별 파일 파싱 및 전처리 ---
    year_data: dict[int, pd.DataFrame] = {}
    year_pattern = re.compile(r"(\d{4})(?:년|_)")

    for filename, file_bytes in uploaded_files.items():
        # macOS NFD → NFC 정규화 (한글 자모 분해 방지)
        normalized_name = unicodedata.normalize("NFC", filename)
        match = year_pattern.search(normalized_name)
        if not match:
            raise ValueError(
                f"파일명 '{filename}'에서 연도를 추출할 수 없습니다. "
                "파일명에 '2024년' 또는 '2024_' 형태의 연도가 포함되어야 합니다."
            )
        year = int(match.group(1))

        # BytesIO로 Excel 읽기 (파일 시스템 접근 없음)
        df_raw = pd.read_excel(io.BytesIO(file_bytes), header=None)
        cols = find_columns(df_raw)
        data_start = cols["data_start_row"]

        # 필요한 컬럼만 추출 (read_excel 내부 로직 인라인 재현)
        df = df_raw.iloc[data_start:, [
            cols["학교명"],
            cols["학교종류"],
            cols["전임교원수"],
            cols["SCI논문수"],
        ]].copy()
        df.columns = ["학교명", "학교종류", "전임교원수", "SCI논문수"]
        df["학교명"] = df["학교명"].astype(str).str.strip()
        df["학교종류"] = df["학교종류"].astype(str).str.strip()
        df["전임교원수"] = pd.to_numeric(df["전임교원수"], errors="coerce").fillna(0.0)
        df["SCI논문수"] = pd.to_numeric(df["SCI논문수"], errors="coerce").fillna(0.0)
        df = df.reset_index(drop=True)

        # 기존 함수 재사용: 필터링 → 캠퍼스 합산 → 1인당 논문수 계산
        df = filter_universities(df)
        df = merge_campuses(df, name_mapping)
        df = calculate_metrics(df)
        year_data[year] = df

    # --- Step 3: 순위 계산 ---
    all_national: list[tuple[int, pd.DataFrame]] = []
    all_region: list[tuple[int, pd.DataFrame]] = []

    for year in sorted(year_data.keys()):
        national_df, region_df = calculate_rankings(year_data[year], region_names)
        all_national.append((year, national_df))
        all_region.append((year, region_df))

    # --- Step 4: 연도별 결과 통합 (export_csv 내부 로직 재현, 쓰기 없음) ---
    national_frames = []
    for year, ndf in all_national:
        tmp = ndf[["학교명", "전임교원수", "SCI논문수", "1인당논문수", "전국순위"]].copy()
        tmp.insert(0, "연도", year)
        national_frames.append(tmp)

    national_combined = pd.concat(national_frames, ignore_index=True)
    national_combined = national_combined.rename(columns={"SCI논문수": "SCI/SCOPUS논문수"})
    national_combined = national_combined.sort_values(
        ["연도", "전국순위"], ascending=[True, True]
    ).reset_index(drop=True)

    region_frames = []
    for year, rdf in all_region:
        tmp = rdf[["학교명", "전임교원수", "SCI논문수", "1인당논문수", "충청권순위", "전국순위"]].copy()
        tmp.insert(0, "연도", year)
        region_frames.append(tmp)

    region_combined = pd.concat(region_frames, ignore_index=True)
    region_combined = region_combined.rename(columns={"SCI논문수": "SCI/SCOPUS논문수"})
    region_combined = region_combined.sort_values(
        ["연도", "충청권순위"], ascending=[True, True]
    ).reset_index(drop=True)

    return national_combined, region_combined


# ---------------------------------------------------------------------------
# 12. 메인 함수
# ---------------------------------------------------------------------------
def main():
    script_dir = Path(__file__).parent
    config_dir = script_dir / "config"    # config JSON은 코드와 함께 번들에 포함 (read-only OK)
    raw_dir = Path.cwd() / "Raw data"     # CWD 기준 (쓰기 가능)
    output_dir = Path.cwd() / "output"    # CWD 기준 (쓰기 가능)

    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("  전임교원 연구실적 전처리 도구")
    print("=" * 60)

    # --- 설정 로드 ---
    print("\n[1/5] 설정 파일 로드 중...")
    universities, name_mapping, regions = load_config(config_dir)
    print(f"  대학 수: {len(universities)}개")
    print(f"  이름 매핑: {len(name_mapping)}개 항목")
    print(f"  지역: {', '.join(regions.keys())}")

    # --- 파일 스캔 ---
    print(f"\n[2/5] Raw 데이터 파일 스캔 중... (경로: {raw_dir})")
    if not raw_dir.exists():
        print(f"  [오류] Raw data 폴더가 존재하지 않습니다: {raw_dir}")
        return
    all_xlsx = list(raw_dir.glob("*.xlsx"))
    print(f"  발견된 xlsx 파일: {len(all_xlsx)}개")
    for f in all_xlsx:
        print(f"    - {f.name}")
    year_files = scan_raw_files(raw_dir)
    if not year_files:
        print("  [오류] 파일명에서 연도(YYYY년)를 찾을 수 없습니다.")
        print("  파일명에 '2024년' 같은 연도가 포함되어야 합니다.")
        return
    for year, fpath in year_files.items():
        print(f"  {year}년: {fpath.name}")

    # --- 연도별 데이터 처리 ---
    print("\n[3/5] 연도별 데이터 처리 중...")
    year_data: dict[int, pd.DataFrame] = {}

    for year, fpath in year_files.items():
        print(f"\n  --- {year}년 데이터 처리 ---")
        print(f"  파일: {fpath.name}")

        df = read_excel(fpath)
        print(f"  전체 행 수: {len(df)}")

        df = filter_universities(df)
        print(f"  대학교 필터링 후: {len(df)}개")

        df = merge_campuses(df, name_mapping)
        print(f"  캠퍼스 합산 후: {len(df)}개 대학")

        df = calculate_metrics(df)
        year_data[year] = df

    # --- 순위 계산 ---
    print("\n[4/5] 순위 계산 중...")
    region_names = regions.get("충청권", [])
    print(f"  충청권 대학 수: {len(region_names)}개")

    all_national: list[tuple[int, pd.DataFrame]] = []
    all_region: list[tuple[int, pd.DataFrame]] = []

    for year in sorted(year_data.keys()):
        national_df, region_df = calculate_rankings(year_data[year], region_names)
        all_national.append((year, national_df))
        all_region.append((year, region_df))
        print(f"  {year}년: 전국 {len(national_df)}개 대학, 충청권 {len(region_df)}개 대학")

    # --- 결과 내보내기 ---
    print("\n[5/5] 결과 파일 저장 중...")
    excel_path = output_dir / "전임교원_연구실적_전처리결과.xlsx"
    export_excel(all_national, all_region, excel_path)
    export_csv(all_national, all_region, output_dir)

    # --- 요약 ---
    print("\n" + "=" * 60)
    print("  처리 완료!")
    print(f"  처리 연도: {len(year_data)}개년 ({min(year_data.keys())}~{max(year_data.keys())})")
    total_unis = set()
    for _, ndf in all_national:
        total_unis.update(ndf["학교명"].tolist())
    print(f"  처리 대학 수: {len(total_unis)}개")
    print(f"  출력 파일:")
    print(f"    - {excel_path}")
    print(f"    - {output_dir / '전체_대학_데이터.csv'}")
    print(f"    - {output_dir / '충청권_순위.csv'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
