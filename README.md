# XGhostSignal

> **Local-First OSINT & Cellular Intelligence Workbench**
>
> Cell tower mapping · Phone enrichment · RF signal detection · Entity correlation

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/getxeyronoxz/XGhostSignal/releases/tag/v0.2.0)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

**XGhostSignal** is a local-first intelligence tool for mapping cell towers, enriching phone number metadata, correlating identifiers across datasets, and analyzing RF signals. It features a CLI (`xgs`) for power users and a web GUI for visualization.

**Your data never leaves your machine.** No telemetry, no cloud, no external APIs.

---

## Features

- **Phone Intelligence** — E.164 normalization, carrier/location lookup, validity checks (scoped to IN, PK, CN, US, RU)
- **Cell Tower Mapping** — Import and visualize tower data from OpenCelliD, CellMapper, and RTL-Power
- **RF Signal Detection** — Live RTL-SDR streaming with signal burst detection
- **ADS-B Aviation Tracking** — Real-time aircraft position data from dump1090
- **Entity Correlation** — Automatic co-location analysis and graph-based relationship mapping
- **Breach Checking** — Local LMDB/SQLite-based phone number leak database
- **LLM Summarization** — Tactical AI summaries via local Ollama (llama3:8b)
- **Multiple Export Formats** — CSV, JSON, KML (Google Earth), Markdown, SQLite dump
- **Plugin System** — Extend with custom plugins in `plugins/custom/`
- **REST API** — Full FastAPI backend with Swagger/ReDoc documentation
- **Web Dashboard** — Leaflet maps + Cytoscape graph visualization, zero build step

---

## Quick Start

```bash
# Clone
git clone https://github.com/getxeyronoxz/XGhostSignal.git
cd XGhostSignal

# Setup
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install
pip install -r requirements.txt
pip install -e .

# Initialize database
xgs init

# Search a phone number
xgs search "+919876543210"

# Generate report
xgs report "+919876543210"

# Start web UI
xgs serve
# Open http://localhost:8080
```

---

## Installation

### Requirements
- Python 3.9+
- pip or uv package manager

### From Source
```bash
git clone https://github.com/getxeyronoxz/XGhostSignal.git
cd XGhostSignal
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install -e .  # Installs `xgs` command globally
```

### Development Install
```bash
pip install -e ".[dev]"  # Includes pytest and testing tools
```

---

## Usage

### CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `xgs init` | Initialize SQLite database | `xgs init` |
| `xgs search <number>` | Search and enrich a phone number | `xgs search "+919876543210"` |
| `xgs report <number>` | Generate Markdown dossier | `xgs report "+919876543210"` |
| `xgs summarize <number>` | Generate dossier + LLM summary | `xgs summarize "+919876543210"` |
|`xgs ingest <file> --parser-type <type>` | Ingest RF/telecom data | `xgs ingest data.csv --parser-type opencellid` |
| `xgs stream <hardware>` | Live hardware capture | `xgs stream rtl-sdr` |
| `xgs export <id> --format <fmt>` | Export data | `xgs export "+919876543210" --format kml` |
| `xgs serve` | Start web UI server | `xgs serve` |

### Supported Parsers
- `opencellid` — OpenCelliD CSV exports
- `cellmapper` — CellMapper CSV exports
- `rtl_power` — RTL-Power spectrum scans
- `pcap` — PCAP/PCAPNG packet captures (requires scapy)
- `sdr_stream` — Live RTL-SDR streaming
- `adsb` — ADS-B aviation data (requires dump1090)

### Web Interface

Start the server:
```bash
xgs serve
```

Navigate to `http://localhost:8080` for:
- **Interactive Map** — Leaflet-based tower visualization
- **Correlation Graph** — Cytoscape.js entity relationship graph
- **Console** — Real-time operation logging

### API Documentation

Once running:
- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`

---

## Configuration

### Country Scope
Edit `core/config.py` to modify allowed regions (default: IN, PK, CN, US, RU):
```python
ALLOWED_COUNTRY_CODES = ["IN", "PK", "CN", "US", "RU"]
ALLOWED_MCCS = [404, 405, 410, 460, 310, 311, 312, 313, 314, 315, 316, 250]
```

### Database
Default: SQLite at `xghostsignal.db` (WAL mode, 30s timeout)

### LLM Settings
Ollama at `http://localhost:11434`, model `llama3:8b` (required only for `xgs summarize`)

---

## Architecture

```
core/          Config (country scope, DB path) + SQLAlchemy models
cli_app/       Typer CLI (init, search, report, summarize, ingest, stream, export, serve)
api/           FastAPI REST endpoints (/api/*)
services/      Export, Reports, LLM, Graph analysis
parsers/       Unified Parser Engine (BaseParser ABC + specific parsers)
plugins/       Dynamic plugin loader + default plugins
static/        Vanilla HTML/CSS/JS frontend (no build step)
```

### Data Flow
```
Raw Data (CSV, PCAP, SDR) → Parsers → Unified Schema → SQLite
                                                         ↓
                                                   Graph Analysis
                                                         ↓
                                              Export (CSV/JSON/KML/MD/SQL)
```

### Technology Stack
- **Python 3.9+**, **Typer** (CLI), **FastAPI** (API), **SQLAlchemy** (ORM)
- **SQLite** with WAL mode for concurrent access
- **NetworkX** for graph correlation
- **Phonenumbers** for phone parsing
- **Scapy** for PCAP parsing, **PyRtlSdr** for RTL-SDR
- **Leaflet** + **Cytoscape.js** for web visualization

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Development Setup
```bash
git clone https://github.com/getxeyronoxz/XGhostSignal.git
cd XGhostSignal
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

### How to Contribute
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Commit: `git commit -m "Add your feature"`
6. Push: `git push origin feature/your-feature`
7. Open a Pull Request

### Adding a Parser
```python
# parsers/custom_parser.py
from parsers.base import BaseParser

class CustomParser(BaseParser):
    def parse_file(self, file_path: str):
        # Your parsing logic
        return records
```

### Adding a Plugin
```python
# plugins/custom/my_plugin.py
PLUGIN_NAME = "my_plugin"

def run(arg1: str) -> dict:
    return {"status": "success", "result": arg1}
```

---

## Project Structure

```
XGhostSignal/
├── core/               # Configuration and database models
├── cli_app/            # Typer CLI application
├── api/                # FastAPI REST routes
├── services/           # Business logic (export, reports, LLM, graph)
├── parsers/            # Unified parser engine
├── plugins/            # Plugin system + default plugins
├── static/             # Web frontend (HTML/CSS/JS)
├── tests/              # Test suite
├── docs/               # Documentation
├── main.py             # Web server entry point
├── __main__.py         # Module entry point
├── pyproject.toml      # Package configuration
├── requirements.txt    # Dependencies
├── CHANGELOG.md        # Version history
├── CONTRIBUTING.md     # Contribution guidelines
├── LICENSE             # MIT License
└── AGENTS.md           # AI assistant guidance
```

---

## Security

- **Local-first** — All data stays on your machine
- **No telemetry** — No tracking, no external calls (except optional Ollama)
- **Path traversal protection** — Import/export paths sanitized
- **XML escaping** — KML export prevents injection
- **SQLite WAL mode** — Concurrent access without corruption

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [OpenCelliD](https://opencellid.org) — Cell tower database
- [dump1090](https://github.com/antirez/dump1090) — ADS-B decoding
- [PyRtlSdr](https://github.com-roger-/pyrtlsdr) — RTL-SDR support
- [Scapy](https://scapy.net) — Packet parsing
- [Ollama](https://ollama.ai) — Local LLM inference

---

## Disclaimer

This tool is for **educational and authorized security testing purposes only**. Ensure you have proper authorization before conducting any testing. The authors are not responsible for misuse of this tool.
