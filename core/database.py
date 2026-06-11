import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, func
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import text

from core.config import DB_PATH

Base = declarative_base()
engine = create_engine(DB_PATH, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def utc_now():
    """Return timezone-aware UTC timestamp."""
    return datetime.datetime.now(datetime.timezone.utc)

class Entity(Base):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)
    value = Column(String, unique=True, index=True)
    normalized_value = Column(String, index=True)
    source = Column(String)
    created_at = Column(DateTime, default=utc_now)

class Observation(Base):
    __tablename__ = "observations"
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, index=True, nullable=True) # Optional, can be just a raw RF observation
    observation_type = Column(String)
    protocol = Column(String, nullable=True)
    frequency = Column(String, nullable=True)
    mcc = Column(String, nullable=True)
    mnc = Column(String, nullable=True)
    lac_tac = Column(String, nullable=True)
    cell_id = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    signal_strength = Column(String, nullable=True)
    region_name = Column(String, nullable=True)
    timestamp = Column(DateTime, default=utc_now)
    confidence = Column(String)
    source = Column(String)

class Tower(Base):
    __tablename__ = "towers"
    id = Column(Integer, primary_key=True, index=True)
    mcc = Column(Integer, index=True)
    mnc = Column(Integer, index=True)
    lac_tac = Column(Integer, index=True)
    cell_id = Column(Integer, index=True)
    band = Column(String, nullable=True)
    latitude = Column(Float)
    longitude = Column(Float)
    sector = Column(Float, nullable=True)
    source = Column(String)

class Link(Base):
    __tablename__ = "links"
    id = Column(Integer, primary_key=True, index=True)
    left_entity_id = Column(Integer, index=True)
    right_entity_id = Column(Integer, index=True)
    link_type = Column(String)
    confidence = Column(Float)
    reason = Column(String)

class ImportLog(Base):
    __tablename__ = "imports"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_hash = Column(String)
    imported_at = Column(DateTime, default=utc_now)
    source_type = Column(String)
    record_count = Column(Integer)

def init_db():
    Base.metadata.create_all(bind=engine)
