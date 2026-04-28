import os
import sys
from sqlalchemy.orm import Session

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.database import SessionLocal
from db.models import SurveyData

def ingest_regional_results():
    db = SessionLocal()
    
    results = [
        {
            "region": "서울",
            "results": {"더불어민주당": 52.2, "국민의힘": 46.3, "기타": 1.5}
        },
        {
            "region": "경기",
            "results": {"더불어민주당": 54.8, "국민의힘": 42.8, "기타": 2.4}
        },
        {
            "region": "인천",
            "results": {"더불어민주당": 53.5, "국민의힘": 45.0, "기타": 1.5}
        },
        {
            "region": "강원",
            "results": {"더불어민주당": 44.5, "국민의힘": 54.1, "기타": 1.4}
        },
        {
            "region": "영남",
            "results": {"더불어민주당": 38.5, "국민의힘": 58.2, "기타": 3.3}
        },
        {
            "region": "호남",
            "results": {"더불어민주당": 82.5, "국민의힘": 12.3, "기타": 5.2}
        },
        {
            "region": "충청",
            "results": {"더불어민주당": 51.2, "국민의힘": 46.8, "기타": 2.0}
        }
    ]
    
    count = 0
    for res in results:
        existing = db.query(SurveyData).filter(
            SurveyData.category == "election_result",
            SurveyData.date == "2024-04-10",
            SurveyData.region == res["region"]
        ).first()
        
        if not existing:
            new_res = SurveyData(
                category="election_result",
                date="2024-04-10",
                agency="중앙선거관리위원회 (공식 결과)",
                region=res["region"],
                results=res["results"],
                method="Actual",
                is_active=True
            )
            db.add(new_res)
            count += 1
            
    db.commit()
    db.close()
    print(f"Successfully ingested {count} regional election results for 2024-04-10")

if __name__ == "__main__":
    ingest_regional_results()
