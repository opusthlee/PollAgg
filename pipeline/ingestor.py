from typing import List, Dict, Any
from sqlalchemy.orm import Session
from db.models import Poll

class DataIngestor:
    """
    Handles parsing and saving of polling data from various sources (JSON, Excel, etc.)
    """
    def __init__(self, db: Session):
        self.db = db
        
    def parse_and_save_json(self, raw_data: List[Dict[str, Any]]) -> int:
        """
        Parses a list of JSON-like dictionaries and saves them to the DB.
        """
        saved_count = 0
        for item in raw_data:
            # Basic validation
            if "agency" not in item or "results" not in item:
                continue
                
            poll = Poll(
                agency=item["agency"],
                date=item.get("date", "1970-01-01"),
                results=item["results"],
                sample_size=item.get("sample_size", 1000),
                method=item.get("method", "Unknown"),
                response_rate=item.get("response_rate", None),
                is_manual_override=item.get("is_manual_override", False)
            )
            self.db.add(poll)
            saved_count += 1
            
        self.db.commit()
        return saved_count
        
    def parse_and_save_csv(self, file_path: str):
        """
        Stub for future CSV/Excel parsing.
        Would use pandas to read and convert rows to dicts, then call parse_and_save_json.
        """
        pass
