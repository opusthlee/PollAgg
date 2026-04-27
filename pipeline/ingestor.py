import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from db.models import SurveyData

logger = logging.getLogger(__name__)


class DataIngestor:
    """
    Handles parsing and saving of statistical data from various sources.
    V4: 수집기 오케스트레이션 + 중복 방지 + NESDC 스크래퍼 통합
    """
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # 핵심: 수집기 오케스트레이션
    # ------------------------------------------------------------------
    def run_collectors(self, config_path: str = "config.json") -> Dict[str, int]:
        """
        config.json에 정의된 모든 활성화된 수집기를 실행하고 DB에 저장합니다.

        Returns:
            {소스명: 저장건수} 딕셔너리
        """
        from pipeline.collectors import DataGovKrCollector, NecDataCollector, NesdcScraper

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except FileNotFoundError:
            logger.error(f"[Ingestor] config.json을 찾을 수 없습니다: {config_path}")
            return {}

        sources = config.get("data_sources", {})
        results_summary: Dict[str, int] = {}

        # ── 1. data.go.kr (공공데이터포털 API) ──
        dgk_cfg = sources.get("data_gov_kr", {})
        if dgk_cfg.get("enabled", False):
            logger.info("[Ingestor] data.go.kr 수집 시작...")
            collector = DataGovKrCollector(api_key=dgk_cfg.get("api_key", ""))
            for target in config.get("ingest_targets", {}).get("elections", []):
                data = collector.collect(
                    sg_id=target.get("sg_id", dgk_cfg.get("default_sg_id", "20240410")),
                    sg_type_code=target.get("sg_type_code", dgk_cfg.get("default_sg_type_code", "2")),
                )
                saved = self.parse_and_save_json(data, category=target.get("category", "election"))
                results_summary[f"data_gov_kr:{target.get('name', 'unknown')}"] = saved

        # ── 2. data.nec.go.kr (선거 실제 결과 API) ──
        nec_cfg = sources.get("nec_data", {})
        if nec_cfg.get("enabled", False):
            logger.info("[Ingestor] data.nec.go.kr 수집 시작...")
            collector = NecDataCollector(api_key=nec_cfg.get("api_key", ""))
            for target in config.get("ingest_targets", {}).get("elections", []):
                data = collector.collect(
                    election_id=target.get("election_id", nec_cfg.get("default_election_id", "0020240410")),
                    election_date=target.get("date", ""),
                )
                saved = self.parse_and_save_json(data, category="election_result")
                results_summary[f"nec_data:{target.get('name', 'unknown')}"] = saved

        # ── 3. NESDC 스크래퍼 (중앙선거여론조사심의위원회) ──
        nesdc_cfg = sources.get("nesdc", {})
        if nesdc_cfg.get("enabled", False):
            logger.info("[Ingestor] NESDC 스크래퍼 수집 시작...")
            scraper = NesdcScraper()
            
            # 주간 주요 데이터 (XLS) 우선 수집 (지지율 포함)
            if nesdc_cfg.get("use_weekly_xls", True):
                logger.info("[Ingestor] NESDC 주간 주요 데이터(XLS) 수집 중...")
                xls_data = scraper.fetch_weekly_xls(pages=nesdc_cfg.get("weekly_pages", 1))
                saved_xls = self.parse_and_save_json(xls_data, category="election")
                results_summary["nesdc_xls"] = saved_xls

            # 목록 페이지 수집 (메타데이터 위주)
            data = scraper.collect(
                pages=nesdc_cfg.get("pages", 1),
                poll_gubun=nesdc_cfg.get("poll_gubun", ""),
                sdate=nesdc_cfg.get("sdate", ""),
                edate=nesdc_cfg.get("edate", ""),
                delay=nesdc_cfg.get("delay", 1.5),
                fetch_detail=nesdc_cfg.get("fetch_detail", True),
            )
            saved = self.parse_and_save_json(data, category="election")
            results_summary["nesdc_list"] = saved

        logger.info(f"[Ingestor] 전체 수집 완료: {results_summary}")
        return results_summary

    # ------------------------------------------------------------------
    # 개별 저장 메서드
    # ------------------------------------------------------------------
    def parse_and_save_json(
        self,
        raw_data: List[Dict[str, Any]],
        category: str = "general",
    ) -> int:
        """
        정규화된 데이터 리스트를 DB에 저장합니다.
        중복 방지: 동일 agency + date 조합은 건너뜁니다.
        """
        saved_count = 0
        skipped_count = 0

        for item in raw_data:
            if not item.get("agency") or not item.get("results"):
                continue

            agency = item["agency"]
            date = item.get("date", "1970-01-01")

            # 중복 체크: agency + date + region + district 조합으로 체크
            query = self.db.query(SurveyData).filter(
                SurveyData.agency == agency, 
                SurveyData.date == date
            )
            if item.get("region"):
                query = query.filter(SurveyData.region == item["region"])
            if item.get("district"):
                query = query.filter(SurveyData.district == item["district"])
                
            existing = query.first()
            if existing:
                skipped_count += 1
                continue

            entry = SurveyData(
                category=item.get("category", category),
                agency=agency,
                date=date,
                results=item["results"],
                sample_size=int(item.get("sample_size", 1000)),
                method=item.get("method", "Unknown"),
                response_rate=item.get("response_rate"),
                region=item.get("region"),
                district=item.get("district"),
                is_manual_override=item.get("is_manual_override", False),
            )
            self.db.add(entry)
            saved_count += 1

        self.db.commit()
        if skipped_count:
            logger.info(f"[Ingestor] 중복 {skipped_count}건 건너뜀")
        logger.info(f"[Ingestor] {saved_count}건 저장 완료")
        return saved_count

    def parse_and_save_csv(self, file_path: str) -> int:
        """CSV/Excel 파일 직접 임포트 (향후 확장용)"""
        # TODO: pandas 또는 openpyxl로 파싱 구현
        logger.warning("[Ingestor] parse_and_save_csv는 아직 미구현입니다.")
        return 0
