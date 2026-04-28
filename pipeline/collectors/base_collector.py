"""
Base Collector Abstract Class
모든 데이터 수집기의 공통 인터페이스를 정의합니다.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    모든 데이터 수집기의 기반 클래스.
    새로운 데이터 소스 추가 시 이 클래스를 상속하여 구현합니다.
    """
    SOURCE_NAME: str = "unknown"
    CATEGORY: str = "general"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = None

    @abstractmethod
    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        원본 데이터를 수집하고 PollAgg 표준 포맷으로 반환합니다.

        Returns:
            List of dicts with keys:
            - agency (str): 조사 기관명
            - date (str): 조사 기준일 (YYYY-MM-DD)
            - results (dict): {후보/정당명: 지지율(float)}
            - sample_size (int): 표본 크기
            - method (str): 조사 방법 (ARS, 면접 등)
            - response_rate (float|None): 응답률
            - category (str): 데이터 카테고리
            - source (str): 수집 소스 식별자
        """
        raise NotImplementedError

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        원시 데이터를 PollAgg 표준 포맷으로 정규화합니다.
        서브클래스에서 오버라이드 가능.
        """
        return {
            "agency": raw.get("agency", "Unknown"),
            "date": raw.get("date", "1970-01-01"),
            "results": raw.get("results", {}),
            "sample_size": int(raw.get("sample_size", 1000)),
            "method": raw.get("method", "Unknown"),
            "response_rate": raw.get("response_rate", None),
            "category": raw.get("category", self.CATEGORY),
            "source": self.SOURCE_NAME,
            "is_manual_override": False,
        }

    def collect(self, **kwargs) -> List[Dict[str, Any]]:
        """fetch() → normalize() 파이프라인 실행"""
        try:
            raw_list = self.fetch(**kwargs)
            normalized = [self.normalize(r) for r in raw_list]
            logger.info(f"[{self.SOURCE_NAME}] 수집 완료: {len(normalized)}건")
            return normalized
        except Exception as e:
            logger.error(f"[{self.SOURCE_NAME}] 수집 실패: {e}")
            return []
