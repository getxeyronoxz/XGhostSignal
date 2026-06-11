# XGhostSignal - Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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