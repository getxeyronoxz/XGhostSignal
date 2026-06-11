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
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from io import StringIO

from core.database import SessionLocal, Entity, Observation, Tower, Link


def export_csv(entities: List[Dict[str, Any]], filename: str = None) -> str:
    """Export entities to CSV format.

    Args:
        entities: List of entity dictionaries to export
        filename: Output filename (optional)

    Returns:
        Path to exported file
    """
    if not entities:
        return ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = filename or f"export_{timestamp}.csv"
    filepath = os.path.join("exports", safe_filename)

    os.makedirs("exports", exist_ok=True)

    # Get all keys from entities for CSV headers
    all_keys = set()
    for entity in entities:
        all_keys.update(entity.keys())

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
        writer.writeheader()
        writer.writerows(entities)

    return filepath


def export_json(entities: List[Dict[str, Any]], filename: str = None) -> str:
    """Export entities to JSON format.

    Args:
        entities: List of entity dictionaries to export
        filename: Output filename (optional)

    Returns:
        Path to exported file
    """
    if not entities:
        return ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = filename or f"export_{timestamp}.json"
    filepath = os.path.join("exports", safe_filename)

    os.makedirs("exports", exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(entities, f, indent=2, default=str)

    return filepath


def export_kml(entities: List[Dict[str, Any]], filename: str = None) -> str:
    """Export entities to KML format for Google Earth.

    Args:
        entities: List of entity dictionaries (should have lat/lon)
        filename: Output filename (optional)

    Returns:
        Path to exported file
    """
    if not entities:
        return ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = filename or f"export_{timestamp}.kml"
    filepath = os.path.join("exports", safe_filename)

    os.makedirs("exports", exist_ok=True)

    # Build KML document
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
            name = entity.get('value') or entity.get('id', 'Unknown')
            entity_type = entity.get('type', 'Unknown')
            desc = entity.get('description', entity.get('source', ''))

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

    return filepath


def export_markdown_report(entities: List[Dict[str, Any]], filename: str = None) -> str:
    """Export entities to Markdown report format.

    Args:
        entities: List of entity dictionaries to export
        filename: Output filename (optional)

    Returns:
        Path to exported file
    """
    if not entities:
        return ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = filename or f"report_{timestamp}.md"
    filepath = os.path.join("exports", safe_filename)

    os.makedirs("exports", exist_ok=True)

    lines = [
        "# XGhostSignal Intelligence Report",
        f"**Generated:** {datetime.now().isoformat()}Z",
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

    return filepath


def export_database_dump(output_path: str = None) -> str:
    """Export the entire XGhostSignal database to a dump file.

    Args:
        output_path: Output path for SQL dump (optional)

    Returns:
        Path to exported file
    """
    from core.config import DB_PATH

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = output_path or f"xghostsignal_dump_{timestamp}.sql"
    filepath = os.path.join("exports", safe_filename)

    os.makedirs("exports", exist_ok=True)

    # Connect to the SQLite database
    db_path = DB_PATH.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    conn.text_factory = str

    with open(filepath, 'w', encoding='utf-8') as f:
        # Write header
        f.write("-- XGhostSignal Database Dump\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}Z\n")
        f.write("-- https://github.com/xeyronox/xghostsignal\n\n")

        # Dump schema
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
        for row in cursor.fetchall():
            f.write(f"{row[0]};\n\n")

        # Dump data from each table
        tables = ['entities', 'observations', 'towers', 'links', 'imports']
        for table in tables:
            f.write(f"-- Data from {table}\n")
            cursor.execute(f"SELECT * FROM {table};")
            rows = cursor.fetchall()
            if rows:
                # Get column names
                column_names = [description[0] for description in cursor.description]
                for row in rows:
                    values = []
                    for val in row:
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, str):
                            # Escape single quotes
                            val = val.replace("'", "''")
                            values.append(f"'{val}'")
                        else:
                            values.append(str(val))
                    f.write(f"INSERT INTO {table} ({', '.join(column_names)}) VALUES ({', '.join(values)});\n")
            f.write("\n")

        conn.close()

    return filepath


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
