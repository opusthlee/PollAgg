import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from db.models import SurveyData
import numpy as np

logger = logging.getLogger(__name__)

class ModelValidator:
    """
    실제 결과(Actual Result)와 여론조사 예측치를 비교하여 모델 성능 및 기관 편향성을 분석합니다.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_comparison_report(self, category: str = "election", election_date: str = "2024-04-10", region: str = None, district: str = None):
        """
        특정 선거의 실제 결과와 여론조사들을 비교 분석합니다.
        범위(region, district)를 지정하여 지역별 정확도를 분석할 수 있습니다.
        """
        # 1. 실제 결과 데이터 가져오기
        actual_query = self.db.query(SurveyData).filter(
            SurveyData.category == "election_result", 
            SurveyData.date == election_date
        )
        
        if region:
            actual_query = actual_query.filter(SurveyData.region == region)
        if district:
            actual_query = actual_query.filter(SurveyData.district.like(f"%{district}%"))
            
        actual = actual_query.first()
        
        if not actual:
            logger.warning(f"[{election_date}] {region or '전국'} {district or ''}에 해당하는 실제 결과 데이터가 없습니다.")
            return None

        actual_results = actual.results  # e.g., {"더불어민주당": 45.2, "국민의힘": 38.0, ...}
        
        # 2. 분석 대상 여론조사들 가져오기 (선거일 이전 데이터)
        poll_query = self.db.query(SurveyData).filter(
            SurveyData.category == category, 
            SurveyData.date < election_date
        )
        
        if region:
            poll_query = poll_query.filter(SurveyData.region == region)
        if district:
            poll_query = poll_query.filter(SurveyData.district.like(f"%{district}%"))
            
        polls = poll_query.all()
        
        if not polls:
            logger.warning(f"{region or '전국'} {district or ''}에 비교 분석할 여론조사 데이터가 없습니다.")
            return None

        # 3. 기관별/방법별 오차 분석
        agency_metrics = {}
        method_metrics = {"전화면접": [], "ARS": [], "Unknown": []}
        
        all_errors = []

        for poll in polls:
            agency = poll.agency
            method = poll.method or "Unknown"
            poll_results = poll.results
            
            # 공통된 키(정당/후보)에 대해서만 오차 계산
            errors = []
            for key in actual_results:
                if key in poll_results:
                    # 단순 오차 (예측 - 실제) -> 편향 확인용
                    bias = poll_results[key] - actual_results[key]
                    # 절대 오차 -> 정확도 확인용
                    abs_error = abs(bias)
                    errors.append({
                        "target": key,
                        "bias": bias,
                        "abs_error": abs_error
                    })
            
            if not errors: continue

            avg_abs_error = np.mean([e["abs_error"] for e in errors])
            all_errors.append(avg_abs_error)

            # 기관별 누적
            if agency not in agency_metrics:
                agency_metrics[agency] = {"errors": [], "biases": {k: [] for k in actual_results}}
            
            agency_metrics[agency]["errors"].append(avg_abs_error)
            for e in errors:
                agency_metrics[agency]["biases"][e["target"]].append(e["bias"])

            # 방법별 누적
            if method in method_metrics:
                method_metrics[method].append(avg_abs_error)

        # 4. 최종 리포트 구성
        report = {
            "election": actual.agency,
            "election_date": election_date,
            "total_polls_analyzed": len(polls),
            "overall_mae": np.mean(all_errors) if all_errors else 0,
            "agency_analysis": [],
            "method_analysis": {}
        }

        for agency, data in agency_metrics.items():
            report["agency_analysis"].append({
                "agency": agency,
                "avg_error": np.mean(data["errors"]),
                "bias_by_target": {k: float(np.mean(v)) for k, v in data["biases"].items() if v},
                "poll_count": len(data["errors"])
            })

        for method, errs in method_metrics.items():
            if errs:
                report["method_analysis"][method] = np.mean(errs)

        # 평균 오차 낮은 순으로 정렬
        report["agency_analysis"].sort(key=lambda x: x["avg_error"])
        
        return report
