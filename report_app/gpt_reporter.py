"""
GPT API 연동 + 보고서 서술 생성 모듈

각 섹션에 필요한 데이터를 JSON으로 전달하여
대학 IR 분석 스타일의 한국어 서술 텍스트를 생성한다.
"""

from __future__ import annotations

import json

from openai import OpenAI

from report_app.config import GPT_MAX_TOKENS, GPT_MODEL, GPT_TEMPERATURE, UNIVERSITY

# ---------------------------------------------------------------------------
# 시스템 프롬프트
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """당신은 대학 IR(기관연구) 전문 분석가입니다.
제공된 데이터를 바탕으로 대학 내부 보고서용 한국어 서술문을 작성합니다.

작성 규칙:
- 핵심 수치를 반드시 언급하되, 자연스러운 문장으로 서술합니다.
- 객관적이고 분석적인 어조를 유지합니다.
- 각 항목을 불릿 포인트(•) 형식으로 2~4개 서술합니다.
- 한 불릿 포인트는 2~3문장 이내로 작성합니다.
- 수치는 소수점 네 자리까지 그대로 기재합니다.
- 마크다운 기호(**,#등)는 사용하지 않습니다.
- 순위 상승·하락 표현: 상승(▲), 하락(▼), 유지(-)
"""


def _call_gpt(client: OpenAI, user_content: str) -> str:
    """GPT API를 호출하고 응답 텍스트를 반환한다."""
    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        max_tokens=GPT_MAX_TOKENS,
        temperature=GPT_TEMPERATURE,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# 섹션별 서술 생성 함수
# ---------------------------------------------------------------------------

def generate_trend_narrative(
    client: OpenAI,
    hoseo_trend: dict[int, dict],
    averages: dict[int, dict],
    university: str | None = None,
) -> str:
    """
    섹션 1: 연도별 1인당논문수 추이 서술

    Args:
        client: OpenAI 클라이언트
        hoseo_trend: get_hoseo_trend() 반환값
        averages: get_averages() 반환값
        university: 대학명 (None이면 config.UNIVERSITY 사용)
    """
    univ = university or UNIVERSITY
    prompt = f"""아래는 {univ}의 전임교원 1인당 SCI/SCOPUS 논문수 연도별 추이 데이터입니다.

{univ} 연도별 데이터:
{json.dumps(hoseo_trend, ensure_ascii=False, indent=2)}

연도별 평균 데이터:
{json.dumps(averages, ensure_ascii=False, indent=2)}

위 데이터를 바탕으로 다음 내용을 서술해주세요:
- {univ}의 연도별 1인당논문수 변화 추이 (증가/감소 여부, 변화폭)
- 전국 평균, 충청권 평균, 비교군 평균과의 격차 현황
- 전반적인 연구 역량 평가"""

    return _call_gpt(client, prompt)


def generate_comparison_narrative(
    client: OpenAI,
    compare_data: list[dict],
    averages: dict[int, dict],
    year: int,
    university: str | None = None,
) -> str:
    """
    섹션 2: 전국·충청권·비교군 평균 비교 서술

    Args:
        client: OpenAI 클라이언트
        compare_data: get_compare_group_data() 반환값
        averages: get_averages() 반환값
        year: 기준 연도
        university: 대학명 (None이면 config.UNIVERSITY 사용)
    """
    univ = university or UNIVERSITY
    prompt = f"""{year}년 기준 {univ} 및 비교군 데이터입니다.

비교군({year}년):
{json.dumps(compare_data, ensure_ascii=False, indent=2)}

평균 데이터({year}년):
{json.dumps(averages.get(year, {}), ensure_ascii=False, indent=2)}

위 데이터를 바탕으로 다음 내용을 서술해주세요:
- {univ}와 비교군 5개 대학의 1인당논문수 순위 및 비교
- 전국 평균, 충청권 평균 대비 {univ}의 위치
- 비교군 내 상위·하위 대학과의 격차"""

    return _call_gpt(client, prompt)


def generate_regional_narrative(
    client: OpenAI,
    hoseo_trend: dict[int, dict],
    rank_changes: dict[int, dict],
    university: str | None = None,
) -> str:
    """
    섹션 3: 충청권 순위 비교 서술

    Args:
        client: OpenAI 클라이언트
        hoseo_trend: get_hoseo_trend() 반환값
        rank_changes: get_rank_changes() 반환값
        university: 대학명 (None이면 config.UNIVERSITY 사용)
    """
    univ = university or UNIVERSITY
    prompt = f"""아래는 {univ}의 충청권 및 전국 순위 변화 데이터입니다.

순위 변화 데이터:
{json.dumps(rank_changes, ensure_ascii=False, indent=2)}

1인당논문수 추이:
{json.dumps(hoseo_trend, ensure_ascii=False, indent=2)}

위 데이터를 바탕으로 다음 내용을 서술해주세요:
- 충청권 내 {univ}의 순위 변화 추이 (▲상승/▼하락 표기)
- 전국 순위 변화 추이
- 순위 변화의 원인 및 시사점"""

    return _call_gpt(client, prompt)


def generate_yoy_narrative(
    client: OpenAI,
    yoy_changes: dict,
    year: int,
    university: str | None = None,
) -> str:
    """
    섹션 4: 전년대비 증감 현황 서술

    Args:
        client: OpenAI 클라이언트
        yoy_changes: get_yoy_changes() 반환값
        year: 기준 연도
        university: 대학명 (None이면 config.UNIVERSITY 사용)
    """
    univ = university or UNIVERSITY
    prev_year = year - 1
    prompt = f"""{prev_year}년 대비 {year}년 충청권 대학 1인당논문수 증감 현황입니다.

증감률 상위 3개 대학:
{json.dumps(yoy_changes.get('상위', []), ensure_ascii=False, indent=2)}

증감률 하위 3개 대학:
{json.dumps(yoy_changes.get('하위', []), ensure_ascii=False, indent=2)}

{univ} 증감 현황:
{json.dumps(yoy_changes.get('호서'), ensure_ascii=False, indent=2)}

위 데이터를 바탕으로 다음 내용을 서술해주세요:
- {univ}의 전년대비 증감 현황 (증감률, 절대값 변화)
- 충청권 내 상위·하위 증감 대학 현황
- 전반적인 충청권 연구 실적 변화 흐름"""

    return _call_gpt(client, prompt)
