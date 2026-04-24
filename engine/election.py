import numpy as np
from typing import List, Dict
from .base import BaseStatisticalModel
from .strategies import TimeDecayStrategy, ResponseRateStrategy, MethodologyStrategy, HouseBiasStrategy
from .validators import OutlierDetector

class ElectionPredictionModel(BaseStatisticalModel):
    """
    Advanced Election Predictor with Outlier Detection and House Bias Correction.
    """
    
    # This can be loaded from a JSON/DB in the future
    BIAS_DATA = {
        "Agency_Alpha": {"candidate_a": 2.5, "candidate_b": -2.5},
        "Agency_Beta": {"candidate_a": -2.0, "candidate_b": 2.0}
    }

    def __init__(self, data: List[Dict]):
        # Define the advanced pipeline
        strategies = [
            HouseBiasStrategy(self.BIAS_DATA), # Correct for bias first
            TimeDecayStrategy(decay_rate=0.07), # More aggressive decay for elections
            ResponseRateStrategy(),
            MethodologyStrategy()
        ]
        super().__init__(data, strategies=strategies)
        self.detector = OutlierDetector(threshold=1.5) # Sensitive detection

    def analyze(self) -> Dict:
        """
        Runs validation and pipeline.
        """
        # Step 1: Detect outliers before final weighted mean calculation
        self.raw_data = self.detector.detect_and_flag(self.raw_data, "candidate_a")
        
        # Step 2: Run strategy pipeline
        return super().analyze()

    def simulate_win_probability(self, simulations: int = 10000, use_correlated_errors: bool = False) -> Dict:
        analysis = self.analyze()
        mean_a = analysis["candidate_a"]["weighted_mean"]
        mean_b = analysis["candidate_b"]["weighted_mean"]
        
        # 1. Consensus Variance: How much do polls disagree?
        raw_values_a = [d["results"].get("candidate_a", mean_a) for d in self.raw_data]
        poll_std = np.std(raw_values_a) if len(raw_values_a) > 1 else 3.0
        
        # 2. Sample Size Impact: More people = less uncertainty
        total_n = sum([d.get("sample_size", 1000) for d in self.raw_data])
        sample_error_reduction = 1 / np.sqrt(total_n / 1000)
        
        # 3. Final Uncertainty Score
        uncertainty = np.clip(poll_std * sample_error_reduction + 1.0, 2.0, 8.0)
        
        if use_correlated_errors:
            # Simulate a systemic polling error (e.g., all polls miss by X points)
            systemic_error = np.random.normal(0, uncertainty * 0.5, simulations)
            # Both candidates are affected inversely by the systemic error
            sim_a = np.random.normal(mean_a, uncertainty * 0.8, simulations) + systemic_error
            sim_b = np.random.normal(mean_b, uncertainty * 0.8, simulations) - systemic_error
        else:
            sim_a = np.random.normal(mean_a, uncertainty, simulations)
            sim_b = np.random.normal(mean_b, uncertainty, simulations)
        
        wins_a = np.sum(sim_a > sim_b)
        
        return {
            "candidate_a_win_prob": (wins_a / simulations) * 100,
            "candidate_b_win_prob": (1 - (wins_a / simulations)) * 100,
            "simulations_run": simulations,
            "calculated_uncertainty": float(uncertainty),
            "used_correlated_errors": use_correlated_errors
        }

