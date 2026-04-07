# 호서대학교 정화민 - 연구실적 분석 포털

대학알리미 원시 데이터(Excel)를 자동 전처리하고, GPT-4o 기반 서술 생성 + matplotlib 차트 + python-docx Word 보고서를 자동 생성하는 **Streamlit 웹 앱**입니다.

## 주요 기능

- **원시 데이터 자동 전처리**: 대학알리미 Excel → 전임교원수, SCI/SCOPUS 논문수 추출, 캠퍼스 합산, 순위 산출
- **구형/신형 포맷 모두 지원**: 2016~2025년 대학알리미 엑셀 형식 자동 감지
- **5단계 Step-by-Step 워크플로우**: 데이터 설정 → 통계 확인 → 그래프 검토 → GPT 서술 → 보고서 생성
- **GPT-4o 서술 자동 생성**: 섹션별 분석 텍스트를 AI가 작성, 직접 편집 가능
- **차트 5종 자동 생성**: 연도별 추이, 평균 비교, 충청권 비교, 순위 변화, 비교군 현황
- **Word 보고서 자동 조립**: 표지 + 5개 섹션(표/차트/서술 포함) → `.docx` 다운로드

## 빠른 시작

### 설치

```bash
# Python 3.10 이상 필요
pip install -r requirements.txt
```

### 실행

```bash
# 프로젝트 루트에서 실행 (필수)
streamlit run report_app/app.py
```

또는 `start_app.bat` 더블클릭으로 바로 실행

브라우저에서 http://localhost:8501 접속

### API Key 설정

앱 사이드바에서 OpenAI API Key 입력 후 저장 버튼 클릭 (`.env`에 자동 저장)

## 앱 워크플로우 (5단계)

```
1단계: 전처리·데이터 설정
  ├─ [원시 데이터 전처리] 대학알리미 xlsx 업로드 → 전처리 실행 → CSV 자동 생성
  ├─ [전처리 결과 CSV 업로드] 이미 전처리된 CSV 직접 업로드
  └─ [기존 output/ 폴더 사용] 기존 CSV 파일 바로 사용

2단계: 통계 확인
  └─ 요약 카드, 연도별 수치표, 비교군 표, 전년대비 증감 검토

3단계: 그래프 검토
  └─ 5종 차트 탭별 확인 (PNG 개별 저장 가능)

4단계: GPT 서술 생성 및 편집
  └─ 섹션별 [GPT 생성] 버튼 → text_area에서 직접 편집

5단계: 보고서 생성
  └─ [Word 보고서 생성] → .docx 다운로드
```

## 생성 보고서 구조

| 섹션 | 내용 |
|------|------|
| 표지 | 대학명, 제목, 기준연도, 생성일 |
| 1. 연도별 추이 | GPT 서술 + 수치표 + 라인차트 |
| 2. 평균 비교 | GPT 서술 + 수평 바차트 |
| 3. 충청권 비교 | GPT 서술 + 막대차트 + 순위변화차트 |
| 4. 비교군 현황 | 5개교 비교표 + 막대차트 |
| 5. 전년대비 증감 | GPT 서술 + 증감 상위/하위 표 |

## 디렉토리 구조

```
Hoseo-IR-/
├── README.md                              ← 이 파일
├── requirements.txt                       ← Python 의존 라이브러리
├── start_app.bat                          ← 앱 바로 실행 런처
├── .env                                   ← OpenAI API Key (git 제외)
├── 전임교원_연구실적_전처리.py            ← 전처리 스크립트 (앱 내에서도 호출)
│
├── report_app/                            ← Streamlit 앱 모듈
│   ├── app.py                             ← 메인 앱 (5단계 워크플로우)
│   ├── config.py                          ← 대학명, 비교군, 경로, GPT 설정
│   ├── data_loader.py                     ← CSV 로드 + 통계 계산
│   ├── chart_generator.py                 ← matplotlib 차트 5종 생성
│   ├── gpt_reporter.py                    ← OpenAI API 섹션별 서술 생성
│   └── report_builder.py                  ← python-docx Word 보고서 조립
│
├── Raw data/                              ← 대학알리미 원본 Excel 파일
│   ├── 2016년_...xlsx ~ 2022년_...xlsx    ← 구형 포맷 (하위 헤더 없음)
│   └── 2023년_...xlsx ~ 2025년_...xlsx    ← 신형 포맷
│
├── config/                                ← 전처리 설정 파일
│   ├── universities.json                  ← 대학 정보 및 캠퍼스 매핑 (136개교)
│   └── regions.json                       ← 지역별 대학 리스트 (충청권 27개교)
│
└── output/                                ← 결과 파일 (자동 생성)
    ├── 전임교원_연구실적_전처리결과.xlsx
    ├── 전체_대학_데이터.csv
    ├── 충청권_순위.csv
    └── reports/                           ← 생성된 Word 보고서
```

## 데이터 구조

### `output/전체_대학_데이터.csv`

| 연도 | 학교명 | 전임교원수 | SCI/SCOPUS논문수 | 1인당논문수 | 전국순위 |
|------|--------|------------|-------------------|-------------|----------|

### `output/충청권_순위.csv`

| 연도 | 학교명 | 전임교원수 | SCI/SCOPUS논문수 | 1인당논문수 | 충청권순위 | 전국순위 |
|------|--------|------------|-------------------|-------------|------------|----------|

- 인코딩: UTF-8 with BOM (`utf-8-sig`)
- Raw 파일명 규칙: 파일명에 `YYYY년` 포함 필수

## 비교 대학군

천안·아산 5개 대학 (`config.py`에서 수정 가능):
- 순천향대학교, 선문대학교, 한서대학교, 나사렛대학교, **호서대학교**

## 전처리 스크립트 단독 실행

앱 없이 전처리만 실행할 수도 있습니다:

```bash
python 전임교원_연구실적_전처리.py
```

### 처리 과정

```
[1/5] 설정 파일 로드 (universities.json, regions.json)
[2/5] Raw 데이터 파일 스캔 (연도 패턴 자동 감지)
[3/5] 연도별 데이터 처리 (헤더 자동 탐지 → 필터링 → 캠퍼스 합산 → 1인당 계산)
[4/5] 순위 계산 (전국 + 충청권)
[5/5] 결과 저장 (Excel + CSV)
```

### 처리 규칙

- **대학 필터링**: 학교종류 "대학교"만 포함 (사이버대/전문대/원격대 제외)
- **캠퍼스 통합**: `universities.json`의 aliases 기반 자동 합산
- **분교 처리**: `is_branch: true` 설정 시 독립 대학으로 취급
- **컬럼 자동 감지**: 키워드 기반으로 헤더 위치 자동 탐지 (구형/신형 포맷 모두 지원)

## 기술 스택

| 라이브러리 | 용도 |
|---|---|
| streamlit | 웹 앱 프레임워크 |
| pandas | 데이터 처리 |
| openpyxl | Excel 읽기/쓰기 |
| matplotlib | 차트 생성 (Malgun Gothic 한글 폰트) |
| openai | GPT-4o 서술 생성 |
| python-docx | Word 보고서 조립 |
| python-dotenv | API Key 환경변수 관리 |

## 문제 해결

| 증상 | 해결 |
|------|------|
| matplotlib 한글 깨짐 | `rcParams["font.family"] = "Malgun Gothic"` (Windows) |
| CSV 한글 깨짐 | `encoding="utf-8-sig"` 사용 |
| 컬럼 탐지 실패 | 구형 포맷은 자동 폴백 지원, 그래도 실패 시 `find_columns()` 키워드 조정 |
| GPT-4o 미사용 계정 | `config.py`에서 `GPT_MODEL = "gpt-4"`로 변경 |
| Streamlit 실행 오류 | 반드시 프로젝트 루트에서 실행 |

## 라이선스 (License)

[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-blue.svg)](https://polyformproject.org/licenses/noncommercial/1.0.0)

**Copyright (c) 2026 정화민 (Junghwamin). All rights reserved.**

본 소프트웨어는 [PolyForm Noncommercial License 1.0.0](./LICENSE) 하에 배포됩니다.

- ✅ **허용**: 연구, 교육, 학술, 개인 학습, 비영리 기관 사용, 수정 및 재배포 (비상업적 목적에 한함)
- ❌ **금지**: 상업적 이용 (상업적 이익이나 금전적 보상을 주된 목적으로 하는 모든 사용)
- 📌 **인용 필수**: 본 코드를 사용한 연구물 발표 시 [`CITATION.cff`](./CITATION.cff)에 따른 인용 표기 요청

상업적 사용을 원하시는 경우 별도의 라이선스 협의가 필요합니다. [GitHub Issues](https://github.com/Junghwamin/Hoseo-IR-/issues)를 통해 문의해 주세요.

전체 라이선스 조항은 [`LICENSE`](./LICENSE) 및 [`NOTICE`](./NOTICE) 파일을 참조하시기 바랍니다.

---

This software is licensed under the [PolyForm Noncommercial License 1.0.0](./LICENSE).
Commercial use is strictly prohibited without prior written consent from the copyright holder.
