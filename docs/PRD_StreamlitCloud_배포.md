# PRD: 호서대학교 IR센터 연구실적 분석 포털 - Streamlit Cloud 배포

**문서 버전:** 1.0
**작성일:** 2026-03-07
**상태:** Draft

---

## 1. 프로젝트 개요 및 목표

### 1.1 배경

호서대학교 IR센터는 전임교원 연구실적(SCI/SCOPUS 논문수) 데이터를 분석하고,
연도별 추이/충청권 비교/전국 순위 등의 통계를 자동으로 Word 보고서로 생성하는 Streamlit 앱을 운영 중이다.
현재 이 앱은 Windows 로컬 환경에서만 실행 가능하며, 타 PC 배포를 위해 PyInstaller 기반 빌드를 사용하고 있다.

### 1.2 목표

로컬 전용 앱을 **Streamlit Community Cloud**에 배포하여 다음 목표를 달성한다:

| 목표 | 설명 |
|------|------|
| **접근성 향상** | 설치 없이 웹 브라우저에서 즉시 사용 가능 |
| **유지보수 간소화** | GitHub 푸시만으로 자동 배포, PC별 빌드 불필요 |
| **협업 지원** | IR센터 내 복수 인원이 동시에 접근 가능 |
| **데모 제공** | 외부 이해관계자에게 보고서 생성 과정 시연 가능 |

### 1.3 핵심 지표(KPI)

- 배포 후 5단계 전체 워크플로우(데이터 업로드 ~ Word 다운로드) 정상 동작 확인
- 한글 차트 렌더링 정상 동작율 100%
- 클라우드 환경에서 보고서 생성 완료까지 30초 이내 (GPT 서술 제외)

---

## 2. 타겟 사용자

| 사용자 유형 | 설명 | 주요 니즈 |
|------------|------|----------|
| **IR센터 연구원** (Primary) | 호서대학교 IR센터 소속 직원 2~5명 | 매 학기 보고서 작성 시간 단축, Excel 전처리 자동화 |
| **IR센터 센터장** (Secondary) | 보고서 검토 및 승인 | 생성된 보고서 미리보기, 수치 검증 |
| **대학 경영진** (Tertiary) | 보고서 최종 수신자 | 직접 사용하지 않으나, 보고서 품질에 영향받음 |

---

## 3. 핵심 기능 요구사항 (Functional Requirements)

### FR-1: 데이터 입력 (1단계)

| ID | 요구사항 | 우선순위 | 변경 필요 |
|----|---------|---------|----------|
| FR-1.1 | Raw Excel 파일 업로드 (다중 파일) | Must | 인메모리 처리로 전환 |
| FR-1.2 | 앱 내 전처리 실행 (xlsx -> CSV 변환) | Must | Raw data/ 폴더 저장 제거, BytesIO/DataFrame 기반 변경 |
| FR-1.3 | 전처리 결과 CSV 직접 업로드 | Must | 변경 없음 |
| FR-1.4 | 기존 output/ 폴더 파일 사용 | - | **제거** (클라우드에 output/ 폴더 없음) |

### FR-2: 통계/그래프/GPT/보고서 (2~5단계)

| ID | 요구사항 | 변경 필요 |
|----|---------|----------|
| FR-2.1 | 연도별 핵심 지표 카드/표 | 변경 없음 |
| FR-3.1 | 5종 차트 생성 | 한글 폰트 설정 변경 |
| FR-4.1 | GPT-4o 서술 자동 생성 | API Key 관리 방식 변경 |
| FR-5.1 | Word 보고서 생성 및 다운로드 | BytesIO 직접 반환 (현재도 사용 중이므로 최소 변경) |

---

## 4. 비기능 요구사항 (Non-Functional Requirements)

| 카테고리 | 요구사항 | 기준 |
|---------|---------|------|
| 성능 | 전처리 실행 시간 | xlsx 3개 기준 10초 이내 |
| 성능 | 메모리 사용량 | 1GB 이내 (Community Cloud 제한) |
| 보안 | API Key 보호 | st.secrets 사용, 코드/저장소에 노출 금지 |
| 보안 | 업로드 데이터 격리 | 세션 종료 시 자동 삭제 (ephemeral) |
| 호환성 | 브라우저 지원 | Chrome, Edge, Safari 최신 2개 버전 |
| 가용성 | 앱 가동 | 비활성 시 슬립 허용, Cold start 30초 이내 |

---

## 5. 클라우드 배포 시 변경 범위

### 5.1 아키텍처 비교

```
[현재: 로컬 실행]
사용자 PC (Windows)
  +-- Raw data/     <-- xlsx 파일 저장
  +-- output/       <-- CSV + Word 보고서 저장
  +-- .env          <-- API Key
  +-- streamlit run report_app/app.py

[목표: 클라우드 배포]
GitHub (Public Repo)
  +-- Push -> Streamlit Community Cloud (Debian Linux)
               +-- st.secrets      <-- API Key
               +-- session_state   <-- DataFrame (인메모리)
               +-- BytesIO         <-- 차트/보고서 (인메모리)
               +-- st.download_button <-- 사용자에게 직접 전달
```

### 5.2 영향받는 파일 요약

| 파일 | 변경 유형 | 규모 |
|------|----------|------|
| `report_app/app.py` | 수정 | **대** (API Key, 전처리 흐름, 탭 제거) |
| `report_app/config.py` | 수정 | 소 (경로 상수 변경) |
| `report_app/data_loader.py` | 수정 | 소 (DataFrame 직접 수신 지원) |
| `report_app/chart_generator.py` | 수정 | 소 (폰트 캐시 갱신 추가) |
| `report_app/gpt_reporter.py` | 없음 | - |
| `report_app/report_builder.py` | 없음 | - |
| `전임교원_연구실적_전처리.py` | 수정 | 중 (인메모리 함수 추가) |
| `packages.txt` | **신규** | 소 |
| `.streamlit/secrets.toml` | **신규** | 소 (로컬용, 커밋 제외) |
| `.gitignore` | 수정 | 소 |

---

## 6. 제외 범위 (Out of Scope)

| 항목 | 사유 |
|------|------|
| 사용자 인증/로그인 | Community Cloud 무료 플랜 미지원 |
| 데이터베이스 연동 | CSV 기반으로 충분 |
| 다중 지표 모듈 추가 | 본 배포 범위에서는 기존 지표만 |
| 모바일 최적화 | Streamlit 기본 반응형에 의존 |
| Windows 빌드 수정 | 클라우드 배포와 병행 유지 |
| CI/CD 파이프라인 | GitHub 푸시 시 자동 배포로 충분 |

---

## 7. 성공 기준 (Success Criteria)

| ID | 기준 | 검증 방법 |
|----|------|----------|
| SC-1 | CSV 업로드 ~ Word 다운로드 전체 흐름 오류 없이 완료 | 수동 E2E 테스트 |
| SC-2 | Raw Excel 전처리 결과가 로컬과 동일 | 로컬 vs 클라우드 diff 비교 |
| SC-3 | matplotlib 차트 한글 정상 렌더링 | 5종 차트 육안 확인 |
| SC-4 | st.secrets API Key 정상 동작 | GPT 서술 생성 성공 확인 |
| SC-5 | Word 파일 Windows에서 정상 열림 | Word 실행 확인 |

---

## 8. 리스크 및 완화 방안

| # | 리스크 | 영향 | 완화 방안 |
|---|--------|------|----------|
| R-1 | API Key 노출 (Public 앱) | 높음 | HTTPS 기본 제공, `type="password"` 사용, 세션 메모리에만 보관 |
| R-2 | GPT API 비용 폭증 | 높음 | 사용자 본인 API Key 입력 구조 유지 (비용은 사용자 부담) |
| R-3 | 한글 폰트 미설치 | 중간 | `packages.txt`에 `fonts-nanum` + 폰트 캐시 갱신 코드 |
| R-4 | Ephemeral Storage 데이터 유실 | 중간 | session_state 보관 + CSV 다운로드 버튼 제공 |
| R-5 | 메모리 제한 (1GB) | 중간 | 현재 데이터 규모에서 안전, 모니터링 |
| R-6 | 앱 슬립 모드 | 낮음 | 사용 빈도 낮으므로 허용 (Cold start 30초) |
| R-7 | 한글 파일명 Linux 이슈 | 낮음 | unicodedata.normalize("NFC") 처리 적용됨 |
