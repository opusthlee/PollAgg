from typing import List, Dict
import copy
from .aggregator import AggregateAnalysisEngine

class StressTester:
    """
    Tests the fragility of the model by injecting fake shock data.
    """
    def __init__(self, base_data: List[Dict]):
        self.base_data = copy.deepcopy(base_data)

    def run_shock_scenario(self, shock_data: Dict, target_1: str = "target_a", target_2: str = "target_b") -> Dict:
        """
        Injects a single 'shock' data point to see how much the lead probability swings.
        """
        # Run baseline
        base_model = AggregateAnalysisEngine(self.base_data)
        base_probs = base_model.simulate_superiority(simulations=5000, target_1=target_1, target_2=target_2)
        
        # Inject shock
        shocked_dataset = copy.deepcopy(self.base_data)
        shocked_dataset.append(shock_data)
        
        shock_model = AggregateAnalysisEngine(shocked_dataset)
        shock_probs = shock_model.simulate_superiority(simulations=5000, target_1=target_1, target_2=target_2)
        
        # Calculate Delta
        prob_key = "target_1_lead_prob"
        
        # Validation: Check if simulate_superiority returned an error
        if "error" in base_probs or "error" in shock_probs:
            return {
                "status": "Error: Targets not found in simulation",
                "baseline_prob_a": 0,
                "shocked_prob_a": 0,
                "delta_a": 0
            }

        delta_1 = shock_probs[prob_key] - base_probs[prob_key]
        
        # Analyze fragility
        fragility_status = "Stable"
        if abs(delta_1) > 20.0:
            fragility_status = "Highly Fragile (Swing > 20%)"
        elif abs(delta_1) > 10.0:
            fragility_status = "Moderately Fragile (Swing > 10%)"
            
        return {
            "baseline_prob_a": base_probs[prob_key],
            "shocked_prob_a": shock_probs[prob_key],
            "delta_a": delta_1,
            "status": fragility_status
        }
