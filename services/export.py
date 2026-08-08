"""Export Services for XGhostSignal

Provides export functionality for intelligence data in various formats:
- CSV: Tabular data export
- JSON: Structured data export
- KML: Geospatial/KML export for Google Earth
- Markdown: Dossier generation
- SQLite: Database export
"""
import csv
import json
import os
import re
import sqlite3
import contextlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from xml.sax.saxutils import escape as xml_escape

from core.database import SessionLocal, Entity, Observation


def _safe_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    safe = Path(filename).name
    safe = re.sub(r'[^A-Za-z0-9_.-]', '_', safe)
    if not safe:
        safe = "export"
    return safe


def _exports_dir() -> Path:
    p = Path("exports")
    p.mkdir(exist_ok=True)
    return p


def export_csv(entities: List[Dict[str, Any]], filename: str = None) -> str:
    """Export entities to CSV format."""
    if not entities:
        return ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = _safe_filename(filename or f"export_{timestamp}.csv")
    filepath = _exports_dir() / safe_filename

    all_keys = set()
    for entity in entities:
        all_keys.update(entity.keys())

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
        writer.writeheader()
        writer.writerows(entities)

    return str(filepath)


def export_json(entities: List[Dict[str, Any]], filename: str = None) -> str:
    """Export entities to JSON format."""
    if not entities:
        return ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = _safe_filename(filename or f"export_{timestamp}.json")
    filepath = _exports_dir() / safe_filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(entities, f, indent=2, default=str)

    return str(filepath)


def export_kml(entities: List[Dict[str, Any]], filename: str = None) -> str:
    """Export entities to KML format for Google Earth."""
    if not entities:
        return ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = _safe_filename(filename or f"export_{timestamp}.kml")
    filepath = _exports_dir() / safe_filename

    kml_header = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>XGhostSignal Export</name>
    <description>Exported from XGhostSignal Intelligence Workbench</description>
'''

    kml_footer = '''  </Document>
</kml>
'''

    placemarks = []
    for entity in entities:
        lat = entity.get('latitude') or entity.get('lat')
        lon = entity.get('longitude') or entity.get('lon')

        if lat is not None and lon is not None:
            name = xml_escape(str(entity.get('value') or entity.get('id', 'Unknown')))
            desc = xml_escape(str(entity.get('description', entity.get('source', ''))))

            placemark = f'''    <Placemark>
      <name>{name}</name>
      <description>{desc}</description>
      <Point>
        <coordinates>{lon},{lat},0</coordinates>
      </Point>
    </Placemark>
'''
            placemarks.append(placemark)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(kml_header)
        f.write('\n'.join(placemarks))
        f.write(kml_footer)

    return str(filepath)


def export_markdown_report(entities: List[Dict[str, Any]], filename: str = None) -> str:
    """Export entities to Markdown report format."""
    if not entities:
        return ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = _safe_filename(filename or f"report_{timestamp}.md")
    filepath = _exports_dir() / safe_filename

    lines = [
        "# XGhostSignal Intelligence Report",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        "## Summary",
        f"**Total Entities:** {len(entities)}",
        "",
    ]

    for i, entity in enumerate(entities, 1):
        lines.extend([
            f"## Entity #{i}",
            "",
            f"- **Identifier:** `{entity.get('value', 'N/A')}`",
            f"- **Type:** `{entity.get('type', 'Unknown')}`",
            f"- **Source:** `{entity.get('source', 'Unknown')}`",
            f"- **Coordinates:** {entity.get('latitude', 'N/A')}, {entity.get('longitude', 'N/A')}",
            "",
        ])

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return str(filepath)


def export_database_dump(output_path: str = None) -> str:
    """Export the entire XGhostSignal database to a dump file."""
    from core.config import DB_PATH

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = _safe_filename(output_path or f"xghostsignal_dump_{timestamp}.sql")
    filepath = _exports_dir() / safe_filename

    db_path = DB_PATH.replace("sqlite:///", "")

    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("-- XGhostSignal Database Dump\n")
            f.write(f"-- Generated: {datetime.now().isoformat()}\n")
            f.write("-- https://github.com/xeyronox/xghostsignal\n\n")
            for line in conn.iterdump():
                f.write(f"{line};\n")

    return str(filepath)


def get_all_entities() -> List[Dict[str, Any]]:
    """Fetch all entities from the database.

    Returns:
        List of entity dictionaries
    """
    session = SessionLocal()
    try:
        entities = session.query(Entity).all()
        return [
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
    finally:
        session.close()


def get_all_observations() -> List[Dict[str, Any]]:
    """Fetch all observations from the database.

    Returns:
        List of observation dictionaries
    """
    session = SessionLocal()
    try:
        observations = session.query(Observation).all()
        return [
            {
                "id": o.id,
                "entity_id": o.entity_id,
                "observation_type": o.observation_type,
                "protocol": o.protocol,
                "frequency": o.frequency,
                "mcc": o.mcc,
                "mnc": o.mnc,
                "lac_tac": o.lac_tac,
                "cell_id": o.cell_id,
                "latitude": o.latitude,
                "longitude": o.longitude,
                "signal_strength": o.signal_strength,
                "confidence": o.confidence,
                "source": o.source,
                "timestamp": str(o.timestamp)
            }
            for o in observations
        ]
    finally:
        session.close()


# Export module
__all__ = [
    'export_csv',
    'export_json',
    'export_kml',
    'export_markdown_report',
    'export_database_dump',
    'get_all_entities',
    'get_all_observations',
]
