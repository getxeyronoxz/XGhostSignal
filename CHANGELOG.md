# XGhostSignal - Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- Added path traversal protection on `POST /api/import` (files restricted to `data/` root)
- Added filename sanitization for exports and reports
- Fixed KML/XML injection via proper entity escaping in export module
- Bumped `fastapi` to `>=0.115` (fixes CVE-2024-47874 in Starlette)

### Added
- `AGENTS.md` — AI assistant guidance for future development sessions
- `CONTRIBUTING.md` — contribution guidelines for forkers and contributors
- `xgs serve` command — start web UI server (previously documented but non-functional)
- SQLite WAL mode with 30s timeout for concurrent writer support
- Foreign keys pragma enabled on database connections
- `pytest` added to `[project.optional-dependencies].dev`
- GitHub topics/tags for discoverability

### Fixed
- **B1**: Fixed `POST /api/export` crash from `get_all_entities` name shadowing
- **B3**: Fixed plugin registry import path (`xghostsignal.plugins` → `plugins`)
- **B4**: Removed broken `GSMPacket` import from PCAP parser
- **B5**: Removed fabricated evidence from PCAP parser (no more fake geolocation)
- **B6**: Removed broken `Observation` construction crashing `xgs export`
- **B9**: Fixed naive/aware datetime mismatch in stats endpoint
- **B13**: Fixed dashboard towers rendering (API response shape mismatch)
- **PR1**: Fixed `SDRStreamParser.parse_file()` to return `[]` instead of raising `NotImplementedError`
- **PR3**: Fixed `latitude=0`/`longitude=0` being dropped (truthiness → `is not None`)
- **DB3**: Fixed entity race condition with `flush()` + single commit pattern
- **DB4**: Removed per-row `commit()` on import — now single outer commit
- **DB5**: Added SQLite timeout and WAL mode for concurrent access
- **P1-P3**: Replaced deprecated `datetime.utcnow()` with timezone-aware `datetime.now(timezone.utc)`
- **C1**: Synced version to `0.2.0` across `__init__.py`, `pyproject.toml`, and `CHANGELOG.md`
- **C2**: Added working `xgs serve` command (was documented but missing)

### Changed
- Updated `README.md` — comprehensive rewrite for contributors and forkers
- Updated `pyproject.toml` — removed unused deps, added dev dependencies
- Updated `requirements.txt` — removed unused dependencies
- Updated GitHub repo description and topics

### Removed
- Removed unused dependencies: `pandas`, `geopandas`, `shapely`, `pyyaml`, `ollama`, `requests`
- Deleted dead code: `services/geo.py`

## [0.2.0] - 2026-06-10

### Added
- **Real RTL-SDR Hardware Integration** - Full `pyrtlsdr` support with configurable frequency, gain, sample rate, and signal detection
- **Real PCAP Parsing** - Full `scapy` integration for LTE S1AP, NAS, GSM RR, and generic packet extraction
- **Real ADS-B Streaming** - dump1090 integration for aircraft tracking
- **SQLite Leak Database** - Breach database with phone normalization, hash-based lookups, and HIBP-compatible import
- **Export Services Module** - CSV, JSON, KML, Markdown, and database dump exports
- **CLI Export Command** - `xgs export <identifier> --format csv|json|kml|md|db`
- **Enhanced API Routes** - 20+ new endpoints including export, search enrichment, and detailed stats
- **SQLAlchemy UTC Support** - Fixed deprecated `datetime.utcnow()` warnings with timezone-aware `utc_now()`
- **Requirements File** - Added `requirements.txt` for easy dependency installation
- **Package Entry Point** - `__main__.py` for `python -m xghostsignal` execution

### Fixed
- Circular import between `main.py` and `cli_app/main.py`
- `pyproject.toml` packages list (removed `main.py`, added `cli_app`)
- Hardcoded module path in `plugins/registry.py` - now uses relative paths
- Observation creation bug in ingest command (Entity → Observation)
- UK phone logic test (Channel Islands GG detection)

### Changed
- `main.py` - Clean entry point with CLI/web detection
- `cli_app/main.py` - Standalone CLI with proper imports
- `services/graph.py` - Already had required functions
- All parsers use relative imports

## [0.1.0] - Initial Release

### Added
- Core CLI commands (init, search, report, ingest, stream)
- Web UI with Leaflet map and Cytoscape graph
- Phone number parsing with phonenumbers library
- MCC-based country filtering (India, Pakistan, China, USA, Russia)
- Plugin registry system
- Basic parsers (OpenCelliD, CellMapper, rtl_power, PCAP)
- LLM integration via Ollama

---

## Project Status

### Current Version: 0.2.0

### Planned Features
- [ ] Real tower database API integration (OpenCelliD/CellMapper)
- [ ] SS7 signaling analysis
- [ ] IMSI catchers integration
- [ ] Advanced correlation algorithms
- [ ] Timeline analysis
- [ ] Export to additional formats (PDF, Excel)

### Known Limitations
- Local breach database requires manual population
- RTL-SDR requires proper hardware setup
- ADS-B requires dump1090 running locally
- Ollama required for LLM summarization
