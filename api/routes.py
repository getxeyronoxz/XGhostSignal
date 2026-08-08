"""API Routes for XGhostSignal - Local-first OSINT and Cellular Intelligence Workbench"""
import os
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional
import networkx as nx
import phonenumbers
from phonenumbers import geocoder, carrier

from core.database import SessionLocal, Entity, Tower, Observation, Link, ImportLog
from services.graph import build_entity_graph, get_cytoscape_data
from services.export import (
    get_all_entities as fetch_all_entities,
    get_all_observations as fetch_all_observations,
    export_csv, export_json, export_kml, export_markdown_report, export_database_dump
)
from services.reports import generate_dossier
from plugins.default.leak_search import run as run_leak_check
from plugins.default.phone_intel import run as run_phone_intel

DATA_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _safe_import_path(file_path: str) -> str:
    """Resolve import path within DATA_ROOT to prevent path traversal."""
    resolved = os.path.realpath(os.path.join(DATA_ROOT, file_path))
    if not resolved.startswith(os.path.realpath(DATA_ROOT)):
        raise ValueError("Path traversal detected")
    return resolved

router = APIRouter()


# ==================== Models ====================

class StatsResponse(BaseModel):
    entities_count: int
    towers_count: int
    observations_count: Optional[int] = None


class SearchRequest(BaseModel):
    number: str

    @field_validator('number')
    @classmethod
    def validate_number(cls, v):
        if not v:
            raise ValueError('Phone number is required')
        return v.strip()


class EntityExportRequest(BaseModel):
    entity_id: int
    format: str = "csv"


# ==================== Stats Endpoints ====================

@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """Get overall statistics from the Evidence Vault."""
    session = SessionLocal()
    try:
        e_count = session.query(Entity).count()
        t_count = session.query(Tower).count()
        o_count = session.query(Observation).count()
        return {
            "entities_count": e_count,
            "towers_count": t_count,
            "observations_count": o_count
        }
    finally:
        session.close()


@router.get("/stats/detailed")
def get_detailed_stats():
    """Get detailed statistics with entity type breakdown."""
    session = SessionLocal()
    try:
        # Entity type breakdown
        entity_types = session.query(Entity.type, Entity.source).all()
        type_counts = {}
        for entity_type, source in entity_types:
            key = f"{entity_type}:{source}" if source else entity_type
            type_counts[key] = type_counts.get(key, 0) + 1

        # Tower locations
        towers_with_coords = session.query(Observation).filter(
            Observation.latitude != None
        ).count()

        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_observations = session.query(Observation).filter(
            Observation.timestamp >= yesterday
        ).count()

        return {
            "entity_types": type_counts,
            "towers_with_coordinates": towers_with_coords,
            "recent_observations_24h": recent_observations,
            "total_links": session.query(Link).count()
        }
    finally:
        session.close()


# ==================== Entity Endpoints ====================

@router.get("/entities")
def get_all_entities(limit: int = 100, offset: int = 0, type_filter: Optional[str] = None):
    """List all entities with pagination."""
    session = SessionLocal()
    try:
        query = session.query(Entity)
        if type_filter:
            query = query.filter(Entity.type == type_filter)

        total = query.count()
        entities = query.order_by(Entity.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "data": [
                {
                    "id": e.id,
                    "type": e.type,
                    "value": e.value,
                    "normalized_value": e.normalized_value,
                    "source": e.source,
                    "created_at": str(e.created_at)
                }
                for e in entities
            ]
        }
    finally:
        session.close()


@router.get("/entities/{entity_id}")
def get_entity(entity_id: int):
    """Get details of a specific entity."""
    session = SessionLocal()
    try:
        entity = session.query(Entity).filter_by(id=entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        observations = session.query(Observation).filter_by(entity_id=entity_id).all()

        return {
            "id": entity.id,
            "type": entity.type,
            "value": entity.value,
            "normalized_value": entity.normalized_value,
            "source": entity.source,
            "created_at": str(entity.created_at),
            "observations": [
                {
                    "id": o.id,
                    "type": o.observation_type,
                    "protocol": o.protocol,
                    "frequency": o.frequency,
                    "mcc": o.mcc,
                    "mnc": o.mnc,
                    "cell_id": o.cell_id,
                    "latitude": o.latitude,
                    "longitude": o.longitude,
                    "confidence": o.confidence,
                    "timestamp": str(o.timestamp)
                }
                for o in observations
            ]
        }
    finally:
        session.close()


@router.get("/entities/{entity_id}/leaks")
def check_entity_leaks(entity_id: int):
    """Check if an entity (phone number) appears in breach databases."""
    session = SessionLocal()
    try:
        entity = session.query(Entity).filter_by(id=entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        result = run_leak_check(entity.value)
        return result
    finally:
        session.close()


# ==================== Tower/Cell Data Endpoints ====================

@router.get("/towers")
def get_towers(limit: int = 100, offset: int = 0):
    """List all cell tower observations."""
    session = SessionLocal()
    try:
        obs = session.query(Observation).filter(
            Observation.latitude != None
        ).offset(offset).limit(limit).all()

        return {
            "total": len(obs),
            "offset": offset,
            "limit": limit,
            "data": [
                {
                    "id": o.id,
                    "mcc": o.mcc,
                    "mnc": o.mnc,
                    "cell_id": o.cell_id,
                    "lac_tac": o.lac_tac,
                    "lat": o.latitude,
                    "lon": o.longitude,
                    "radio": o.protocol,
                    "signal": o.signal_strength,
                    "confidence": o.confidence,
                    "timestamp": str(o.timestamp)
                }
                for o in obs
            ]
        }
    finally:
        session.close()


@router.get("/towers/bbox")
def get_towers_bbox(
    min_lat: float, max_lat: float,
    min_lon: float, max_lon: float,
    limit: int = 500
):
    """Query towers within a physical bounding box."""
    session = SessionLocal()
    try:
        obs = session.query(Observation).filter(
            Observation.latitude >= min_lat,
            Observation.latitude <= max_lat,
            Observation.longitude >= min_lon,
            Observation.longitude <= max_lon
        ).limit(limit).all()

        return {
            "bbox": {
                "min_lat": min_lat, "max_lat": max_lat,
                "min_lon": min_lon, "max_lon": max_lon
            },
            "count": len(obs),
            "data": [
                {
                    "id": o.id,
                    "mcc": o.mcc,
                    "mnc": o.mnc,
                    "cell_id": o.cell_id,
                    "lat": o.latitude,
                    "lon": o.longitude,
                    "radio": o.protocol,
                    "signal": o.signal_strength
                }
                for o in obs
            ]
        }
    finally:
        session.close()


@router.get("/towers/mcc/{mcc}")
def get_towers_by_mcc(mcc: str, limit: int = 100):
    """Get towers for a specific Mobile Country Code."""
    session = SessionLocal()
    try:
        obs = session.query(Observation).filter(
            Observation.mcc == mcc
        ).limit(limit).all()

        return {
            "mcc": mcc,
            "count": len(obs),
            "data": [
                {
                    "id": o.id,
                    "mnc": o.mnc,
                    "cell_id": o.cell_id,
                    "lac_tac": o.lac_tac,
                    "lat": o.latitude,
                    "lon": o.longitude,
                    "radio": o.protocol
                }
                for o in obs
            ]
        }
    finally:
        session.close()


# ==================== Graph Endpoints ====================

@router.get("/graph")
def get_graph():
    """Get entity correlation graph data."""
    G = build_entity_graph()
    return get_cytoscape_data(G)


@router.get("/graph/neighbors/{entity_id}")
def get_graph_neighbors(entity_id: int, depth: int = 1):
    """Get neighbors of a specific entity in the graph."""
    G = build_entity_graph()

    if entity_id not in G:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not in graph")

    # Get neighbors at specified depth
    neighbors = nx.ego_graph(G, entity_id, radius=depth, undirected=True)

    return get_cytoscape_data(neighbors)


# ==================== Search & Intelligence ====================

@router.post("/search")
def search_entity(req: SearchRequest):
    """Search and enrich a phone number."""
    try:
        parsed = phonenumbers.parse(req.number)
        if not phonenumbers.is_valid_number(parsed):
            raise HTTPException(status_code=400, detail="Invalid phone number format.")

        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        geo_loc = geocoder.description_for_number(parsed, "en")
        carrier_name = carrier.name_for_number(parsed, "en")

        session = SessionLocal()
        try:
            entity = session.query(Entity).filter_by(value=req.number).first()
            if not entity:
                entity = Entity(
                    type="PHONE_NUMBER",
                    value=req.number,
                    normalized_value=formatted,
                    source="web_ui"
                )
                session.add(entity)
                session.commit()

            return {
                "number": formatted,
                "location": geo_loc or "Unknown Region",
                "carrier": carrier_name or "Unknown Carrier",
                "country_code": parsed.country_code
            }
        finally:
            session.close()
    except phonenumbers.phonenumberutil.NumberParseException:
        raise HTTPException(status_code=400, detail="Failed to parse number.")


@router.post("/search/enrich")
def enrich_search(req: SearchRequest):
    """Search with full enrichment including leak check and phone intelligence."""
    try:
        parsed = phonenumbers.parse(req.number)
        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

        # Get phone intelligence
        phone_intel = run_phone_intel(formatted)

        # Check for breaches
        leak_check = run_leak_check(formatted)

        # Get existing entity data
        session = SessionLocal()
        try:
            entity = session.query(Entity).filter_by(value=req.number).first()
            if entity:
                observations = session.query(Observation).filter_by(entity_id=entity.id).all()
                obs_data = [
                    {
                        "id": o.id,
                        "type": o.observation_type,
                        "timestamp": str(o.timestamp)
                    }
                    for o in observations
                ]
            else:
                obs_data = []

            return {
                "number": formatted,
                "phone_intel": phone_intel,
                "leak_check": leak_check,
                "observations": obs_data
            }
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Export Endpoints ====================

class ExportRequest(BaseModel):
    format: str = "csv"
    entity_id: Optional[int] = None
    all_entities: bool = False


@router.post("/export")
def export_data(req: ExportRequest):
    """Export data to various formats (CSV, JSON, KML, Markdown)."""
    try:
        if req.all_entities:
            entities = fetch_all_entities()
        elif req.entity_id:
            session = SessionLocal()
            try:
                entity = session.query(Entity).filter_by(id=req.entity_id).first()
                if not entity:
                    raise HTTPException(status_code=404, detail=f"Entity {req.entity_id} not found")
                entities = [{
                    "id": entity.id,
                    "type": entity.type,
                    "value": entity.value,
                    "source": entity.source
                }]
            finally:
                session.close()
        else:
            entities = fetch_all_entities()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if req.format == "csv":
            filepath = export_csv(entities, filename=f"{timestamp}_entities.csv")
        elif req.format == "json":
            filepath = export_json(entities, filename=f"{timestamp}_entities.json")
        elif req.format == "kml":
            filepath = export_kml(entities, filename=f"{timestamp}_entities.kml")
        elif req.format == "md":
            filepath = export_markdown_report(entities, filename=f"{timestamp}_report.md")
        elif req.format == "db":
            filepath = export_database_dump(f"xghostsignal_{timestamp}.sql")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown format: {req.format}")

        return {
            "success": True,
            "format": req.format,
            "filepath": filepath
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Export failed")


@router.get("/export/{entity_id}")
def export_entity(entity_id: int, format: str = "csv"):
    """Export a specific entity to a file."""
    session = SessionLocal()
    try:
        entity = session.query(Entity).filter_by(id=entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        observations = session.query(Observation).filter_by(entity_id=entity_id).all()

        if format == "csv":
            filepath = export_csv([{
                "id": entity.id,
                "type": entity.type,
                "value": entity.value,
                "source": entity.source
            }], filename=f"entity_{entity.value.replace('+', '')}.csv")
        elif format == "json":
            filepath = export_json([{
                "id": entity.id,
                "type": entity.type,
                "value": entity.value,
                "source": entity.source
            }], filename=f"entity_{entity.value.replace('+', '')}.json")
        elif format == "kml":
            filepath = export_kml([{
                "id": entity.id,
                "type": entity.type,
                "value": entity.value,
                "source": entity.source
            }], filename=f"entity_{entity.value.replace('+', '')}.kml")
        elif format == "md":
            filepath = export_markdown_report([{
                "id": entity.id,
                "type": entity.type,
                "value": entity.value,
                "source": entity.source
            }], filename=f"entity_{entity.value.replace('+', '')}.md")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown format: {format}")

        return {
            "success": True,
            "format": format,
            "filepath": filepath
        }
    finally:
        session.close()


# ==================== Import Endpoints ====================

class ImportRequest(BaseModel):
    file_path: str
    parser_type: str = "opencellid"


def _get_or_create_entity(session, entity_value, entity_type, source):
    """Get existing entity or create new one, handling race conditions."""
    entity = session.query(Entity).filter_by(value=entity_value).first()
    if not entity:
        entity = Entity(
            type=entity_type,
            value=entity_value,
            normalized_value=entity_value,
            source=source
        )
        session.add(entity)
        session.flush()
    return entity


@router.post("/import")
def import_data(req: ImportRequest):
    """Import data from a file using the specified parser."""
    parser_type = req.parser_type.lower()

    try:
        safe_path = _safe_import_path(req.file_path)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")

    if parser_type == "opencellid":
        from parsers.opencellid import OpenCellIDParser
        parser = OpenCellIDParser()
    elif parser_type == "cellmapper":
        from parsers.cellmapper import CellMapperParser
        parser = CellMapperParser()
    elif parser_type == "rtl_power":
        from parsers.rtl_power import RtlPowerParser
        parser = RtlPowerParser()
    elif parser_type == "pcap":
        from parsers.pcap import PCAPParser
        parser = PCAPParser()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown parser type: {parser_type}")

    records = parser.parse_file(safe_path)

    session = SessionLocal()
    try:
        for r in records:
            entity_value = None
            entity_type = "UNKNOWN"

            if r.get("cell_id"):
                entity_value = f"{r.get('mcc')}-{r.get('mnc')}-{r.get('lac_tac')}-{r.get('cell_id')}"
                entity_type = "CELL_TOWER"
            elif r.get("protocol"):
                entity_value = f"EMITTER_{r.get('protocol')}_{r.get('frequency')}"
                entity_type = "RF_EMITTER"

            entity_id = None
            if entity_value:
                entity = _get_or_create_entity(
                    session, entity_value, entity_type, r.get("source", "import")
                )
                entity_id = entity.id

            obs = Observation(
                entity_id=entity_id,
                observation_type=r.get("protocol", "RF"),
                protocol=r.get("protocol"),
                frequency=r.get("frequency"),
                mcc=r.get("mcc"),
                mnc=r.get("mnc"),
                lac_tac=r.get("lac_tac"),
                cell_id=r.get("cell_id"),
                latitude=float(r["latitude"]) if r.get("latitude") not in (None, "") else None,
                longitude=float(r["longitude"]) if r.get("longitude") not in (None, "") else None,
                signal_strength=r.get("signal_strength"),
                confidence=r.get("confidence"),
                source=r.get("source")
            )
            session.add(obs)

        session.commit()

        import_log = ImportLog(
            filename=req.file_path,
            file_hash="",
            source_type=parser_type,
            record_count=len(records)
        )
        session.add(import_log)
        session.commit()

        return {
            "success": True,
            "parser": parser_type,
            "records_imported": len(records)
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ==================== Reports ====================

@router.get("/report/{identifier}")
def get_report(identifier: str):
    """Generate a Markdown intelligence dossier for an entity."""
    result = generate_dossier(identifier)

    if result.startswith("Error"):
        raise HTTPException(status_code=404, detail=result)

    # Read the file content
    with open(result, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "success": True,
        "filepath": result,
        "content": content
    }


# ==================== Health ====================

@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.2.0",
        "features": [
            "entity_search",
            "tower_mapping",
            "graph_correlation",
            "export_csv",
            "export_json",
            "export_kml",
            "leak_check",
            "phone_intel"
        ]
    }
