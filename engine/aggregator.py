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
        
        # 1. Consensus Variance: How much do sources disagree?
        raw_values_1 = [d["results"].get(target_1, mean_1) for d in self.raw_data]
        poll_std = np.std(raw_values_1) if len(raw_values_1) > 1 else 3.0
        
        # 2. Sample Size Impact
        total_n = sum([d.get("sample_size", 1000) for d in self.raw_data])
        sample_error_reduction = 1 / np.sqrt(total_n / 1000)
        
        # 3. Final Uncertainty Score
        uncertainty = np.clip(poll_std * sample_error_reduction + 1.0, 2.0, 10.0)
        
        if use_correlated_errors:
            # Systemic bias simulation
            systemic_error = np.random.normal(0, uncertainty * 0.5, simulations)
            sim_1 = np.random.normal(mean_1, uncertainty * 0.8, simulations) + systemic_error
            sim_2 = np.random.normal(mean_2, uncertainty * 0.8, simulations) - systemic_error
        else:
            sim_1 = np.random.normal(mean_1, uncertainty, simulations)
            sim_2 = np.random.normal(mean_2, uncertainty, simulations)
        
        wins_1 = np.sum(sim_1 > sim_2)
        
        return {
            "target_1": target_1,
            "target_2": target_2,
            "target_1_value": float(mean_1),
            "target_2_value": float(mean_2),
            "expected_gap": float(mean_1 - mean_2),
            "target_1_lead_prob": (wins_1 / simulations) * 100,
            "target_2_lead_prob": (1 - (wins_1 / simulations)) * 100,
            "simulations_run": simulations,
            "calculated_uncertainty": float(uncertainty),
            "used_correlated_errors": use_correlated_errors
        }
