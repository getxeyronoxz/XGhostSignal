# XGhostSignal

> **Local-First OSINT and Cellular Intelligence Workbench**  
> *A secure enclave for defensive research, telecom study, and geospatial correlation.*

## Overview

**XGhostSignal** is a robust, production-grade intelligence tool built for mapping cell towers, enriching phone number metadata, and correlating identifiers across datasets. It features a tactical dual-interface: a high-speed CLI (`xgs`) for power users and a fully-featured, dark-mode web GUI for detailed visualization.

### 🌍 Target Scope Constraint
To ensure high fidelity, accuracy, and compliance, the core logic (phone parsing, MCC/MNC tower filtering, and geospatial boundaries) is strictly scoped to **five specific target nations**:
*   🇮🇳 **India**
*   🇵🇰 **Pakistan**
*   🇨🇳 **China**
*   🇺🇸 **USA**
*   🇷🇺 **Russia**

*Queries outside of these regions will be automatically rejected by the engine.*

---

## Installation

XGhostSignal is built as a modular Python package.

```bash
# Clone the repository
git clone https://github.com/xeyronox/XGhostSignal.git
cd XGhostSignal

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

Once installed, the `xgs` command becomes globally available on your terminal.

---

## Usage Guide

### 1. Initializing the Database

Before running any intelligence queries, you must initialize the local SQLite secure enclave:

```bash
xgs init
# Or
python -m cli_app.main init
```

### 2. Tactical CLI Commands

The CLI is designed for rapid batch analysis and data ingestion.

**Search an Identifier (Phone Number):**
```bash
xgs search "+919876543210"
```
*Provides E.164 normalization, country code, carrier context, and validity checks.*

**Generate Intelligence Report:**
```bash
xgs report "+919876543210"
```
*Creates a comprehensive Markdown dossier in `reports/` directory.*

**Summarize with Local LLM:**
```bash
xgs summarize "+919876543210"
```
*Requires Ollama running locally with `llama3:8b` model.*

**Ingest Signal Intelligence Logs:**
```bash
xgs ingest path/to/data.csv --parser-type opencellid
xgs ingest path/to/power.csv --parser-type rtl_power
xgs ingest path/to/capture.pcap --parser-type pcap
```
*The Unified Parser Engine routes RF captures, SDR logs, and CSVs into a strict normalized JSON schema before hitting the Evidence Vault.*

**Live Hardware Streaming:**
```bash
xgs stream rtl-sdr
xgs stream adsb
```
*Capture real-time RTL-SDR signals or ADS-B aircraft data.*

**Export Data:**
```bash
xgs export "+919876543210" --format csv
xgs export "+919876543210" --format json
xgs export "+919876543210" --format kml
xgs export "+919876543210" --format md
xgs export "+919876543210" --format db
```

### 3. The Evidence Vault & Local AI

Generate a comprehensive Markdown dossier for an entity:
```bash
xgs report "+919876543210"
```
*Outputs a timestamped file into the `reports/` directory.*

To automatically summarize this dossier using a Local LLM (requires Ollama running `llama3:8b` locally):
```bash
xgs summarize "+919876543210"
```
*Your data never leaves the machine.*

### 4. Launching the Tactical UI

To visualize your intelligence, you must run the API server which serves the vanilla frontend dynamically.

**Start the API Enclave (Port 8080)**
```bash
xgs serve
# Or
python -m cli_app.main -g
```

Navigate to `http://localhost:8080` to view the live dashboard. The UI features a custom dark CartoDB Leaflet integration for tracking coordinates and a Cytoscape Graph engine for network correlations, served purely through high-speed vanilla JavaScript and HTML.

---

## Advanced Plugins

Create custom plugins in `plugins/custom/`:

```python
# plugins/custom/my_plugin.py
PLUGIN_NAME = "my_plugin"
VERSION = "1.0.0"

def run(arg1: str, arg2: int = 10) -> dict:
    """Plugin entry point."""
    return {"status": "success", "result": f"Processed {arg1} {arg2} times"}
```

---

## Architecture

XGhostSignal strictly adheres to local-first principles.

### Backend Stack
- **Python 3.9+**
- **Typer** - CLI framework
- **FastAPI** - Web API server
- **SQLAlchemy** - Database ORM (SQLite)
- **Geopandas & Shapely** - Geospatial analysis
- **NetworkX** - Graph correlation

### Frontend Stack
- **Vanilla HTML/CSS/JavaScript** - No build tools
- **Leaflet 1.9** - Interactive maps
- **Cytoscape.js 3.28** - Graph visualization

### Data Flow
```
Raw Data (CSV, PCAP, SDR) → Parsers → Normalized Schema → SQLite Evidence Vault
                                                              ↓
                                                        Graph Analysis
                                                              ↓
                                                         Export Formats
```

---

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`

### Endpoints Summary
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Overall statistics |
| GET | `/api/stats/detailed` | Detailed breakdown |
| GET | `/api/entities` | List all entities |
| GET | `/api/towers` | Cell tower data |
| GET | `/api/towers/bbox` | Towers in bounding box |
| GET | `/api/graph` | Entity correlation graph |
| POST | `/api/search` | Search phone number |
| POST | `/api/export` | Export data |
| GET | `/api/health` | Health check |

---

## Configuration

### Country/Region Filtering

Edit `core/config.py` to modify allowed regions:

```python
# Mobile Country Codes (MCC)
ALLOWED_MCCS = [404, 405, 410, 460, 310, 311, 312, 313, 314, 315, 316, 250]

# ISO-3166-1 alpha-2 country codes
ALLOWED_COUNTRY_CODES = ["IN", "PK", "CN", "US", "RU"]
```

### Database Settings

Default: SQLite at `xghostsignal.db`

```python
DB_PATH = "sqlite:///xghostsignal.db"
```

### LLM Settings

Default: Ollama at `http://localhost:11434`

```python
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:8b"
```

---

## Hardware Support

### RTL-SDR Setup

1. **Install PyRtlSdr:**
   ```bash
   pip install pyrtlsdr
   ```

2. **Windows Driver Setup:**
   - Download [Zadig](https://zadig.akeo.ie)
   - Select RTL2832U device
   - Install LibUSB Win32 driver

3. **Linux Udev Rules:**
   ```bash
   sudo cp docs/rtl-sdr.rules /etc/udev/rules.d/
   sudo udevadm control --reload-rules
   ```

### ADS-B Setup

1. **Install dump1090:**
   ```bash
   # Windows
   # Download from https://github.com/antirez/dump1090
   
   # Linux
   sudo apt-get install dump1090-mutability
   ```

2. **Start dump1090:**
   ```bash
   dump1090 --net --net-sbs-port 30003
   ```

---

## Security

### Local-First Architecture
- All data stays on your machine
- No external API calls (except optional Ollama)
- No telemetry or tracking
- No cloud synchronization

### Privacy Features
- Phone numbers are hashed for leak checking
- No data leaves your system
- Local-only graph analysis
- Optional breach database (SQLite-based)

---

## Troubleshooting

### RTL-SDR Not Working
```bash
# Check device detection
python -c "from rtlsdr import RtlSdr; sdr = RtlSdr()"
```

### Web UI Not Starting
```bash
# Check port availability
# Windows: netstat -ano | findstr :8080
# Linux/Mac: lsof -i :8080
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
git clone https://github.com/xeyronox/XGhostSignal.git
cd XGhostSignal
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Run tests
pytest tests/ -v
```

### Adding New Features

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `pytest tests/ -v`
4. Commit: `git commit -m "Add your feature"`
5. Push: `git push origin feature/your-feature`
6. Open a Pull Request

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- OpenCelliD for tower database
- Dump1090 for ADS-B decoding
- PyRtlSdr for RTL-SDR support
- Scapy for packet parsing

---

## Disclaimer

This tool is for educational and authorized security testing purposes only. Ensure you have proper authorization before conducting any testing. The authors are not responsible for misuse of this tool.
