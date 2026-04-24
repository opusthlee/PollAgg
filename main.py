from typing import List, Dict, Optional
from engine.election import ElectionPredictionModel
from engine.survey import SurveyAnalysisModel
from engine.strategies import BayesianAdjustmentStrategy

class StatsOptimizer:
    """
    Main orchestrator for the Stats-Optimizer system.
    Provides high-level methods for different analysis types.
    """
    
    @staticmethod
    def analyze_election(data: List[Dict], prior_data: Optional[Dict] = None) -> Dict:
        """
        Runs the full election prediction pipeline.
        :param data: List of survey results.
        :param prior_data: Optional historical context to apply Bayesian adjustment.
        """
        model = ElectionPredictionModel(data)
        
        # If prior data is provided, inject the Bayesian strategy at the end of the pipeline
        if prior_data:
            bayesian_strategy = BayesianAdjustmentStrategy(prior_data, strength=0.15)
            model.strategies.append(bayesian_strategy)
            
        analysis = model.analyze()
        predictions = model.simulate_win_probability()
        
        return {
            "status": "success",
            "summary": analysis,
            "prediction": predictions,
            "total_polls_analyzed": len(data)
        }

    @staticmethod
    def analyze_general_survey(data: List[Dict]) -> Dict:
        """
        Runs a standard survey analysis.
        """
        model = SurveyAnalysisModel(data)
        return model.analyze()

if __name__ == "__main__":
    # Example Usage
    sample_polls = [
        {"agency": "Neutral_1", "date": "2026-04-24", "results": {"candidate_a": 44, "candidate_b": 40}, "sample_size": 1000},
        {"agency": "Agency_Alpha", "date": "2026-04-20", "results": {"candidate_a": 48, "candidate_b": 38}, "sample_size": 1000}
    ]
    
    # Optional Prior (e.g., historical party strength)
    historical_prior = {"candidate_a": 41.0, "candidate_b": 43.0}
    
    optimizer = StatsOptimizer()
    result = optimizer.analyze_election(sample_polls, prior_data=historical_prior)
    
    print("--- Election Analysis Result ---")
    print(f"Candidate A Optimized Support: {result['summary']['candidate_a']['weighted_mean']:.2f}%")
    print(f"A Win Prob: {result['prediction']['candidate_a_win_prob']:.1f}%")
    print(f"Calculated Uncertainty: ±{result['prediction']['calculated_uncertainty']:.2f}%")
