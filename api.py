from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Import the engine and DB
from main import StatsOptimizer
from db.database import engine, get_db, Base
from db.models import SurveyData, AgencyBias
from pipeline.ingestor import DataIngestor
from engine.validator import ModelValidator

# Create static directory if not exists
if not os.path.exists("static"):
    os.makedirs("static")

app = FastAPI(title="PollAgg General-Purpose API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BatchAnalysisRequest(BaseModel):
    data: List[Dict]
    category: str
    config: Dict
    regions: List[str]

class AnalyzeRequest(BaseModel):
    data: List[Dict]
    category: Optional[str] = "general"
    prior_data: Optional[Dict] = None
    fundamentals: Optional[Dict] = None
    config: Dict

class DataCreate(BaseModel):
    category: str = "election"
    agency: str
    date: str
    results: Dict[str, Any]
    sample_size: int = 1000
    method: Optional[str] = None
    response_rate: Optional[float] = None
    region: Optional[str] = None
    district: Optional[str] = None
    is_manual_override: bool = False

@app.post("/api/analyze")
def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)):
    logger.info(f"Analysis requested for category: {req.category}")
    config = req.config
    config["category"] = req.category
    
    region = config.get("region")
    district = config.get("district")
    
    # 1. Fetch Hierarchical Bias Data
    biases = db.query(AgencyBias).all()
    bias_map = {}
    
    # Priority: District -> Region -> National
    for b in [b for b in biases if b.region is None]:
        bias_map[b.agency] = b.bias_scores
    if region:
        for b in [b for b in biases if b.region == region and b.district is None]:
            bias_map[b.agency] = b.bias_scores
    if district:
        for b in [b for b in biases if b.district == district]:
            bias_map[b.agency] = b.bias_scores
    
    optimizer = StatsOptimizer(config=config)
    result = optimizer.analyze_dataset(
        data=req.data, 
        prior_data=req.prior_data, 
        fundamentals=req.fundamentals,
        bias_data=bias_map
    )
    return result

@app.get("/api/data")
def get_data(category: Optional[str] = None, region: Optional[str] = None, district: Optional[str] = None, db: Session = Depends(get_db)):
    logger.info(f"Data requested for category: {category}, region: {region}, district: {district}")
    query = db.query(SurveyData).filter(SurveyData.is_active == True)
    if category:
        query = query.filter(SurveyData.category == category)
    if region:
        query = query.filter(SurveyData.region == region)
    if district:
        query = query.filter(SurveyData.district.like(f"%{district}%"))
        
    results = query.all()
    logger.info(f"Returning {len(results)} items")
    return results

@app.post("/api/data")
def create_data(item: DataCreate, db: Session = Depends(get_db)):
    db_item = SurveyData(
        category=item.category,
        agency=item.agency,
        date=item.date,
        results=item.results,
        sample_size=item.sample_size,
        method=item.method,
        response_rate=item.response_rate,
        region=item.region,
        district=item.district,
        is_manual_override=item.is_manual_override
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.post("/api/optimize")
def save_bias_data(region: Optional[str] = None, district: Optional[str] = None, db: Session = Depends(get_db)):
    """
    실제 결과와 비교하여 계산된 각 기관의 오차(Bias)를 DB에 저장합니다.
    계층적(전국/광역/기초)으로 각각의 보정치를 생성합니다.
    """
    validator = ModelValidator(db)
    # 가장 최근 주요 선거 결과를 기준으로 오차 계산
    report = validator.get_comparison_report(election_date="2024-04-10", region=region, district=district)
    if not report:
        return {"status": "error", "message": f"No validation data available for {region or 'National'} {district or ''}."}
    
    saved_count = 0
    for agency_data in report["agency_analysis"]:
        agency_name = agency_data["agency"]
        bias_scores = agency_data["bias_by_target"]
        
        # 기존 데이터 업데이트 또는 생성 (동일 scope 기준)
        existing = db.query(AgencyBias).filter(
            AgencyBias.agency == agency_name,
            AgencyBias.region == region,
            AgencyBias.district == district
        ).first()
        
        if existing:
            existing.bias_scores = bias_scores
        else:
            new_bias = AgencyBias(agency=agency_name, region=region, district=district, bias_scores=bias_scores)
            db.add(new_bias)
        saved_count += 1
    
    db.commit()
    return {"status": "success", "message": f"Optimization complete for {region or 'National'}. Saved bias for {saved_count} agencies."}

@app.get("/api/v1/summary/{category}")
def run_analysis(category: str, region: Optional[str] = None, district: Optional[str] = None, db: Session = Depends(get_db)):
    """
    전체 데이터를 분석하여 통합 트렌드와 예측치를 반환합니다.
    지역별 보정치(Bias)를 우선적으로 적용합니다.
    """
    query = db.query(SurveyData).filter(SurveyData.is_active == True)
    if category:
        query = query.filter(SurveyData.category == category)
    if region:
        query = query.filter(SurveyData.region == region)
    if district:
        query = query.filter(SurveyData.district.like(f"%{district}%"))
        
    data = query.all()
    if not data:
        return {"status": "empty", "category": category}
        
    # 1. 기관별 편향(Bias) 데이터 로드 (최적화 데이터)
    # 지역/지역구에 해당하는 보정치가 있으면 우선 사용, 없으면 전국 평균 사용
    biases = db.query(AgencyBias).all()
    
    # Hierarchical Bias Map Construction
    # Priority: District -> Region -> National
    bias_map = {}
    
    # 1. Start with National (None, None)
    for b in [b for b in biases if b.region is None]:
        bias_map[b.agency] = b.bias_scores
        
    # 2. Layer with Region (if matches)
    if region:
        for b in [b for b in biases if b.region == region and b.district is None]:
            bias_map[b.agency] = b.bias_scores
            
    # 3. Layer with District (if matches)
    if district:
        for b in [b for b in biases if b.district == district]:
            bias_map[b.agency] = b.bias_scores
        
    # Convert list of models to list of dicts for the engine
    raw_data = []
    for d in data:
        raw_data.append({
            "agency": d.agency,
            "date": d.date,
            "results": d.results,
            "sample_size": d.sample_size,
            "method": d.method,
            "response_rate": d.response_rate,
            "region": d.region,
            "district": d.district
        })
        
    # StatsOptimizer에 bias_map 전달
    optimizer = StatsOptimizer(config={"category": category, "use_smoothing": True})
    return optimizer.analyze_dataset(raw_data, bias_data=bias_map)

# --- Static File Serving ---
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

@app.get("/api/validate")
async def get_validation_report(date: str = "2024-04-10", region: Optional[str] = None, district: Optional[str] = None, db: Session = Depends(get_db)):
    """실제 결과와 대조한 검증 리포트 반환 (지역 필터 포함)"""
    validator = ModelValidator(db)
    report = validator.get_comparison_report(election_date=date, region=region, district=district)
    if not report:
        return {"status": "error", "message": "Validation data not found for selected scope"}
    return report


@app.post("/api/batch-analyze")
async def run_batch_analysis(req: BatchAnalysisRequest, db: Session = Depends(get_db)):
    results = {}
    optimizer = StatsOptimizer(config=req.config)
    base_data = [d for d in req.data if d.get("category") == req.category]
    for region in req.regions:
        region_data = [d for d in base_data if d.get("region") == region or (region == "National" and d.get("region") in [None, "National"])]
        if not region_data: continue
        analysis = optimizer.analyze_dataset(data=region_data)
        results[region] = analysis
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8002, reload=False)
