from typing import List, Dict, Optional
from engine.aggregator import AggregateAnalysisEngine
from engine.strategies import BayesianAdjustmentStrategy
from engine.processors import TimeSeriesSmoother
from engine.evaluators import StressTester

class StatsOptimizer:
    """
    Main orchestrator for the PollAgg General-Purpose Engine.
    V3: Domain-agnostic orchestration for Politics, Marketing, and Research.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            "use_correlated_errors": False,
            "use_smoothing": False,
            "run_stress_test": False,
            "category": "general"
        }

    def analyze_dataset(self, data: List[Dict], prior_data: Optional[Dict] = None, fundamentals: Optional[Dict] = None, bias_data: Optional[Dict] = None) -> Dict:
        """
        Runs the full analysis pipeline on any dataset.
        """
        if not data:
            return {"status": "error", "message": "No data provided"}

        # Initialize the generic engine with optional bias data
        engine = AggregateAnalysisEngine(data, bias_data=bias_data)
        
        # 1. Feature: Bayesian Adjustment (e.g., Fundamentals in politics or Brand Prior in marketing)
        if prior_data or fundamentals:
            bayesian_strategy = BayesianAdjustmentStrategy(
                prior_results=prior_data or {}, 
                fundamentals_score=fundamentals,
                strength=0.15
            )
            engine.strategies.append(bayesian_strategy)
            
        analysis = engine.analyze()
        
        # Extract dynamic targets from config or auto-detect
        targets = list(analysis.keys())
        target_1 = self.config.get("target_1")
        target_2 = self.config.get("target_2")
        
        # Fallback if provided targets are not in the data
        if not target_1 or target_1 not in analysis:
            target_1 = targets[0] if len(targets) > 0 else None
        if not target_2 or target_2 not in analysis:
            target_2 = targets[1] if len(targets) > 1 else None

        # 2. Feature: Superiority/Lead Simulation
        predictions = {}
        if target_1 and target_2:
            use_corr = self.config.get("use_correlated_errors", False)
            predictions = engine.simulate_superiority(
                use_correlated_errors=use_corr, 
                target_1=target_1, 
                target_2=target_2
            )
        
        result = {
            "status": "success",
            "category": self.config.get("category", "general"),
            "summary": analysis,
            "prediction": predictions,
            "total_samples": len(data)
        }
        
        # 3. Feature: Time-Series Smoothing
        if self.config.get("use_smoothing", False):
            smoother = TimeSeriesSmoother(window_days=7)
            result["trend_lines"] = smoother.smooth(data, target_keys=[target_1, target_2])
            
        # 4. Feature: Stress Testing
        # 의미 있는 stress test: 현재 리딩 후보를 challenge하는 방향으로 shock 주입.
        # (이미 우세한 쪽을 더 밀면 확률이 saturation에 걸려 변동 0이 되어버림)
        if self.config.get("run_stress_test", False) and target_1 and target_2:
            tester = StressTester(data)
            mean_1 = analysis.get(target_1, {}).get("weighted_mean", 0)
            mean_2 = analysis.get(target_2, {}).get("weighted_mean", 0)
            if mean_1 >= mean_2:
                # target_1이 리드 → target_2 우세 shock
                shock_results = {target_1: 40, target_2: 50}
            else:
                # target_2가 리드 → target_1 우세 shock
                shock_results = {target_1: 50, target_2: 40}
            mock_shock = {
                "agency": "Shock_Simulation", "date": "2024-04-10",
                "survey_date": "2024-04-10",
                "results": shock_results,
                "sample_size": 2000, "response_rate": 0.2, "method": "Digital",
            }
            result["stress_test_report"] = tester.run_shock_scenario(mock_shock, target_1=target_1, target_2=target_2)

        return result

if __name__ == "__main__":
    # Example: Marketing Research Usage
    market_data = [
        {"agency": "Survey_X", "date": "2026-04-10", "results": {"brand_apple": 45, "brand_samsung": 42}, "sample_size": 2000},
        {"agency": "Survey_Y", "date": "2026-04-20", "results": {"brand_apple": 48, "brand_samsung": 38}, "sample_size": 2000},
    ]
    
    config = {
        "category": "marketing",
        "target_1": "brand_apple",
        "target_2": "brand_samsung",
        "use_smoothing": True
    }
    
    optimizer = StatsOptimizer(config=config)
    result = optimizer.analyze_dataset(market_data)
    
    print(f"=== [PollAgg Analysis: {result['category'].upper()}] ===")
    print(f"Lead Prob: {result['prediction'].get('target_1_lead_prob', 0):.1f}% for {result['prediction'].get('target_1')}")
