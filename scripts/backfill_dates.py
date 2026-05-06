"""
기존 polls 행의 raw `date`를 (survey_date, survey_year, survey_week)로 정규화하여 채움.

사용법 (backend 컨테이너 내부):
  python scripts/backfill_dates.py --dry-run    # 변경 건수만 보고
  python scripts/backfill_dates.py              # 실제 적용
"""
import argparse
import logging
import sys
from collections import Counter

# Project root을 path에 추가 (스크립트가 ~/pollagg/scripts/에서 실행되든 컨테이너에서든)
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from db.models import SurveyData
from utils.dates import normalize_raw_date

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill_dates")


def run(dry_run: bool) -> None:
    db = SessionLocal()
    try:
        total = db.query(SurveyData).count()
        logger.info(f"전체 레코드: {total}")

        stats = Counter()
        unparseable_samples: list[str] = []
        updated = 0
        batch = 500

        # 모든 행 페이지네이션
        offset = 0
        while True:
            rows = (
                db.query(SurveyData)
                .order_by(SurveyData.id)
                .offset(offset)
                .limit(batch)
                .all()
            )
            if not rows:
                break

            for row in rows:
                sd, sy, sw = normalize_raw_date(row.date)
                changed = (
                    row.survey_date != sd
                    or row.survey_year != sy
                    or row.survey_week != sw
                )
                if changed:
                    if not dry_run:
                        row.survey_date = sd
                        row.survey_year = sy
                        row.survey_week = sw
                    updated += 1

                # 통계 분류
                if sd is not None:
                    stats["A. survey_date 채움 (ISO)"] += 1
                elif sw is not None:
                    stats["C. survey_year+week (주차)"] += 1
                elif sy is not None:
                    stats["X. survey_year만 (연도만)"] += 1
                else:
                    stats["Z. 모두 NULL (파싱 실패)"] += 1
                    if len(unparseable_samples) < 10 and row.date:
                        unparseable_samples.append(row.date)

            if not dry_run:
                db.commit()
            offset += batch
            logger.info(f"  진행: {offset}/{total}")

        logger.info("=" * 60)
        logger.info(f"{'DRY-RUN ' if dry_run else ''}변경 대상: {updated}건")
        for k, v in sorted(stats.items()):
            logger.info(f"  {v:>5} | {k}")
        if unparseable_samples:
            logger.info(f"  unparseable 예시: {unparseable_samples}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="DB에 반영하지 않고 통계만 출력")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
