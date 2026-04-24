import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append("/Users/up_main/Desktop/T_Antigravity/dev/stats-optimizer")

from engine.base import BaseStatisticalModel
from engine.survey import SurveyAnalysisModel
from engine.election import ElectionPredictionModel

def integrated_test():
    print("=== [Stats-Optimizer Integrated Test] ===\n")
    
    # 1. Raw Data from 3 different surveys
    raw_surveys = [
        {
            "agency": "Agency_Alpha", # Leans A (+2.5)
            "date": "2026-04-10", 
            "results": {"candidate_a": 48.0, "candidate_b": 38.0}, # Very early, biased
            "response_rate": 0.04, # Low
            "method": "ARS",
            "sample_size": 1000
        },
        {
            "agency": "Agency_Beta", # Leans B (-2.0)
            "date": "2026-04-20", 
            "results": {"candidate_a": 42.0, "candidate_b": 44.0}, # More recent
            "response_rate": 0.12, 
            "method": "CATI",
            "sample_size": 1000
        },
        {
            "agency": "Neutral_Poll", # Neutral
            "date": "2026-04-24", # Most recent
            "results": {"candidate_a": 44.0, "candidate_b": 40.0},
            "response_rate": 0.18, # High
            "method": "CATI",
            "sample_size": 2000 # Large sample
        }
    ]

    # --- Layer 1: Simple Base Analysis ---
    base_data = [s["results"] for s in raw_surveys]
    base_model = BaseStatisticalModel(base_data)
    base_results = base_model.analyze()
    print(f"[Layer 1] Simple Average: A={base_results['candidate_a']['weighted_mean']:.2f}%, B={base_results['candidate_b']['weighted_mean']:.2f}%")

    # --- Layer 2: Survey Specialized Analysis (Time/Method weighting) ---
    survey_model = SurveyAnalysisModel(raw_surveys)
    survey_results = survey_model.analyze()
    print(f"[Layer 2] Weighted Average: A={survey_results['candidate_a']['weighted_mean']:.2f}%, B={survey_results['candidate_b']['weighted_mean']:.2f}%")
    print("  * Note: Recent and high-response CATI polls weighted more.")

    # --- Layer 3: Election Prediction (House Effect + Win Prob) ---
    election_model = ElectionPredictionModel(raw_surveys)
    election_results = election_model.analyze()
    print(f"[Layer 3] Corrected Analysis: A={election_results['candidate_a']['weighted_mean']:.2f}%, B={election_results['candidate_b']['weighted_mean']:.2f}%")
    
    # Simulation
    probs = election_model.simulate_win_probability()
    print(f"\n[Final Insight] Win Probability:")
    print(f"  - Candidate A: {probs['candidate_a_win_prob']:.1f}%")
    print(f"  - Candidate B: {probs['candidate_b_win_prob']:.1f}%")
    print(f"  (Based on {probs['simulations_run']} simulations)")

if __name__ == "__main__":
    integrated_test()
