import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append("/Users/up_main/Desktop/T_Antigravity/dev/stats-optimizer")

from engine.election import ElectionPredictionModel

def strategy_pipeline_test():
    print("=== [Strategy-Based Pipeline Test] ===\n")
    
    # 1. Mock Data including an Outlier
    # Candidate A usually around 44, but one poll says 55
    data = [
        {
            "agency": "Neutral_1", 
            "date": "2026-04-24", 
            "results": {"candidate_a": 44.0, "candidate_b": 40.0},
            "response_rate": 0.15, "method": "CATI"
        },
        {
            "agency": "Neutral_2", 
            "date": "2026-04-23", 
            "results": {"candidate_a": 43.5, "candidate_b": 41.0},
            "response_rate": 0.14, "method": "CATI"
        },
        {
            "agency": "Agency_Alpha", # Has +2.5 bias for A
            "date": "2026-04-22", 
            "results": {"candidate_a": 47.0, "candidate_b": 38.0}, # Raw 47 -> Corrected 44.5
            "response_rate": 0.10, "method": "ARS"
        },
        {
            "agency": "Rogue_Pollster", # OUTLIER
            "date": "2026-04-24", 
            "results": {"candidate_a": 55.0, "candidate_b": 30.0}, # Way off!
            "response_rate": 0.03, "method": "ARS"
        }
    ]

    model = ElectionPredictionModel(data)
    results = model.analyze()
    
    print(f"Optimized Candidate A 지지율: {results['candidate_a']['weighted_mean']:.2f}%")
    print(f"Optimized Candidate B 지지율: {results['candidate_b']['weighted_mean']:.2f}%")

    # Check if Outlier was detected
    for i, item in enumerate(model.raw_data):
        if item.get("is_outlier"):
            print(f"\n[ALERT] Outlier detected from {item['agency']}: Support {item['results']['candidate_a']}%")
            print(f"  * Outlier Score: {item['outlier_score']:.2f}")

    probs = model.simulate_win_probability()
    print(f"\n[Final Prediction] A 승리 확률: {probs['candidate_a_win_prob']:.1f}%")

if __name__ == "__main__":
    strategy_pipeline_test()
