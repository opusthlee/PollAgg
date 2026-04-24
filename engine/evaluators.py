from typing import List, Dict
import copy
from .election import ElectionPredictionModel

class StressTester:
    """
    Tests the fragility of the model by injecting fake shock data.
    """
    def __init__(self, base_data: List[Dict]):
        self.base_data = copy.deepcopy(base_data)

    def run_shock_scenario(self, shock_data: Dict) -> Dict:
        """
        Injects a single 'shock' poll to see how much the win probability swings.
        :param shock_data: A mock poll dictionary (e.g., {"agency": "Shock", "results": {"candidate_a": 30, "candidate_b": 60}, ...})
        """
        # Run baseline
        base_model = ElectionPredictionModel(self.base_data)
        base_probs = base_model.simulate_win_probability(simulations=5000)
        
        # Inject shock
        shocked_dataset = copy.deepcopy(self.base_data)
        shocked_dataset.append(shock_data)
        
        shock_model = ElectionPredictionModel(shocked_dataset)
        shock_probs = shock_model.simulate_win_probability(simulations=5000)
        
        # Calculate Delta
        delta_a = shock_probs["candidate_a_win_prob"] - base_probs["candidate_a_win_prob"]
        
        # Analyze fragility
        fragility_status = "Stable"
        if abs(delta_a) > 20.0:
            fragility_status = "Highly Fragile (Swing > 20%)"
        elif abs(delta_a) > 10.0:
            fragility_status = "Moderately Fragile (Swing > 10%)"
            
        return {
            "baseline_prob_a": base_probs["candidate_a_win_prob"],
            "shocked_prob_a": shock_probs["candidate_a_win_prob"],
            "delta_a": delta_a,
            "status": fragility_status
        }
