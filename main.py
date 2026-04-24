from typing import List, Dict, Optional
from engine.election import ElectionPredictionModel
from engine.survey import SurveyAnalysisModel
from engine.strategies import BayesianAdjustmentStrategy
from engine.processors import TimeSeriesSmoother
from engine.evaluators import StressTester

class StatsOptimizer:
    """
    Main orchestrator for the Stats-Optimizer system.
    V2 introduces toggleable advanced features via a configuration dictionary.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            "use_correlated_errors": False,
            "use_smoothing": False,
            "run_stress_test": False
        }

    def analyze_election(self, data: List[Dict], prior_data: Optional[Dict] = None, fundamentals: Optional[Dict] = None) -> Dict:
        """
        Runs the full election prediction pipeline.
        """
        model = ElectionPredictionModel(data)
        
        # 1. Feature: Fundamentals Prior
        if prior_data or fundamentals:
            bayesian_strategy = BayesianAdjustmentStrategy(
                prior_results=prior_data or {}, 
                fundamentals_score=fundamentals,
                strength=0.15
            )
            model.strategies.append(bayesian_strategy)
            
        analysis = model.analyze()
        
        # 2. Feature: Correlated Errors
        use_corr = self.config.get("use_correlated_errors", False)
        predictions = model.simulate_win_probability(use_correlated_errors=use_corr)
        
        result = {
            "status": "success",
            "summary": analysis,
            "prediction": predictions,
            "total_polls_analyzed": len(data)
        }
        
        # 3. Feature: Time-Series Smoothing
        if self.config.get("use_smoothing", False):
            smoother = TimeSeriesSmoother(window_days=7)
            result["trend_lines"] = smoother.smooth(data, target_keys=["candidate_a", "candidate_b"])
            
        # 4. Feature: Stress Testing
        if self.config.get("run_stress_test", False):
            tester = StressTester(data)
            # Inject a sudden 15-point swing to B
            mock_shock = {
                "agency": "Shock_Poll", "date": "2026-04-25",
                "results": {"candidate_a": 35, "candidate_b": 50},
                "sample_size": 2000, "response_rate": 0.2, "method": "CATI"
            }
            result["stress_test_report"] = tester.run_shock_scenario(mock_shock)

        return result

    def analyze_general_survey(self, data: List[Dict]) -> Dict:
        model = SurveyAnalysisModel(data)
        return model.analyze()

if __name__ == "__main__":
    # Example Usage
    sample_polls = [
        {"agency": "Neutral_1", "date": "2026-04-18", "results": {"candidate_a": 42, "candidate_b": 41}, "sample_size": 1000},
        {"agency": "Agency_Alpha", "date": "2026-04-20", "results": {"candidate_a": 48, "candidate_b": 38}, "sample_size": 1000},
        {"agency": "Neutral_2", "date": "2026-04-24", "results": {"candidate_a": 45, "candidate_b": 40}, "sample_size": 1000}
    ]
    
    historical_prior = {"candidate_a": 41.0, "candidate_b": 43.0}
    fundamentals = {"candidate_a": +1.5, "candidate_b": -1.0} # Good economy for A
    
    # Run with all V2 features ON
    v2_config = {
        "use_correlated_errors": True,
        "use_smoothing": True,
        "run_stress_test": True
    }
    
    optimizer = StatsOptimizer(config=v2_config)
    result = optimizer.analyze_election(sample_polls, prior_data=historical_prior, fundamentals=fundamentals)
    
    print("=== [V2 Stats-Optimizer Analysis] ===")
    print(f"Optimized Support: A={result['summary']['candidate_a']['weighted_mean']:.2f}%, B={result['summary']['candidate_b']['weighted_mean']:.2f}%")
    print(f"A Win Prob: {result['prediction']['candidate_a_win_prob']:.1f}% (Correlated Errors: {result['prediction']['used_correlated_errors']})")
    
    if "trend_lines" in result:
        print("\n[Trend Line Points Generated]")
        print(f"A Trend Points: {len(result['trend_lines']['candidate_a'])}")
        
    if "stress_test_report" in result:
        report = result['stress_test_report']
        print(f"\n[Stress Test Report] Status: {report['status']}")
        print(f"Baseline Win Prob: {report['baseline_prob_a']:.1f}% -> Shocked Prob: {report['shocked_prob_a']:.1f}%")
        print(f"Delta: {report['delta_a']:.1f}%")

