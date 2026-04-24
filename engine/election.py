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

    def analyze(self, primary_target: str = "candidate_a") -> Dict:
        """
        Runs validation and pipeline.
        """
        # Step 1: Detect outliers before final weighted mean calculation
        # Use the primary target (or fallback) for outlier detection
        if self.raw_data and primary_target not in self.raw_data[0]["results"]:
            primary_target = list(self.raw_data[0]["results"].keys())[0]

        self.raw_data = self.detector.detect_and_flag(self.raw_data, primary_target)
        
        # Step 2: Run strategy pipeline
        return super().analyze()

    def simulate_win_probability(self, simulations: int = 10000, use_correlated_errors: bool = False, target_1: str = "candidate_a", target_2: str = "candidate_b") -> Dict:
        analysis = self.analyze(primary_target=target_1)
        # Fallback if targets are not found in analysis
        if target_1 not in analysis or target_2 not in analysis:
            return {"error": "Targets not found in data", "target_1_win_prob": 0.0, "target_2_win_prob": 0.0}

        mean_1 = analysis[target_1]["weighted_mean"]
        mean_2 = analysis[target_2]["weighted_mean"]
        
        # 1. Consensus Variance: How much do polls disagree?
        raw_values_1 = [d["results"].get(target_1, mean_1) for d in self.raw_data]
        poll_std = np.std(raw_values_1) if len(raw_values_1) > 1 else 3.0
        
        # 2. Sample Size Impact: More people = less uncertainty
        total_n = sum([d.get("sample_size", 1000) for d in self.raw_data])
        sample_error_reduction = 1 / np.sqrt(total_n / 1000)
        
        # 3. Final Uncertainty Score
        uncertainty = np.clip(poll_std * sample_error_reduction + 1.0, 2.0, 8.0)
        
        if use_correlated_errors:
            # Simulate a systemic polling error (e.g., all polls miss by X points)
            systemic_error = np.random.normal(0, uncertainty * 0.5, simulations)
            # Both targets are affected inversely by the systemic error
            sim_1 = np.random.normal(mean_1, uncertainty * 0.8, simulations) + systemic_error
            sim_2 = np.random.normal(mean_2, uncertainty * 0.8, simulations) - systemic_error
        else:
            sim_1 = np.random.normal(mean_1, uncertainty, simulations)
            sim_2 = np.random.normal(mean_2, uncertainty, simulations)
        
        wins_1 = np.sum(sim_1 > sim_2)
        
        return {
            "target_1_win_prob": (wins_1 / simulations) * 100,
            "target_2_win_prob": (1 - (wins_1 / simulations)) * 100,
            "simulations_run": simulations,
            "calculated_uncertainty": float(uncertainty),
            "used_correlated_errors": use_correlated_errors
        }

