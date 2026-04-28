import numpy as np
from typing import List, Dict, Optional, Any

class BaseStatisticalModel:
    """
    Orchestrator for statistical analysis.
    Uses a pipeline of strategies to refine weights and data.
    """
    
    def __init__(self, data: List[Dict], strategies: Optional[List[Any]] = None):
        """
        :param data: List of raw data points with metadata.
        :param strategies: List of Strategy objects to apply.
        """
        self.raw_data = data
        self.strategies = strategies or []
        self.weights = [1.0] * len(data)
        self.results = {}

    def run_pipeline(self):
        """
        Executes all strategies in order.
        """
        if hasattr(self, "_pipeline_run") and self._pipeline_run:
            return
            
        # Apply each strategy to update weights or data
        for strategy in self.strategies:
            self.weights = strategy.apply(self.raw_data, self.weights)
        
        self._pipeline_run = True
        
    def calculate_weighted_mean(self, key: str) -> float:
        values = np.array([item["results"].get(key, 0) for item in self.raw_data])
        weights = np.array(self.weights)
        
        # Apply outlier penalty: if a point is flagged as an outlier, reduce its weight
        for i, item in enumerate(self.raw_data):
            if item.get("is_outlier", False):
                weights[i] *= 0.5 # Penalty factor
                
        total_weight = np.sum(weights)
        if total_weight == 0: return 0.0
        
        return np.sum(values * weights) / total_weight

    def analyze(self) -> Dict:
        """
        Performs the full analysis pipeline.
        """
        self.run_pipeline()
        
        # Extract keys from the first data point's results
        if not self.raw_data: return {}
        keys = self.raw_data[0]["results"].keys()
        
        analysis = {}
        for key in keys:
            analysis[key] = {
                "weighted_mean": self.calculate_weighted_mean(key),
                "sample_size": len(self.raw_data)
            }
            
        self.results = analysis
        return analysis
