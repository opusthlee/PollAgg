import os
import sys
import time
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.database import SessionLocal
from db.models import SurveyData

def collect_new_data():
    """
    Simulates a daily early-morning data collection task.
    In a real scenario, this would scrape NESDC or other sites.
    """
    db = SessionLocal()
    today = datetime.now().strftime("%Y-%m-%d")
    
    print(f"[{datetime.now()}] Starting daily data collection...")
    
    # 1. Simulate new Presidential Approval Rating
    new_approval = SurveyData(
        category="approval_rating",
        date=today,
        agency="Daily Tracker",
        region="National",
        results={
            "positive": round(random.uniform(62, 68), 1),
            "negative": round(random.uniform(28, 34), 1)
        },
        sample_size=1000,
        method="Mixed",
        is_active=True
    )
    db.add(new_approval)
    
    # 2. Simulate random regional local election data update
    regions = ["서울", "경기", "강원", "인천", "충청"]
    target_region = random.choice(regions)
    
    new_local = SurveyData(
        category="local_election",
        date=today,
        agency="Regional Pulse",
        region=target_region,
        results={
            "DP_lead": round(random.uniform(45, 55), 1),
            "PPP_lead": round(random.uniform(40, 50), 1)
        },
        sample_size=500,
        method="Mixed",
        is_active=True
    )
    db.add(new_local)
    
    db.commit()
    db.close()
    print(f"[{datetime.now()}] Collection complete. Added 2 new records.")

if __name__ == "__main__":
    # If run directly, perform one collection
    collect_new_data()
    
    # CRONTAB INSTRUCTION:
    # To run this every day at 4:00 AM, add the following to your crontab (crontab -e):
    # 0 4 * * * /usr/bin/python3 /Users/up_main/Desktop/T_Antigravity/PollAgg/scripts/auto_collect.py >> /Users/up_main/Desktop/T_Antigravity/PollAgg/logs/collection.log 2>&1
