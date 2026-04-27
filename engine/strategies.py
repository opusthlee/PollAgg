import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """
    Abstract base class for all statistical strategies.
    Autoresearch can subclass this to add new optimization logic.
    """
    @abstractmethod
    def apply(self, data: List[Dict], weights: List[float]) -> List[float]:
        """
        Apply the strategy and return the updated weights.
        """
        pass

class TimeDecayStrategy(BaseStrategy):
    """
    Applies exponential decay based on the recency of the data.
    """
    def __init__(self, decay_rate: float = 0.05, reference_date: datetime = None):
        self.decay_rate = decay_rate
        self.reference_date = reference_date or datetime.now()

    def apply(self, data: List[Dict], weights: List[float]) -> List[float]:
        new_weights = []
        for i, item in enumerate(data):
            # Expects item to have a 'date' field
            date_str = item.get("date")
            if not date_str:
                new_weights.append(weights[i])
                continue
                
            try:
                item_date = datetime.strptime(date_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                # 날짜 파싱 실패 시 현재 날짜로부터 30일 전으로 가정하거나 가중치 보존
                if date_str:
                    logger.warning(f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD. Skipping decay.")
                new_weights.append(weights[i])
                continue

            days_diff = (self.reference_date - item_date).days
            decay = np.exp(-self.decay_rate * max(0, days_diff))
            new_weights.append(weights[i] * decay)
        return new_weights

class ResponseRateStrategy(BaseStrategy):
    """
    Adjusts weights based on the response rate quality.
    """
    def __init__(self, target_rate: float = 0.15, floor: float = 0.5):
        self.target_rate = target_rate
        self.floor = floor

    def apply(self, data: List[Dict], weights: List[float]) -> List[float]:
        new_weights = []
        # k: steepness, mid: inflection point
        k = 30.0
        mid = 0.10
        amplitude = 1.2 - self.floor
        
        for i, item in enumerate(data):
            rr = item.get("response_rate")
            if rr is None:
                rr = self.target_rate
                
            # Sigmoid formula: floor + (amplitude / (1 + e^(-k(x - mid))))
            rr_weight = self.floor + (amplitude / (1 + np.exp(-k * (rr - mid))))
            new_weights.append(weights[i] * rr_weight)
        return new_weights

class MethodologyStrategy(BaseStrategy):
    """
    Weights different survey methodologies (e.g., CATI vs ARS).
    """
    def __init__(self, method_weights: Dict[str, float] = None):
        self.method_weights = method_weights or {"CATI": 1.2, "ARS": 0.8}

    def apply(self, data: List[Dict], weights: List[float]) -> List[float]:
        new_weights = []
        for i, item in enumerate(data):
            method = item.get("method", "Unknown")
            w = self.method_weights.get(method, 1.0)
            new_weights.append(weights[i] * w)
        return new_weights

class HouseBiasStrategy(BaseStrategy):
    """
    Corrects for known pollster bias (House Effect).
    Note: This modifies the results data, not just the weights.
    """
    def __init__(self, bias_table: Dict[str, Dict[str, float]]):
        self.bias_table = bias_table

    def apply(self, data: List[Dict], weights: List[float]) -> List[float]:
        for item in data:
            agency = item.get("agency")
            if agency in self.bias_table:
                biases = self.bias_table[agency]
                for key, bias_val in biases.items():
                    if key in item["results"]:
                        item["results"][key] -= bias_val
        return weights

class BayesianAdjustmentStrategy(BaseStrategy):
    """
    Adjusts results based on a 'Prior' belief. 
    In V2, this incorporates both past polls and 'Fundamentals' (e.g., economic indicators).
    """
    def __init__(self, prior_results: Dict[str, float], fundamentals_score: Dict[str, float] = None, strength: float = 0.2):
        self.prior_results = prior_results
        self.fundamentals_score = fundamentals_score or {}
        self.strength = strength # Base strength of the prior

    def apply(self, data: List[Dict], weights: List[float]) -> List[float]:
        for item in data:
            results = item["results"]
            for key, prior_val in self.prior_results.items():
                if key in results:
                    # If fundamentals exist for this candidate, adjust the prior slightly
                    fund_boost = self.fundamentals_score.get(key, 0.0)
                    adjusted_prior = prior_val + fund_boost
                    
                    # Blend the poll result with the adjusted prior
                    results[key] = (results[key] * (1 - self.strength)) + (adjusted_prior * self.strength)
        return weights

