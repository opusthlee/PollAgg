import json
import os
import sys
from datetime import datetime

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.database import SessionLocal
from db.models import SurveyData

def ingest_data():
    data_path = "scratch/2026_data_collection.json"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    db = SessionLocal()
    count = 0
    
    try:
        # Flatten all categories into a single list for ingestion
        all_items = []
        
        # Approval Ratings
        for item in raw_data.get("approval_rating", []):
            all_items.append(SurveyData(
                category="approval_rating",
                agency=item["agency"],
                date=item["date"],
                results=item["results"],
                sample_size=item["sample_size"],
                method=item["method"],
                is_active=True
            ))
            
        # Local Election
        for item in raw_data.get("local_election_2026", []):
            all_items.append(SurveyData(
                category="local_election",
                agency=item["agency"],
                date=item["date"],
                results=item["results"],
                sample_size=item["sample_size"],
                method=item["method"],
                region=item.get("region"),
                is_active=True
            ))
            
        # By-elections
        for item in raw_data.get("by_election_2026", []):
            all_items.append(SurveyData(
                category="by_election",
                agency=item["agency"],
                date=item["date"],
                results=item["results"],
                sample_size=item["sample_size"],
                method=item["method"],
                region=item.get("region"),
                is_active=True
            ))
            
        for db_item in all_items:
            # Check for duplicates (simplified)
            existing = db.query(SurveyData).filter(
                SurveyData.agency == db_item.agency,
                SurveyData.date == db_item.date,
                SurveyData.category == db_item.category,
                SurveyData.region == db_item.region
            ).first()
            
            if not existing:
                db.add(db_item)
                count += 1
            else:
                print(f"Skipping duplicate: {db_item.agency} - {db_item.category} ({db_item.date})")
        
        db.commit()
        print(f"Successfully ingested {count} new survey items into pollagg.db")
        
    except Exception as e:
        print(f"Error during ingestion: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    ingest_data()
