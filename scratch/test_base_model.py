import sys
import os

# Add the project directory to sys.path
sys.path.append("/Users/up_main/Desktop/T_Antigravity/dev/stats-optimizer")

from engine.base import BaseStatisticalModel

def test_base_model():
    # Mock data: Support for candidate A and B in 5 different samples
    mock_data = [
        {"A": 45, "B": 35},
        {"A": 47, "B": 33},
        {"A": 44, "B": 36},
        {"A": 46, "B": 34},
        {"A": 48, "B": 32}
    ]
    
    # Initial equal weights
    model = BaseStatisticalModel(mock_data)
    results = model.analyze()
    
    print("--- Analysis with Equal Weights ---")
    print(f"Candidate A Weighted Mean: {results['A']['weighted_mean']:.2f}%")
    print(f"Candidate B Weighted Mean: {results['B']['weighted_mean']:.2f}%")
    print(f"Margin of Error (95%): ±{results['meta']['margin_of_error_95']:.2f}%")
    
    # Test with custom weights (e.g., more recent samples have more weight)
    custom_weights = [1.0, 1.2, 1.5, 2.0, 3.0]
    weighted_model = BaseStatisticalModel(mock_data, weights=custom_weights)
    weighted_results = weighted_model.analyze()
    
    print("\n--- Analysis with Custom Weights (Recent heavier) ---")
    print(f"Candidate A Weighted Mean: {weighted_results['A']['weighted_mean']:.2f}%")
    print(f"Candidate B Weighted Mean: {weighted_results['B']['weighted_mean']:.2f}%")

if __name__ == "__main__":
    test_base_model()
