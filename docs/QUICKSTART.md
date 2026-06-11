# XGhostSignal - Quick Start Guide

## For New Users

### 1. Quick Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
xgs init
```

### 2. Basic Usage

```bash
# Search a phone number
xgs search "+919876543210"

# View report
xgs report "+919876543210"
```

### 3. Start Web Interface

```bash
# Launch web UI
xgs serve
# Open http://localhost:8080 in your browser
```

---

## For Security Researchers

### 1. Import Cell Tower Data

```bash
# Import OpenCelliD data
xgs ingest towers.csv --parser opencellid

# Import rtl_power spectrum data
xgs ingest spectrum.csv --parser rtl_power
```

### 2. Live Signal Capture

```bash
# Start RTL-SDR capture
xgs stream rtl-sdr

# Start ADS-B aircraft tracking
xgs stream adsb
```

### 3. Export Intelligence

```bash
# Export as CSV for analysis
xgs export "+919876543210" --format csv

# Export as KML for Google Earth
xgs export "+919876543210" --format kml
```

---

## For Developers

### 1. Development Setup

```bash
# Clone repository
git clone https://github.com/xeyronox/XGhostSignal.git
cd XGhostSignal

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
pytest tests/ -v
```

### 2. Adding a Parser

Create `parsers/custom_parser.py`:

```python
from parsers.base import BaseParser

class CustomParser(BaseParser):
    def parse_file(self, file_path: str):
        # Your parsing logic
        return records
```

### 3. Adding a Plugin

Create `plugins/custom/my_plugin.py`:

```python
PLUGIN_NAME = "my_plugin"

def run(arg1: str) -> dict:
    return {"status": "success", "result": arg1}
```

---

## Common Tasks

| Task | Command |
|------|---------|
| Initialize database | `xgs init` |
| Search phone | `xgs search +919876543210` |
| Generate report | `xgs report +919876543210` |
| Import CSV | `xgs ingest file.csv --parser opencellid` |
| Start RTL-SDR | `xgs stream rtl-sdr` |
| Start ADS-B | `xgs stream adsb` |
| Export data | `xgs export ID --format csv/json/kml` |
| Launch web UI | `xgs serve` |

---

## Next Steps

1. Read the [README](../README.md) for full feature documentation
2. Check [docs/TECHNICAL.md](TECHNICAL.md) for architecture details
3. Join the community for support

---

## Support

- GitHub Issues: https://github.com/xeyronox/XGhostSignal/issues
- Documentation: https://github.com/xeyronox/XGhostSignal/docs
