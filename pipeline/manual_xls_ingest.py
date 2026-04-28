import os
import sys
import openpyxl
from sqlalchemy.orm import Session

# Add PollAgg to path
sys.path.append("/Users/up_main/Desktop/T_Antigravity/PollAgg")

from db.database import SessionLocal
from db.models import SurveyData
from pipeline.collectors.nesdc_scraper import NesdcScraper
from pipeline.ingestor import DataIngestor

def manual_ingest():
    db = SessionLocal()
    ingestor = DataIngestor(db)
    scraper = NesdcScraper()
    
    test_file = "/Users/up_main/Desktop/T_Antigravity/scratch/nesdc_test.xlsx"
    print(f"Manually ingesting from: {test_file}")
    
    # Extract data from XLS (using the same logic as in nesdc_scraper.py)
    wb = openpyxl.load_workbook(test_file, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    header1 = rows[0]
    header2 = rows[1]
    
    parsed_data = []
    party_start_idx = 10 
    parties = []
    for i in range(party_start_idx, len(header2)):
        p_name = header2[i]
        if p_name:
            parties.append((i, p_name.replace("\n", " ").strip()))
    
    for row in rows[2:]:
        if not row[0]: continue
        
        results = {}
        for idx, p_name in parties:
            val = row[idx]
            if isinstance(val, (int, float)):
                results[p_name] = float(val)
        
        # Use the scraper's normalization methods
        item = {
            "agency": str(row[1]).strip(),
            "date": scraper._extract_end_date(str(row[3])),
            "results": results,
            "sample_size": scraper._extract_number(str(row[6])) or 1000,
            "method": str(row[4]).strip(),
            "response_rate": scraper._extract_float(str(row[8])),
            "category": "election",
            "source": "nesdc.go.kr",
            "region": scraper._normalize_region(str(row[5]).strip()),
            "district": str(row[5]).strip(),
            "meta": {
                "ntt_id": str(row[0]),
                "client": str(row[2]).strip(),
                "frame": str(row[5]).strip(),
            }
        }
        parsed_data.append(item)
    
    print(f"Parsed {len(parsed_data)} items. Saving to DB...")
    saved = ingestor.parse_and_save_json(parsed_data, category="election")
    print(f"Successfully saved {saved} new items to DB.")
    
    db.close()

if __name__ == "__main__":
    manual_ingest()
