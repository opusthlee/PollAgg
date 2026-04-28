"""
중앙선거여론조사심의위원회 (NESDC) 스크래퍼
Source 3: https://www.nesdc.go.kr

구조 분석 결과:
  - 목록: /portal/bbs/B0000005/list.do?menuNo=200467&pageIndex={N}
    → <a class="row tr"> 태그, 내부 <span class="col"> 8개
      [0]번호 [1]조사기관 [2]의뢰자 [3]조사방법 [4]표본추출틀
      [5]선거명 [6]날짜 [7]지역
  - 상세: /portal/bbs/B0000005/view.do?nttId={ID}&menuNo=200467
    → Table 0에 전체 메타 (기관명, 표본크기, 응답률, 조사기간 등)
    → 지지율 결과는 PDF에만 존재 (24시간 후 공개 정책)
  - 주요데이터: /portal/bbs/B0000025/list.do?menuNo=200500
    → XLS 다운로드 (주간 집계)

파싱 전략:
  1. 목록 행에서 기본 메타(기관, 의뢰자, 방법, 날짜, 지역) 즉시 추출
  2. 상세 페이지에서 표본크기 / 응답률 보강
  3. 지지율은 추후 XLS(주요데이터) 연동으로 확장
"""
import re
import time
import logging
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)

BASE_URL = "https://www.nesdc.go.kr"
LIST_URL  = f"{BASE_URL}/portal/bbs/B0000005/list.do"
VIEW_URL  = f"{BASE_URL}/portal/bbs/B0000005/view.do"
WEEKLY_URL  = f"{BASE_URL}/portal/bbs/B0000025/list.do"
WEEKLY_VIEW_URL = f"{BASE_URL}/portal/bbs/B0000025/view.do"
MENU_NO   = "200467"
WEEKLY_MENU_NO = "200500"

# 목록 span 인덱스 맵
COL_IDX = {
    "seq":     0,   # 등록번호
    "agency":  1,   # 조사기관
    "client":  2,   # 의뢰자
    "method":  3,   # 조사방법 (ARS, 면접 등)
    "frame":   4,   # 표본추출틀
    "election":5,   # 선거명
    "date":    6,   # 공표일
    "region":  7,   # 지역
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": BASE_URL,
}


class NesdcScraper(BaseCollector):
    """
    중앙선거여론조사심의위원회 스크래퍼.

    목록 페이지의 행 데이터(기관명, 방법, 날짜, 지역)를 기본으로 수집하고
    상세 페이지에서 표본크기, 응답률을 보강합니다.

    사용법:
        scraper = NesdcScraper()
        data = scraper.collect(
            pages=3,                  # 목록 페이지 수 (1페이지 = 10건)
            poll_gubun="",            # 선거구분 필터 (빈 문자열=전체)
            sdate="2026-01-01",       # 시작일
            edate="",                 # 종료일
            fetch_detail=True,        # 상세 페이지에서 표본크기/응답률 보강
            delay=1.5                 # 요청 간 딜레이 (서버 부하 방지)
        )
    """
    SOURCE_NAME = "nesdc.go.kr"
    CATEGORY    = "election"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

    # ------------------------------------------------------------------
    # 목록 수집
    # ------------------------------------------------------------------
    def _fetch_list_page(
        self,
        page: int = 1,
        poll_gubun: str = "",
        sdate: str = "",
        edate: str = "",
    ) -> List[Dict[str, Any]]:
        """목록 페이지 <a class='row tr'> 행들을 파싱합니다."""
        params: Dict[str, str] = {
            "menuNo": MENU_NO,
            "pageIndex": str(page),
        }
        if poll_gubun:
            params["pollGubuncd"] = poll_gubun
        if sdate:
            params["sdate"] = sdate
            params["edate"] = edate or ""

        try:
            resp = self._session.get(LIST_URL, params=params, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"[NESDC] 목록 요청 실패 (page={page}): {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        rows = soup.select("a.row.tr")
        items = []

        for row in rows:
            spans = row.select("span.col")
            if len(spans) < 7:
                continue

            def col(idx: int) -> str:
                return spans[idx].get_text(" ", strip=True) if idx < len(spans) else ""

            # href에서 nttId 추출
            href = row.get("href", "")
            ntt_id_match = re.search(r"nttId=(\d+)", href)
            ntt_id = ntt_id_match.group(1) if ntt_id_match else ""

            items.append({
                "ntt_id":   ntt_id,
                "seq":      col(0), # 등록번호는 항상 첫 번째
                "agency":   col(1), # 조사기관명
                "region":   self._normalize_region(col(-1)), # 시·도는 항상 마지막 스팬
                "date":     self._normalize_date(col(-2)),   # 등록일은 뒤에서 두 번째
                "election": col(-3),                         # 선거명/조사명은 뒤에서 세 번째
                "method":   col(3),                          # 방법은 앞에서 네 번째
                "results":  {},
            })

        logger.info(f"[NESDC] 목록 page={page} → {len(items)}건")
        return items

    # ------------------------------------------------------------------
    # 상세 보강 (표본크기 / 응답률)
    # ------------------------------------------------------------------
    def _enrich_with_detail(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """상세 페이지(Table 0)에서 표본크기, 응답률을 추출해 보강합니다."""
        ntt_id = item.get("ntt_id", "")
        if not ntt_id:
            return item

        try:
            resp = self._session.get(
                VIEW_URL,
                params={"nttId": ntt_id, "menuNo": MENU_NO},
                timeout=15,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning(f"[NESDC] 상세 요청 실패 (nttId={ntt_id}): {e}")
            return item

        soup = BeautifulSoup(resp.text, "lxml")
        tables = soup.select("table")
        if not tables:
            return item

        # Table 1: 표본크기 (전체 행)
        if len(tables) > 1:
            for row in tables[1].select("tr"):
                cells = [td.get_text(strip=True) for td in row.select("td")]
                if cells and cells[0] == "전체" and len(cells) >= 2:
                    n = self._extract_number(cells[1])
                    if n:
                        item["sample_size"] = n
                    break

        # Table 27: 전체 응답률 (전체 접촉률/응답률)
        for table in tables:
            headers = [th.get_text(strip=True) for th in table.select("th")]
            if "전체 응답률" in " ".join(headers) or "전체접촉률" in " ".join(headers):
                for row in table.select("tr"):
                    ths = row.select("th")
                    tds = row.select("td")
                    for th, td in zip(ths, tds):
                        if "응답률" in th.get_text(strip=True):
                            rr = self._extract_float(td.get_text(strip=True))
                            if rr is not None:
                                item["response_rate"] = rr
                break

        # Table 0: 조사일시 (정확한 날짜)로 보강
        if tables:
            for row in tables[0].select("tr"):
                th = row.select_one("th")
                td = row.select_one("td")
                if th and td:
                    key = th.get_text(strip=True)
                    val = td.get_text(strip=True)
                    if "조사일시" in key or "조사기간" in key:
                        end_date = self._extract_end_date(val)
                        if end_date:
                            item["date"] = end_date

        return item

    # ------------------------------------------------------------------
    # 메인 fetch
    # ------------------------------------------------------------------
    def fetch(
        self,
        pages: int = 1,
        poll_gubun: str = "",
        sdate: str = "",
        edate: str = "",
        delay: float = 1.5,
        fetch_detail: bool = True,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        NESDC 목록을 수집합니다.

        Args:
            pages:         크롤링할 목록 페이지 수 (1페이지 = 10건)
            poll_gubun:    선거구분 코드 ('1'=대선, '2'=총선, '3'=지방선거, ''=전체)
            sdate:         시작일 (YYYY-MM-DD)
            edate:         종료일 (YYYY-MM-DD)
            delay:         페이지 간 요청 딜레이 (초)
            fetch_detail:  True면 상세 페이지에서 표본크기/응답률 보강
        """
        all_results: List[Dict[str, Any]] = []

        for page in range(1, pages + 1):
            logger.info(f"[NESDC] page {page}/{pages} 수집...")
            items = self._fetch_list_page(page, poll_gubun, sdate, edate)
            if not items:
                logger.info(f"[NESDC] page={page}: 데이터 없음. 중단.")
                break

            for item in items:
                if fetch_detail and item["ntt_id"]:
                    item = self._enrich_with_detail(item)
                    time.sleep(delay * 0.4)
                all_results.append(item)

            time.sleep(delay)

        logger.info(f"[NESDC] 전체 수집: {len(all_results)}건")
        return all_results

    # ------------------------------------------------------------------
    # 주간 주요 데이터 XLS 수집 (지지율 포함)
    # ------------------------------------------------------------------
    def fetch_weekly_xls(self, pages: int = 1, delay: float = 2.0) -> List[Dict[str, Any]]:
        """
        주간 주요 데이터 목록에서 XLS 파일을 찾아 파싱합니다.
        지지율(results) 데이터가 포함되어 있습니다.
        """
        all_data = []
        for page in range(1, pages + 1):
            logger.info(f"[NESDC-XLS] 목록 page {page} 수집 중...")
            params = {"menuNo": WEEKLY_MENU_NO, "pageIndex": str(page)}
            try:
                resp = self._session.get(WEEKLY_URL, params=params, timeout=15)
                resp.raise_for_status()
            except Exception as e:
                logger.error(f"[NESDC-XLS] 목록 요청 실패: {e}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            # B0000025 게시판 대응 (정규식 기반 링크 검색)
            all_links = soup.find_all("a", href=re.compile(r"nttId=\d+"))
            
            seen_ntt_ids = set()
            for link_tag in all_links:
                href = link_tag.get("href", "")
                ntt_id_match = re.search(r"nttId=(\d+)", href)
                if not ntt_id_match: continue
                
                ntt_id = ntt_id_match.group(1)
                if ntt_id in seen_ntt_ids: continue
                seen_ntt_ids.add(ntt_id)

                # 상세 페이지에서 XLS 링크 찾기
                logger.info(f"[NESDC-XLS] 상세 페이지 보강 중: {ntt_id}")
                xls_data = self._fetch_xls_from_detail(ntt_id)
                if xls_data:
                    all_data.extend(xls_data)
                
                time.sleep(delay)
        
        return all_data

    def _fetch_xls_from_detail(self, ntt_id: str) -> List[Dict[str, Any]]:
        """상세 페이지에서 XLS 파일을 찾아 다운로드하고 파싱합니다."""
        params = {"nttId": ntt_id, "menuNo": WEEKLY_MENU_NO}
        try:
            resp = self._session.get(WEEKLY_VIEW_URL, params=params, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"[NESDC-XLS] 상세 페이지 요청 실패 (nttId={ntt_id}): {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        # 파일 다운로드 링크 찾기
        xls_links = []
        for a in soup.select("a"):
            href = a.get("href", "")
            text = a.get_text(strip=True).lower()
            if "filedown" in href.lower() or ".xls" in text:
                xls_links.append({"url": BASE_URL + href if href.startswith("/") else href, "name": text})
        
        results = []
        for link in xls_links:
            if "xls" in link["name"] or ".xlsx" in link["name"]:
                logger.info(f"[NESDC-XLS] 파일 다운로드 중: {link['name']}")
                data = self._download_and_parse_weekly_xls(link["url"])
                if data:
                    results.extend(data)
        
        return results

    def _download_and_parse_weekly_xls(self, url: str) -> List[Dict[str, Any]]:
        """XLS 파일을 다운로드하여 파싱합니다."""
        import tempfile, os, openpyxl
        try:
            resp = self._session.get(url, timeout=30, stream=True)
            resp.raise_for_status()
            
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                for chunk in resp.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                tmp_path = tmp.name
            
            wb = openpyxl.load_workbook(tmp_path, data_only=True)
            ws = wb.active
            
            # 헤더 파싱 (Row 1: 항목명, Row 2: 상세 정당명)
            rows = list(ws.iter_rows(values_only=True))
            if len(rows) < 3: return []
            
            header1 = rows[0]
            header2 = rows[1]
            
            parsed_data = []
            party_start_idx = 10 # 0~9는 메타데이터
            
            # 정당명 매핑
            parties = []
            for i in range(party_start_idx, len(header2)):
                p_name = header2[i]
                if p_name:
                    parties.append((i, p_name.replace("\n", " ").strip()))
            
            for row in rows[2:]:
                if not row[0]: continue # 등록번호 없으면 건너뜀
                
                results = {}
                for idx, p_name in parties:
                    val = row[idx]
                    if isinstance(val, (int, float)):
                        results[p_name] = float(val)
                
                parsed_data.append({
                    "agency": str(row[1]).strip(),
                    "date": self._extract_end_date(str(row[3])),
                    "results": results,
                    "sample_size": self._extract_number(str(row[6])) or 1000,
                    "method": str(row[4]).strip(),
                    "response_rate": self._extract_float(str(row[8])),
                    "category": self.CATEGORY,
                    "source": self.SOURCE_NAME,
                    "region": self._normalize_region(str(row[5]).strip()), # '선거구' 필드 등에서 유추
                    "district": str(row[5]).strip(),
                    "meta": {
                        "ntt_id": str(row[0]),
                        "client": str(row[2]).strip(),
                        "frame": str(row[5]).strip(),
                    }
                })
            
            os.unlink(tmp_path)
            return parsed_data
            
        except Exception as e:
            logger.error(f"[NESDC-XLS] XLS 파싱 실패: {e}")
            return []

    # ------------------------------------------------------------------
    # normalize: PollAgg 표준 포맷 변환
    # ------------------------------------------------------------------
    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "agency":           raw.get("agency", "NESDC Unknown"),
            "date":             raw.get("date", "1970-01-01"),
            "results":          raw.get("results", {}),
            "sample_size":      int(raw.get("sample_size", 1000)),
            "method":           raw.get("method", "Unknown"),
            "response_rate":    raw.get("response_rate"),
            "category":         self.CATEGORY,
            "source":           self.SOURCE_NAME,
            "is_manual_override": False,
            "meta": {
                "ntt_id":    raw.get("ntt_id", ""),
                "seq":       raw.get("seq", ""),
                "client":    raw.get("client", ""),
                "election":  raw.get("election", ""),
                "region":    raw.get("region", ""),
                "frame":     raw.get("frame", ""),
            },
        }

    # ------------------------------------------------------------------
    # 유틸리티
    # ------------------------------------------------------------------
    def _normalize_region(self, region_str: str) -> str:
        """조사지역 문자열을 표준 권역명으로 정규화"""
        if not region_str: return "전국"
        # 표준 권역 키워드 매핑
        mapping = {
            "서울": "서울", "경기": "경기", "인천": "인천", 
            "충청": "충청", "대전": "충청", "세종": "충청", "충북": "충청", "충남": "충청",
            "호남": "호남", "광주": "호남", "전라": "호남", "전북": "호남", "전남": "호남",
            "영남": "영남", "경상": "영남", "부산": "영남", "대구": "영남", "울산": "영남", "경북": "영남", "경남": "영남",
            "강원": "강원", "제주": "제주"
        }
        for key, val in mapping.items():
            if key in region_str:
                return val
        return "전국"

    def _normalize_date(self, s: str) -> str:
        """다양한 날짜 형식 → YYYY-MM-DD 변환 (노이즈 제거 포함)"""
        if not s:
            return ""
        
        # 숫자와 구분자(-, ., /)만 남기고 제거
        clean = re.sub(r"[^0-9\-./]", "", s.strip())
        # 앞뒤 구분자 제거 (여러 번 반복될 수 있으므로 정규식 사용)
        clean = re.sub(r"^[.\-/]+|[.\-/]+$", "", clean)
        
        if not clean:
            return ""

        # YY.MM.DD or YY-MM-DD -> 20YY-MM-DD
        if re.match(r"^\d{2}[-./]\d{2}[-./]\d{2}$", clean):
            clean = "20" + clean
        
        # 구분자 통일
        clean = clean.replace(".", "-").replace("/", "-")
        
        # 표준 형식 시도
        for fmt in ["%Y-%m-%d", "%Y%m%d"]:
            try:
                from datetime import datetime
                return datetime.strptime(clean, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # 정규식으로 YYYY-MM-DD 추출 시도
        match = re.search(r"(\d{4}-\d{2}-\d{2})", clean)
        if match:
            return match.group(1)
            
        return clean[:10] if len(clean) >= 10 else clean

    def _extract_end_date(self, period_str: str) -> Optional[str]:
        """
        날짜 범위 문자열에서 종료일을 추출합니다.
        예: 
        - '2026-04-23 ~ 2026-04-25' -> '2026-04-25'
        - '26.01.02.~03.' -> '2026-01-03'
        - '25.12.31./26.01.02.' -> '2026-01-02'
        """
        if not period_str: return None
        
        # 1. 종료 부분 분리 ( ~ 또는 / 또는 , 기준)
        parts = [p.strip() for p in re.split(r'[~/]', period_str) if p.strip()]
        if not parts: return None
        
        start_part = parts[0]
        end_part = parts[-1]
        
        # 2. 종료일이 숫자만 있거나 월-일만 있는 경우 (예: '03.', '01-02') 시작일에서 연도 복사
        if re.match(r'^\d{1,2}\.?$', end_part) or re.match(r'^\d{1,2}[-./]\d{1,2}\.?$', end_part):
            # 시작일에서 연도(YYYY. 또는 YY.) 추출
            year_match = re.match(r'^(\d{2,4})[-./]', start_part)
            if year_match:
                year_prefix = year_match.group(1)
                # 만약 end_part가 이미 월을 포함하고 있다면 연도만 붙임
                if '-' in end_part or '.' in end_part or '/' in end_part:
                    # '01-02' -> '2024-01-02'
                    if not end_part.startswith(year_prefix):
                         end_part = f"{year_prefix}-{end_part}"
                else:
                    # '03.' -> '2024.01.03.' (시작일의 연월 활용)
                    prefix_match = re.match(r'^(\d{2,4}[-./]\d{1,2}[-./])', start_part)
                    if prefix_match:
                        end_part = prefix_match.group(1) + end_part
        
        return self._normalize_date(end_part)

    def _extract_number(self, text: str) -> Optional[int]:
        """'808명' → 808"""
        nums = re.sub(r"[^\d]", "", str(text))
        return int(nums) if nums else None

    def _extract_float(self, text: str) -> Optional[float]:
        """'6.5%' → 6.5"""
        m = re.search(r"(\d+(?:\.\d+)?)", str(text))
        return float(m.group(1)) if m else None
