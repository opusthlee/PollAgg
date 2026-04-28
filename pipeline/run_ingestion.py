import logging
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.ingestor import DataIngestor
from db.database import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("IngestionRunner")

def main():
    logger.info("Starting PollAgg Data Ingestion...")
    db = SessionLocal()
    try:
        ingestor = DataIngestor(db)
        summary = ingestor.run_collectors(config_path="config.json")
        logger.info(f"Ingestion complete. Summary: {summary}")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    main()
