from typing import List, Dict, Optional
from .base import BaseStatisticalModel
from .strategies import TimeDecayStrategy, ResponseRateStrategy, MethodologyStrategy

class SurveyAnalysisModel(BaseStatisticalModel):
    """
    Opinion poll analyzer using a standard set of survey strategies.
    """
    def __init__(self, data: List[Dict]):
        # Define the default pipeline for surveys
        strategies = [
            TimeDecayStrategy(),
            ResponseRateStrategy(),
            MethodologyStrategy()
        ]
        super().__init__(data, strategies=strategies)
