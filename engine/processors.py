from typing import List, Dict
import numpy as np
from datetime import datetime, timedelta

class TimeSeriesSmoother:
    """
    Processes discrete poll data points into a continuous smoothed trend line.
    """
    def __init__(self, window_days: int = 7):
        self.window_days = window_days

    def smooth(self, data: List[Dict], target_keys: List[str]) -> Dict[str, List[Dict]]:
        """
        Creates a simple moving average trend line.
        :param data: List of poll dictionaries (must have 'date' and 'results').
        :param target_keys: Keys to smooth (e.g., ["candidate_a", "candidate_b"]).
        :return: A dictionary of smoothed trends.
        """
        if not data:
            return {}

        def _safe_parse_date(d_str):
            try:
                return datetime.strptime(d_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                # 기본값 또는 건너뛰기를 위해 None 반환
                return None

        # 유효한 날짜를 가진 데이터만 필터링 및 파싱
        parsed_data = []
        for d in data:
            dt = _safe_parse_date(d.get("date"))
            if dt:
                parsed_data.append({**d, "_dt": dt})

        if not parsed_data:
            return {}

        # Sort data by date
        parsed_data.sort(key=lambda x: x["_dt"])
        
        start_date = parsed_data[0]["_dt"]
        end_date = parsed_data[-1]["_dt"]
        
        trend_lines = {key: [] for key in target_keys}
        
        # Generate daily points
        current_date = start_date
        while current_date <= end_date:
            window_start = current_date - timedelta(days=self.window_days)
            
            # Find polls within the window
            window_polls = [
                d for d in parsed_data 
                if window_start <= d["_dt"] <= current_date
            ]
            
            if window_polls:
                for key in target_keys:
                    values = [p["results"].get(key) for p in window_polls if key in p["results"]]
                    if values:
                        avg_val = np.mean(values)
                        trend_lines[key].append({
                            "date": current_date.strftime("%Y-%m-%d"),
                            "smoothed_value": float(avg_val)
                        })
            
            current_date += timedelta(days=1)
            
        return trend_lines
