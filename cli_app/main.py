"""XGhostSignal CLI - Local-first OSINT and Cellular Intelligence Workbench"""
import typer
import phonenumbers
from rich.console import Console
from rich.table import Table

from core.database import init_db, SessionLocal, Entity
from core.config import ALLOWED_COUNTRY_CODES
from services.reports import generate_dossier
from services.llm import summarize_dossier_with_llm
from services.export import (
    get_all_entities, get_all_observations,
    export_csv, export_json, export_kml, export_markdown_report, export_database_dump
)
from core.database import Observation

app = typer.Typer(help="XGhostSignal - Local-first OSINT and Cellular Intelligence Workbench")
console = Console()


@app.command()
def init():
    """Initialize the local database."""
    init_db()
    console.print("[green]Database initialized successfully.[/green]")


@app.command()
def search(number: str):
    """Search and enrich a phone number."""
    try:
        parsed = phonenumbers.parse(number, None)
        region = phonenumbers.region_code_for_number(parsed)

        if region not in ALLOWED_COUNTRY_CODES:
            console.print(f"[red]Error: Country {region} is out of scope.[/red]")
            raise typer.Exit(1)

        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        is_valid = phonenumbers.is_valid_number(parsed)

        table = Table(title=f"Phone Intelligence: {formatted}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Valid", str(is_valid))
        table.add_row("Region", region)
        table.add_row("Country Code", str(parsed.country_code))
        table.add_row("National Number", str(parsed.national_number))

        console.print(table)

        # Save to Evidence Vault
        session = SessionLocal()
        try:
            entity = session.query(Entity).filter_by(value=number).first()
            if not entity:
                entity = Entity(
                    type="PHONE_NUMBER",
                    value=number,
                    normalized_value=formatted,
                    source="cli_search"
                )
                session.add(entity)
                session.commit()
                console.print(f"[green][+] Tracked '{formatted}' in the Evidence Vault.[/green]")
        finally:
            session.close()

    except Exception as e:
        console.print(f"[red]Failed to parse number: {e}[/red]")


@app.command()
def report(identifier: str):
    """Generate a Markdown intelligence dossier for an entity."""
    console.print(f"[*] Querying Evidence Vault for {identifier}...")
    result = generate_dossier(identifier)
    if result.startswith("Error"):
        console.print(f"[red]{result}[/red]")
    else:
        console.print(f"[green][+] Dossier successfully generated at: {result}[/green]")


@app.command()
def summarize(identifier: str):
    """Generate a dossier and run it through a local LLM for a tactical summary."""
    console.print(f"[*] Extracting dossier for {identifier}...")
    result = generate_dossier(identifier)

    if result.startswith("Error"):
        console.print(f"[red]{result}[/red]")
        raise typer.Exit(1)

    console.print("[*] Passing dossier to Local LLM Enclave (Ollama)...")
    with open(result, "r", encoding="utf-8") as f:
        dossier_text = f.read()

    summary = summarize_dossier_with_llm(dossier_text)

    console.print("\n[bold cyan]=== AI TACTICAL SUMMARY ===[/bold cyan]")
    console.print(summary)
    console.print("[bold cyan]===========================[/bold cyan]\n")


@app.command()
def ingest(file_path: str, parser_type: str = typer.Option("opencellid", help="Type of parser: opencellid, cellmapper, rtl_power, pcap")):
    """Ingest RF/Telecom data using the Unified Parser Engine."""
    console.print(f"[*] Ingesting [bold]{file_path}[/bold] using {parser_type} parser...")

    parser = None
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
    elif parser_type == "sdr_stream":
        from parsers.sdr_stream import SDRStreamParser
        parser = SDRStreamParser()
    elif parser_type == "adsb":
        from parsers.adsb import ADSBParser
        parser = ADSBParser()
    else:
        console.print(f"[red]Unknown parser type: {parser_type}[/red]")
        raise typer.Exit(1)

    try:
        records = parser.parse_file(file_path) if hasattr(parser, 'parse_file') else []
        console.print(f"[green][+] Normalized {len(records)} unified records from {file_path}.[/green]")

        session = SessionLocal()
        try:
            for r in records:
                # 1. Determine Identity
                entity_value = None
                entity_type = "UNKNOWN"

                if r.get("cell_id"):
                    entity_value = f"{r.get('mcc')}-{r.get('mnc')}-{r.get('lac_tac')}-{r.get('cell_id')}"
                    entity_type = "CELL_TOWER"
                elif r.get("protocol") == "ADS-B":
                    entity_value = r.get("frequency")
                    entity_type = "AIRCRAFT"
                elif r.get("protocol"):
                    entity_value = f"EMITTER_{r.get('protocol')}_{r.get('frequency')}"
                    entity_type = "RF_EMITTER"

                # 2. Upsert Entity
                entity_id = None
                if entity_value:
                    entity = session.query(Entity).filter_by(value=entity_value).first()
                    if not entity:
                        entity = Entity(
                            type=entity_type,
                            value=entity_value,
                            normalized_value=entity_value,
                            source=r.get("source", "parser")
                        )
                        session.add(entity)
                        session.commit()
                        session.refresh(entity)
                    entity_id = entity.id

                # 3. Create Observation linked to Entity
                from core.database import Observation
                obs = Observation(
                    entity_id=entity_id,
                    observation_type=r.get("protocol", "RF"),
                    protocol=r.get("protocol"),
                    frequency=r.get("frequency"),
                    mcc=r.get("mcc"),
                    mnc=r.get("mnc"),
                    lac_tac=r.get("lac_tac"),
                    cell_id=r.get("cell_id"),
                    latitude=float(r["latitude"]) if r.get("latitude") else None,
                    longitude=float(r["longitude"]) if r.get("longitude") else None,
                    signal_strength=r.get("signal_strength"),
                    confidence=r.get("confidence"),
                    source=r.get("source")
                )
                session.add(obs)
            session.commit()
            console.print(f"[green][+] Saved {len(records)} observations and linked entities to Evidence Vault.[/green]")
        finally:
            session.close()

    except Exception as e:
        console.print(f"[red]Ingestion failed: {e}[/red]")


@app.command()
def stream(hardware: str = typer.Option("rtl-sdr", help="Hardware to stream: rtl-sdr, adsb")):
    """Start a live hardware intelligence capture stream."""
    console.print(f"[*] Initializing live hardware capture for: [bold]{hardware}[/bold]")

    if hardware == "rtl-sdr":
        from parsers.sdr_stream import SDRStreamParser
        parser = SDRStreamParser()
        parser.start_stream()
    elif hardware == "adsb":
        from parsers.adsb import ADSBParser
        parser = ADSBParser()
        parser.start_stream()
    else:
        console.print(f"[red]Unsupported hardware: {hardware}[/red]")
        raise typer.Exit(1)


@app.command()
def export(identifier: str, format: str = typer.Option("csv", help="Export format: csv, json, kml, md, db")):
    """Export intelligence data to various formats.

    Args:
        identifier: Entity identifier to export
        format: Output format (csv, json, kml, md for markdown, db for database dump)
    """
    from core.database import SessionLocal, Entity
    session = SessionLocal()
    try:
        entity = session.query(Entity).filter(
            (Entity.value == identifier) | (Entity.id == int(identifier)) if identifier.isdigit() else (Entity.value == identifier)
        ).first()

        if not entity:
            console.print(f"[red]Error: Entity '{identifier}' not found in Evidence Vault.[/red]")
            raise typer.Exit(1)

        # Get all observations for this entity
        observations = session.query(Observation).filter_by(entity_id=entity.id).all()
        entities = [entity] + [Observation(
            id=o.id, type="OBSERVATION",
            value=f"{o.observation_type}:{o.cell_id}",
            normalized_value=str(o.timestamp),
            source=o.source
        ) for o in observations]

        timestamp = session.query(Observation).filter_by(entity_id=entity.id).first()
        if timestamp:
            timestamp = str(timestamp.timestamp)
        else:
            timestamp = "unknown"

    finally:
        session.close()

    # Export based on format
    if format == "csv":
        filepath = export_csv([{
            "id": entity.id,
            "type": entity.type,
            "value": entity.value,
            "source": entity.source
        }], filename=f"entity_{entity.value.replace('+', '')}_{timestamp[:10]}.csv")
        console.print(f"[green][+] Exported CSV to: {filepath}[/green]")
    elif format == "json":
        filepath = export_json([{
            "id": entity.id,
            "type": entity.type,
            "value": entity.value,
            "source": entity.source
        }], filename=f"entity_{entity.value.replace('+', '')}_{timestamp[:10]}.json")
        console.print(f"[green][+] Exported JSON to: {filepath}[/green]")
    elif format == "kml":
        filepath = export_kml([{
            "id": entity.id,
            "type": entity.type,
            "value": entity.value,
            "source": entity.source
        }], filename=f"entity_{entity.value.replace('+', '')}_{timestamp[:10]}.kml")
        console.print(f"[green][+] Exported KML to: {filepath}[/green]")
    elif format == "md":
        filepath = export_markdown_report([{
            "id": entity.id,
            "type": entity.type,
            "value": entity.value,
            "source": entity.source
        }], filename=f"entity_{entity.value.replace('+', '')}_{timestamp[:10]}.md")
        console.print(f"[green][+] Exported Markdown to: {filepath}[/green]")
    elif format == "db":
        filepath = export_database_dump(f"xghostsignal_export_{timestamp[:10]}.sql")
        console.print(f"[green][+] Database dump saved to: {filepath}[/green]")
    else:
        console.print(f"[red]Unknown format: {format}. Use: csv, json, kml, md, db[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
