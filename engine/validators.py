import numpy as np
from typing import List, Dict

class OutlierDetector:
    """
    Identifies data points that deviate significantly from the consensus.
    """
    
    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold # Z-score threshold

    def detect_and_flag(self, data: List[Dict], key: str) -> List[Dict]:
        """
        Calculates Z-scores for a specific metric and flags outliers.
        """
        values = np.array([d["results"].get(key, 0) for d in data])
        if len(values) < 3: # Not enough data for statistical outlier detection
            return data
            
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return data
            
        for i, item in enumerate(data):
            z_score = abs((values[i] - mean) / std)
            if z_score > self.threshold:
                item["is_outlier"] = True
                item["outlier_score"] = z_score
            else:
                item["is_outlier"] = False
                
        return data

class DataValidator:
    """
    Ensures data consistency and integrity.
    """
    @staticmethod
    def validate_proportions(item: Dict):
        """
        Ensures results sum up to something reasonable (e.g., < 100%).
        """
        results = item.get("results", {})
        total = sum(results.values())
        if total > 105: # Allow a small margin for rounding
            raise ValueError(f"Survey results sum to {total}%, which is invalid.")
        return True
