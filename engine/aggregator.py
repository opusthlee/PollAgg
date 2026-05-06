import numpy as np
from typing import List, Dict, Optional
from .base import BaseStatisticalModel
from .strategies import TimeDecayStrategy, ResponseRateStrategy, MethodologyStrategy, HouseBiasStrategy
from .validators import OutlierDetector

class AggregateAnalysisEngine(BaseStatisticalModel):
    """
    General-Purpose Statistical Aggregator Engine.
    V3: Domain-agnostic design for Marketing, Politics, and Social Stats.
    """
    
    def __init__(self, data: List[Dict], bias_data: Optional[Dict] = None, decay_rate: float = 0.05):
        # Define the general-purpose pipeline
        strategies = [
            TimeDecayStrategy(decay_rate=decay_rate),
            ResponseRateStrategy(),
            MethodologyStrategy()
        ]
        
        if bias_data:
            strategies.insert(0, HouseBiasStrategy(bias_data))
            
        super().__init__(data, strategies=strategies)
        self.detector = OutlierDetector(threshold=2.0) # Standard detection

    def analyze(self, primary_target: Optional[str] = None) -> Dict:
        """
        Runs validation and pipeline.
        """
        if not self.raw_data:
            return {}
            
        # Step 1: Detect outliers
        if not primary_target:
            primary_target = list(self.raw_data[0]["results"].keys())[0]

        self.raw_data = self.detector.detect_and_flag(self.raw_data, primary_target)
        
        # Step 2: Run strategy pipeline
        return super().analyze()

    def simulate_superiority(self, simulations: int = 10000, use_correlated_errors: bool = False, target_1: str = None, target_2: str = None) -> Dict:
        """
        Simulates the probability of target_1 being superior to target_2.
        Commonly used for 'Win Probability' in elections or 'Market Lead' in business.
        """
        analysis = self.analyze(primary_target=target_1)
        
        # Auto-detect targets if not provided
        if not target_1 or not target_2:
            keys = list(analysis.keys())
            if len(keys) >= 2:
                target_1 = target_1 or keys[0]
                target_2 = target_2 or keys[1]
            else:
                return {"error": "Insufficient targets for comparison"}

        if target_1 not in analysis or target_2 not in analysis:
            return {"error": "Targets not found in data"}

        mean_1 = analysis[target_1]["weighted_mean"]
        mean_2 = analysis[target_2]["weighted_mean"]

        n_polls = len(self.raw_data)

        # 1. Consensus Variance: How much do sources disagree?
        raw_values_1 = [d["results"].get(target_1, mean_1) for d in self.raw_data]
        poll_std = np.std(raw_values_1) if len(raw_values_1) > 1 else 3.0

        # 2. Sample Size Impact (CLT 기반 — 표본수 합산 효과)
        total_n = sum([d.get("sample_size", 1000) for d in self.raw_data])
        sample_error_reduction = 1 / np.sqrt(total_n / 1000)

        # 3. Small-sample 패널티 — n_polls 적을수록 mean 추정 자체의 불확실성↑
        # n=1: +5pp, n=5: +1pp, n=10+: 0. House-effect 보정의 단순 근사.
        small_n_penalty = max(0.0, 5.0 / max(n_polls, 1) - 0.5)

        # 4. Final Uncertainty Score
        uncertainty = float(np.clip(
            poll_std * sample_error_reduction + 1.0 + small_n_penalty,
            2.0, 10.0,
        ))

        import math
        if use_correlated_errors:
            std_total = math.sqrt(2 * (0.8 * uncertainty)**2 + 2 * (0.5 * uncertainty)**2)
        else:
            std_total = math.sqrt(2 * (uncertainty**2))

        gap = mean_1 - mean_2
        z_score = gap / std_total if std_total > 0 else 0
        prob_1_raw = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))

        # 5. UI/디스플레이용 확률 cap — 0.5 ~ 99.5% 범위.
        #    raw 확률은 별도 필드에 보존 (분석가가 필요시 참조).
        prob_1_capped = max(0.005, min(0.995, prob_1_raw))

        # 6. 데이터 품질 경고
        warnings = []
        if n_polls < 10:
            warnings.append(f"sample_too_small: 폴 {n_polls}개 (10개 미만 — 추정 신뢰도 낮음)")
        if uncertainty <= 2.0 + 1e-9:
            warnings.append("uncertainty_floor_hit: 불확실성 하한(2.0) 도달")
        if abs(prob_1_raw - prob_1_capped) > 1e-9:
            warnings.append(f"probability_capped: raw={prob_1_raw*100:.4f}% → 표시값 {prob_1_capped*100:.2f}%")

        return {
            "target_1": target_1,
            "target_2": target_2,
            "target_1_value": float(mean_1),
            "target_2_value": float(mean_2),
            "expected_gap": float(gap),
            "target_1_lead_prob": prob_1_capped * 100,
            "target_2_lead_prob": (1 - prob_1_capped) * 100,
            "target_1_lead_prob_raw": prob_1_raw * 100,
            "simulations_run": 0,
            "calculated_uncertainty": uncertainty,
            "n_polls": n_polls,
            "warnings": warnings,
            "used_correlated_errors": use_correlated_errors,
        }
