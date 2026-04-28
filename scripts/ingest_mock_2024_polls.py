import os
import sys
from sqlalchemy.orm import Session

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.database import SessionLocal
from db.models import SurveyData

def ingest_mock_2024_polls():
    db = SessionLocal()
    
    # Mock polls for Gangwon before 2024-04-10
    # Actual result was DP 44.5, PPP 54.1
    polls = [
        {
            "agency": "Gallup Korea",
            "date": "2024-03-25",
            "results": {"더불어민주당": 46.0, "국민의힘": 52.0, "기타": 2.0},
            "sample_size": 1000,
            "method": "CATI"
        },
        {
            "agency": "Realmeter",
            "date": "2024-04-02",
            "results": {"더불어민주당": 47.5, "국민의힘": 50.5, "기타": 2.0},
            "sample_size": 2000,
            "method": "ARS"
        }
    ]
    
    count = 0
    for p in polls:
        new_poll = SurveyData(
            category="election",
            date=p["date"],
            agency=p["agency"],
            region="강원",
            results=p["results"],
            sample_size=p["sample_size"],
            method=p["method"],
            is_active=True
        )
        db.add(new_poll)
        count += 1
            
    db.commit()
    db.close()
    print(f"Successfully ingested {count} mock 2024 polls for Gangwon")

if __name__ == "__main__":
    ingest_mock_2024_polls()
