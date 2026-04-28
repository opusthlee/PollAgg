"""
PollAgg 데이터 수집 파이프라인 오케스트레이터 (V2)
모든 데이터 소스를 통합하여 DB에 저장합니다.

사용법:
    python3 -m pipeline.runner                          # 모든 소스 수집
    python3 -m pipeline.runner --source data_gov_kr    # 특정 소스만
    python3 -m pipeline.runner --list                  # 소스 목록 확인
    python3 -m pipeline.runner --dry-run               # DB 저장 없이 미리보기
"""
import argparse
import json
import logging
import os
import sys
from typing import List, Dict, Any, Optional

# PollAgg 루트 경로를 sys.path에 추가 (직접 실행 시 필요)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from pipeline.ingestor import DataIngestor
from pipeline.collectors.data_gov_kr import DataGovKrCollector
from pipeline.collectors.nec_data import NecDataCollector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pipeline.runner")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


def load_config() -> dict:
    """config.json 로드"""
    if not os.path.exists(CONFIG_PATH):
        logger.warning(f"config.json 없음: {CONFIG_PATH}")
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_collectors(config: dict) -> Dict[str, Any]:
    """설정 기반으로 수집기 인스턴스 생성"""
    sources_cfg = config.get("data_sources", {})
    collectors = {}

    # 1. 공공데이터포털 (data.go.kr)
    dgk_cfg = sources_cfg.get("data_gov_kr", {})
    if dgk_cfg.get("enabled", True):
        collectors["data_gov_kr"] = {
            "instance": DataGovKrCollector(api_key=dgk_cfg.get("api_key") or None),
            "fetch_kwargs": {
                "sg_id": dgk_cfg.get("default_sg_id", "20240410"),
                "sg_type_code": dgk_cfg.get("default_sg_type_code", "2"),
            },
            "label": "공공데이터포털 여론조사",
        }

    # 2. NEC 개방포털 (data.nec.go.kr)
    nec_cfg = sources_cfg.get("nec_data", {})
    if nec_cfg.get("enabled", True):
        collectors["nec_data"] = {
            "instance": NecDataCollector(api_key=nec_cfg.get("api_key") or None),
            "fetch_kwargs": {
                "election_id": nec_cfg.get("default_election_id", "0020240410"),
            },
            "label": "NEC 개방포털 선거결과",
        }

    return collectors


def run_pipeline(
    source_filter: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> Dict[str, int]:
    """
    데이터 수집 파이프라인 실행.

    Returns:
        Dict[source_name, saved_count]
    """
    config = load_config()
    collectors = build_collectors(config)
    summary: Dict[str, int] = {}

    if source_filter and source_filter not in collectors:
        logger.error(f"알 수 없는 소스: {source_filter}. 사용 가능: {list(collectors.keys())}")
        return summary

    targets = {k: v for k, v in collectors.items() if not source_filter or k == source_filter}

    db = SessionLocal() if not dry_run else None
    ingestor = DataIngestor(db) if db else None

    for name, info in targets.items():
        logger.info(f"━━━ [{info['label']}] 수집 시작 ━━━")
        collector = info["instance"]
        kwargs = info["fetch_kwargs"]

        collected = collector.collect(**kwargs)

        if not collected:
            logger.warning(f"[{name}] 수집 데이터 없음")
            summary[name] = 0
            continue

        if verbose or dry_run:
            logger.info(f"[{name}] 수집 결과 미리보기 ({len(collected)}건):")
            for i, item in enumerate(collected[:3]):
                logger.info(f"  [{i+1}] {item.get('agency')} | {item.get('date')} | {item.get('results')}")
            if len(collected) > 3:
                logger.info(f"  ... 외 {len(collected) - 3}건")

        if dry_run:
            logger.info(f"[{name}] DRY-RUN: DB 저장 생략")
            summary[name] = len(collected)
        else:
            saved = ingestor.parse_and_save_json(collected, category=collected[0].get("category", "election"))
            logger.info(f"[{name}] DB 저장 완료: {saved}건")
            summary[name] = saved

    if db:
        db.close()

    return summary


def list_sources():
    """사용 가능한 데이터 소스 목록 출력"""
    config = load_config()
    collectors = build_collectors(config)
    print("\n📡 PollAgg 데이터 소스 목록")
    print("=" * 60)
    for name, info in collectors.items():
        instance = info["instance"]
        has_key = bool(instance.api_key)
        status = "✅ API 키 있음" if has_key else "⚠️  API 키 없음 (샘플 데이터 모드)"
        print(f"  [{name}] {info['label']}")
        print(f"    상태: {status}")
        print(f"    기본 파라미터: {info['fetch_kwargs']}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PollAgg 데이터 수집 파이프라인")
    parser.add_argument("--source", type=str, help="특정 소스만 실행 (예: data_gov_kr)")
    parser.add_argument("--list", action="store_true", help="사용 가능한 소스 목록 출력")
    parser.add_argument("--dry-run", action="store_true", help="DB 저장 없이 미리보기만")
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 출력")
    args = parser.parse_args()

    if args.list:
        list_sources()
        sys.exit(0)

    logger.info("🚀 PollAgg 데이터 수집 파이프라인 시작")
    result = run_pipeline(
        source_filter=args.source,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    print("\n📊 수집 결과 요약")
    print("=" * 40)
    total = 0
    for src, count in result.items():
        action = "미리보기" if args.dry_run else "저장"
        print(f"  {src}: {count}건 {action}")
        total += count
    print(f"  총계: {total}건")
    print()
