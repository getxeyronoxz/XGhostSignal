# XGhostSignal - Agent Guide

Local-first OSINT/cellular intelligence workbench. Python 3.9+, Typer CLI, FastAPI API, SQLAlchemy ORM (SQLite), vanilla JS frontend.

## Entry Points

| Command | What it does |
|---------|-------------|
| `xgs <command>` | CLI (maps to `cli_app.main:app`) |
| `python -m xghostsignal -g` | CLI via module |
| `python -m xghostsignal` or `python main.py` | Web server (FastAPI on port 8080) |
| `python -m cli_app.main <command>` | CLI without install |

`main.py` auto-detects mode: if argv[1] is a CLI subcommand (`serve`, `init`, `search`, `report`, `summarize`, `ingest`, `stream`), it runs the Typer app; otherwise it starts the web server.

## Development Commands

```bash
pip install -r requirements.txt   # or: pip install -e .
xgs init                           # create SQLite database (xghostsignal.db)
pytest tests/ -v                   # run tests
```

Tests use in-memory SQLite (`sqlite:///:memory:`) — the test fixture creates its own engine and does not touch the app database.

## Architecture

```
core/          config.py (country scope, DB path) + database.py (SQLAlchemy models)
cli_app/       main.py (Typer CLI: init, search, report, summarize, ingest, stream, export, serve)
api/           routes.py (FastAPI: /api/* endpoints, served on :8080)
services/      export.py, reports.py, llm.py, graph.py
parsers/       base.py (BaseParser ABC) + specific parsers (opencellid, cellmapper, rtl_power, pcap, sdr_stream, adsb)
plugins/       registry.py (dynamic loader) + default/ (phone_intel, leak_search, dns_recon)
static/        index.html, app.js, style.css (vanilla frontend, no build step)
```

### Data Flow
Raw data (CSV, PCAP, SDR) → Parsers → Unified schema → SQLite → Graph analysis → Export (CSV/JSON/KML/MD/SQL)

### Key Constraints
- **Country scope is hardcoded** in `core/config.py`: only IN, PK, CN, US, RU (via `ALLOWED_COUNTRY_CODES` and `ALLOWED_MCCS`). Queries outside these are rejected.
- **Database**: SQLite at `xghostsignal.db` (gitignored).
- **Export/output dirs**: `exports/`, `reports/` are created at runtime and gitignored.
- **Web server**: port 8080 (not 8000).
- **LLM**: Ollama at `http://localhost:11434`, model `llama3:8b` — required for `xgs summarize`.

### Parser Pattern
All parsers inherit from `parsers/base.py:BaseParser` and implement `parse_file() -> List[Dict]`. They use `create_unified_record()` to produce a normalized dict with keys: timestamp, source, protocol, frequency, mcc, mnc, lac_tac, cell_id, latitude, longitude, signal_strength, confidence.

### Plugin System
Plugins need `PLUGIN_NAME` and `run()` in their module. The registry auto-loads from a directory. Default plugins live in `plugins/default/`.

### Database Models (SQLAlchemy)
`Entity` (tracked identifiers), `Observation` (RF/geospatial sightings, linked to Entity), `Tower`, `Link` (entity correlations), `ImportLog`.

## Security Notes
- API has no authentication — server binds to `127.0.0.1` by default. Do not expose to untrusted networks.
- Import endpoint (`POST /api/import`) resolves paths within a `data/` root to prevent path traversal.
- Export/report filenames are sanitized to prevent path traversal.
- KML export escapes XML entities to prevent injection.

## Database Notes
- SQLite runs in WAL mode with 30s timeout for concurrent writer support.
- Foreign keys are enabled via `PRAGMA foreign_keys=ON`.
- Entity upsert uses `session.flush()` instead of per-row `commit()` to avoid race conditions.

## Notes
- Version is 0.2.0 (in sync across `__init__.py`, `pyproject.toml`, and `CHANGELOG.md`).
- `xghostsignal.db`, `reports/`, `exports/`, `*.csv`, `*.pcap`, `*.db` are all gitignored (intelligence data should not be committed).
- Hatchling build system; `pyproject.toml` lists wheel packages: `core`, `cli_app`, `services`, `api`, `plugins`, `parsers`.
- `pandas`, `geopandas`, `shapely`, `pyyaml`, `ollama`, and `requests` were removed as unused dependencies.
- `services/geo.py` was deleted (dead code — only module using pandas/geopandas).
