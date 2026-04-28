"""
공공데이터포털 (data.go.kr) - 중앙선거관리위원회 여론조사 결과 수집기
Source 1: 공식 Open API (API 키 필요)

API 문서 참조:
- 중앙선거관리위원회_선거여론조사결과조회
- https://www.data.go.kr/data/15000174/openapi.do
- Endpoint: http://apis.data.go.kr/9760000/PollInqireService2/
"""
import requests
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# 공공데이터포털 API 엔드포인트
# -------------------------------------------------------------------
BASE_URL = "http://apis.data.go.kr/9760000/PollInqireService2"
ENDPOINTS = {
    "list": f"{BASE_URL}/getPollInqireList2",       # 여론조사 목록
    "detail": f"{BASE_URL}/getPollInqireInfo2",     # 여론조사 상세
    "candidate": f"{BASE_URL}/getCandInqire2",       # 후보자별 조사결과
}

# 선거 종류 코드 (sgTypecode)
SG_TYPE_CODE = {
    "대통령선거": "1",
    "국회의원선거": "2",
    "전국동시지방선거": "3",
    "재보궐선거": "4",
}

# 주요 선거 ID (sgId) - 최근 선거 기준
SG_IDS = {
    "22대국회의원선거_2024": "20240410",
    "8회전국동시지방선거_2022": "20220601",
    "20대대통령선거_2022": "20220309",
    "21대국회의원선거_2020": "20200415",
}


class DataGovKrCollector(BaseCollector):
    """
    공공데이터포털 (data.go.kr) 여론조사 수집기.

    사용법:
        collector = DataGovKrCollector(api_key="YOUR_SERVICE_KEY")
        data = collector.collect(sg_id="20240410", sg_type_code="2")

    API 키 발급:
        1. https://www.data.go.kr 회원가입
        2. "중앙선거관리위원회 선거여론조사" 검색
        3. 활용신청 → 즉시 승인 → 마이페이지에서 일반 인증키 복사
    """
    SOURCE_NAME = "data.go.kr_nec"
    CATEGORY = "election"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)
        if not api_key:
            logger.warning(
                "[DataGovKr] API 키가 설정되지 않았습니다. "
                "config.json의 'data_gov_kr_key' 항목에 키를 입력하세요.\n"
                "  발급처: https://www.data.go.kr → 중앙선거관리위원회 선거여론조사 → 활용신청"
            )

    def _get(self, endpoint: str, params: dict) -> Optional[dict]:
        """공통 GET 요청 처리"""
        if not self.api_key:
            return None

        params.update({
            "serviceKey": self.api_key,
            "resultType": "json",
            "numOfRows": "100",
            "pageNo": "1",
        })
        try:
            resp = requests.get(endpoint, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"[DataGovKr] 요청 실패: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(f"[DataGovKr] JSON 파싱 실패. 응답: {resp.text[:200]}")
            return None

    def fetch_poll_list(self, sg_id: str, sg_type_code: str) -> List[Dict]:
        """여론조사 목록 조회"""
        data = self._get(ENDPOINTS["list"], {
            "sgId": sg_id,
            "sgTypecode": sg_type_code,
        })
        if not data:
            return []
        try:
            items = data["response"]["body"]["items"]["item"]
            return items if isinstance(items, list) else [items]
        except (KeyError, TypeError):
            logger.warning("[DataGovKr] 목록 응답 파싱 실패")
            return []

    def fetch_poll_detail(self, poll_id: str) -> Optional[Dict]:
        """여론조사 상세 조회"""
        data = self._get(ENDPOINTS["detail"], {"pollCommno": poll_id})
        if not data:
            return None
        try:
            return data["response"]["body"]["items"]["item"]
        except (KeyError, TypeError):
            return None

    def fetch_candidate_rates(self, poll_id: str) -> Dict[str, float]:
        """후보자별 지지율 조회 (getCandInqire2)"""
        data = self._get(ENDPOINTS["candidate"], {"pollCommno": poll_id})
        if not data:
            return {}
        
        rates = {}
        try:
            items = data["response"]["body"]["items"]["item"]
            if not isinstance(items, list):
                items = [items]
            
            for item in items:
                name = item.get("candNm")
                rate = item.get("rate")
                if name and rate is not None:
                    try:
                        rates[name] = float(rate)
                    except ValueError:
                        continue
        except (KeyError, TypeError):
            pass
        return rates

    def fetch(self, sg_id: str = "20240410", sg_type_code: str = "2", **kwargs) -> List[Dict[str, Any]]:
        """
        선거 여론조사 데이터 수집 메인 로직.

        Args:
            sg_id: 선거 ID (예: "20240410" = 22대 총선)
            sg_type_code: 선거 종류 코드 (1=대선, 2=총선, 3=지방선거)
        """
        if not self.api_key:
            logger.info("[DataGovKr] API 키 없음 → 샘플 데이터 반환")
            return self._get_sample_data(sg_id)

        poll_list = self.fetch_poll_list(sg_id, sg_type_code)
        results = []
        for poll in poll_list:
            try:
                poll_id = poll.get("pollCommno", "")
                detail = self.fetch_poll_detail(poll_id) or poll

                # 후보별 지지율 파싱 (상세 정보에서 추출하거나 별도 엔드포인트 호출)
                candidate_results = self.fetch_candidate_rates(poll_id)
                
                # 만약 candidate 엔드포인트에서 못 가져왔다면 상세 정보의 단일 필드 확인 (Fallback)
                if not candidate_results and "candNm" in detail and "rate" in detail:
                    candidate_results[detail["candNm"]] = float(detail.get("rate", 0))

                results.append({
                    "agency": detail.get("inqireOrgnztNm", "Unknown"),
                    "date": self._parse_date(detail.get("inqireEndde", "")),
                    "results": candidate_results,
                    "sample_size": int(detail.get("nqirerCnt", 1000)),
                    "method": detail.get("inqireMthd", "Unknown"),
                    "response_rate": self._parse_float(detail.get("rspnsRate")),
                    "category": "election",
                    "source": self.SOURCE_NAME,
                    "meta": {
                        "sg_id": sg_id,
                        "poll_id": poll_id,
                        "election_name": detail.get("sgName", ""),
                    }
                })
            except Exception as e:
                logger.warning(f"[DataGovKr] 항목 파싱 오류: {e}")
                continue

        return results

    def _parse_date(self, date_str: str) -> str:
        """날짜 문자열 → YYYY-MM-DD 변환"""
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")
        for fmt in ["%Y%m%d", "%Y-%m-%d", "%Y.%m.%d"]:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return date_str

    def _parse_float(self, val) -> Optional[float]:
        """안전한 float 변환"""
        try:
            return float(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    def _get_sample_data(self, sg_id: str) -> List[Dict]:
        """
        API 키 없이도 시스템을 테스트할 수 있는 샘플 데이터.
        22대 총선(2024) 기준 주요 여론조사 수동 입력 데이터.
        """
        logger.info("[DataGovKr] 샘플 데이터 모드 (API 키 미설정)")
        return [
            {
                "agency": "한국갤럽 [SAMPLE]",
                "date": "2024-04-01",
                "results": {"더불어민주당": 45.2, "국민의힘": 35.8, "기타": 19.0},
                "sample_size": 1003,
                "method": "전화면접",
                "response_rate": 15.2,
                "category": "election",
                "source": "sample_data",
            },
            {
                "agency": "리얼미터 [SAMPLE]",
                "date": "2024-04-03",
                "results": {"더불어민주당": 43.5, "국민의힘": 37.2, "기타": 19.3},
                "sample_size": 1500,
                "method": "ARS",
                "response_rate": 4.5,
                "category": "election",
                "source": "sample_data",
            },
            {
                "agency": "KBS-한국리서치 [SAMPLE]",
                "date": "2024-04-05",
                "results": {"더불어민주당": 44.8, "국민의힘": 36.1, "기타": 19.1},
                "sample_size": 1000,
                "method": "전화면접",
                "response_rate": 16.8,
                "category": "election",
                "source": "sample_data",
            },
        ]
