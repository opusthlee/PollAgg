from typing import List, Dict
import copy
from .election import ElectionPredictionModel

class StressTester:
    """
    Tests the fragility of the model by injecting fake shock data.
    """
    def __init__(self, base_data: List[Dict]):
        self.base_data = copy.deepcopy(base_data)

    def run_shock_scenario(self, shock_data: Dict, target_1: str = "candidate_a", target_2: str = "candidate_b") -> Dict:
        """
        Injects a single 'shock' poll to see how much the win probability swings.
        """
        # Run baseline
        base_model = ElectionPredictionModel(self.base_data)
        base_probs = base_model.simulate_win_probability(simulations=5000, target_1=target_1, target_2=target_2)
        
        # Inject shock
        shocked_dataset = copy.deepcopy(self.base_data)
        shocked_dataset.append(shock_data)
        
        shock_model = ElectionPredictionModel(shocked_dataset)
        shock_probs = shock_model.simulate_win_probability(simulations=5000, target_1=target_1, target_2=target_2)
        
        # Calculate Delta
        delta_1 = shock_probs["target_1_win_prob"] - base_probs["target_1_win_prob"]
        
        # Analyze fragility
        fragility_status = "Stable"
        if abs(delta_1) > 20.0:
            fragility_status = "Highly Fragile (Swing > 20%)"
        elif abs(delta_1) > 10.0:
            fragility_status = "Moderately Fragile (Swing > 10%)"
            
        return {
            "baseline_prob_1": base_probs["target_1_win_prob"],
            "shocked_prob_1": shock_probs["target_1_win_prob"],
            "delta_1": delta_1,
            "status": fragility_status
        }
