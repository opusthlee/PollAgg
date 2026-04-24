from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
import os

# Import the engine and DB
from main import StatsOptimizer
from db.database import engine, get_db, Base
from db.models import Poll
from pipeline.ingestor import DataIngestor

app = FastAPI(title="Stats-Optimizer Dev API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files for the frontend dashboard
app.mount("/static", StaticFiles(directory="static"), name="static")

class AnalyzeRequest(BaseModel):
    data: List[Dict]
    prior_data: Optional[Dict] = None
    fundamentals: Optional[Dict] = None
    config: Dict

class PollCreate(BaseModel):
    agency: str
    date: str
    results: Dict[str, Any]
    sample_size: int = 1000
    method: Optional[str] = None
    response_rate: Optional[float] = None
    is_manual_override: bool = False

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    # Initialize the optimizer with the requested config toggles
    optimizer = StatsOptimizer(config=req.config)
    
    # Run the full pipeline
    result = optimizer.analyze_election(
        data=req.data, 
        prior_data=req.prior_data, 
        fundamentals=req.fundamentals
    )
    
    return result

# --- DB CRUD Endpoints ---

@app.get("/api/polls")
def get_polls(db: Session = Depends(get_db)):
    polls = db.query(Poll).filter(Poll.is_active == True).all()
    return polls

@app.post("/api/polls")
def create_poll(poll: PollCreate, db: Session = Depends(get_db)):
    db_poll = Poll(
        agency=poll.agency,
        date=poll.date,
        results=poll.results,
        sample_size=poll.sample_size,
        method=poll.method,
        response_rate=poll.response_rate,
        is_manual_override=poll.is_manual_override
    )
    db.add(db_poll)
    db.commit()
    db.refresh(db_poll)
    return db_poll

@app.post("/api/ingest")
def ingest_data(data: List[Dict], db: Session = Depends(get_db)):
    ingestor = DataIngestor(db)
    count = ingestor.parse_and_save_json(data)
    return {"status": "success", "inserted": count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8002, reload=True)
