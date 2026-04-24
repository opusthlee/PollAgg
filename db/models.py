from sqlalchemy import Boolean, Column, Integer, String, Float, JSON, Date, DateTime
import datetime
from .database import Base

class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, index=True)
    agency = Column(String, index=True)
    date = Column(String, index=True)
    results = Column(JSON)
    sample_size = Column(Integer)
    method = Column(String, nullable=True)
    response_rate = Column(Float, nullable=True)
    
    # Flags for manual overrides
    is_manual_override = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True) # If false, the engine ignores it
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AgencyBias(Base):
    __tablename__ = "agency_bias"
    
    id = Column(Integer, primary_key=True, index=True)
    agency = Column(String, unique=True, index=True)
    bias_scores = Column(JSON) # e.g. {"party_democratic": 2.5, "party_republican": -2.5}
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class EngineConfig(Base):
    __tablename__ = "engine_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String, unique=True, index=True)
    config_value = Column(JSON)
    description = Column(String, nullable=True)
