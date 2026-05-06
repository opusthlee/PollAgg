"""
Raw date 문자열 → (survey_date, survey_year, survey_week) 정규화 유틸.

PollAgg DB의 raw `date` 컬럼은 NESDC 등 외부 소스의 다양한 입력을 그대로 저장.
이 모듈은 raw 문자열에서 가능한 한 많은 의미를 추출:
- ISO 단일 날짜로 환산 가능 → survey_date 채움 (year/week도 함께 채움)
- 주간 집계 (YY-WW) → survey_year + survey_week 채움 (survey_date=None)
- 연도만 → survey_year만 채움
- 모호/노이즈 → 모두 None
"""
import re
from datetime import date, datetime
from typing import Optional, Tuple

ISO_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
# YY-NN: 두 자리 연도 + 두 자리 숫자. NN이 1~53이면 주차로 해석.
YY_WK_RE = re.compile(r"^(\d{2})-(\d{1,2})$")
# YY-MM-DD-- 같은 trailing 구분자
YY_MD_TRAIL_RE = re.compile(r"^(\d{2})[-./](\d{1,2})[-./](\d{1,2})[-./]+$")
# YY-MM-DD or YY.MM.DD 정상 (2자리 연도)
YY_MD_RE = re.compile(r"^(\d{2})[-./](\d{1,2})[-./](\d{1,2})$")
# YYYY-MM-DD 변형 (구분자 . 또는 /)
YYYY_MD_RE = re.compile(r"^(\d{4})[-./](\d{1,2})[-./](\d{1,2})$")
# 연도만
YEAR_ONLY_RE = re.compile(r"^(\d{2,4})\.?$")


def _expand_year(yy_or_yyyy: str) -> int:
    """'25' → 2025, '99' → 1999, '2026' → 2026. 두 자리는 70 이상이면 1900대, 미만이면 2000대."""
    n = int(yy_or_yyyy)
    if n >= 1000:
        return n
    if n >= 70:
        return 1900 + n
    return 2000 + n


def _safe_date(y: int, m: int, d: int) -> Optional[date]:
    try:
        return date(y, m, d)
    except (ValueError, TypeError):
        return None


def normalize_raw_date(raw: Optional[str]) -> Tuple[Optional[date], Optional[int], Optional[int]]:
    """
    Raw 입력 → (survey_date, survey_year, survey_week).

    - 단일 ISO 날짜로 풀리면 survey_date 채움. survey_year도 함께 채움. survey_week=None.
    - 'YY-WW' (주차) 형태로만 풀리면 survey_year/week만 채움.
    - 연도만 추출되면 survey_year만 채움.
    - 못 풀면 (None, None, None).
    """
    if raw is None:
        return None, None, None
    s = str(raw).strip()
    if not s or s == "1970-01-01":  # epoch default = 정보없음
        return None, None, None

    # 1. ISO YYYY-MM-DD
    m = ISO_RE.match(s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        dt = _safe_date(y, mo, d)
        if dt:
            return dt, y, None

    # 2. YY-MM-DD-- (trailing dashes/dots)
    m = YY_MD_TRAIL_RE.match(s)
    if m:
        y = _expand_year(m.group(1))
        mo, d = int(m.group(2)), int(m.group(3))
        dt = _safe_date(y, mo, d)
        if dt:
            return dt, y, None

    # 3. YYYY[-./]MM[-./]DD
    m = YYYY_MD_RE.match(s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        dt = _safe_date(y, mo, d)
        if dt:
            return dt, y, None

    # 4. YY[-./]MM[-./]DD
    m = YY_MD_RE.match(s)
    if m:
        y = _expand_year(m.group(1))
        mo, d = int(m.group(2)), int(m.group(3))
        dt = _safe_date(y, mo, d)
        if dt:
            return dt, y, None

    # 5. YY-WW (주간 집계)
    m = YY_WK_RE.match(s)
    if m:
        yy, wk = m.group(1), int(m.group(2))
        if 1 <= wk <= 53:
            return None, _expand_year(yy), wk

    # 6. 연도만
    m = YEAR_ONLY_RE.match(s)
    if m:
        return None, _expand_year(m.group(1)), None

    # 7. 마지막 시도: 어디든 YYYY-MM-DD 부분문자열이 박혀있으면
    inner = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if inner:
        y, mo, d = int(inner.group(1)), int(inner.group(2)), int(inner.group(3))
        dt = _safe_date(y, mo, d)
        if dt:
            return dt, y, None

    return None, None, None
