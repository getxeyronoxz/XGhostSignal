# XGhostSignal - Configuration Guide

## Configuration Files

### Core Configuration

**File:** `core/config.py`

```python
# Mobile Country Codes (MCC) - Filter tower data by country
ALLOWED_MCCS = [
    404, 405,  # India
    410,       # Pakistan
    460,       # China
    310, 311, 312, 313, 314, 315, 316,  # USA
    250        # Russia
]

# ISO-3166-1 alpha-2 country codes - Phone number parsing
ALLOWED_COUNTRY_CODES = [
    "IN",  # India
    "PK",  # Pakistan
    "CN",  # China
    "US",  # USA
    "RU"   # Russia
]

# Database path
DB_PATH = "sqlite:///xghostsignal.db"
```

### Database Configuration

**Default:** SQLite database at `xghostsignal.db`

To change database location:
```python
DB_PATH = "sqlite:////path/to/your/database.db"
```

### LLM Configuration

**File:** `services/llm.py`

```python
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:8b"  # Change to your model
```

To use a different model:
```python
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral:7b-instruct"
```

## Hardware Configuration

### RTL-SDR Settings

**File:** `parsers/sdr_stream.py`

```python
class SDRStreamParser(BaseParser):
    def __init__(self):
        self.center_freq = 900e6      # Default: GSM 900 MHz
        self.sample_rate = 2.4e6      # Default: 2.4 MSps
        self.gain = 40                # Default: 40 dB
        self.buffer_size = 1024
```

### ADS-B Settings

**File:** `parsers/adsb.py`

```python
class ADSBParser(BaseParser):
    def __init__(self):
        self.default_host = "127.0.0.1"
        self.default_port = 30003     # dump1090 default
```

## Environment Variables

Optional environment variables:

```bash
# Database path
export XGS_DB_PATH="/path/to/database.db"

# Ollama URL
export XGS_OLLAMA_URL="http://localhost:11434"

# Log level
export XGS_LOG_LEVEL="info"
```

## Web UI Configuration

### Server Settings

**File:** `main.py`

```python
def start_server(host="127.0.0.1", port=8080):
    uvicorn.run(app, host=host, port=port, log_level="info")
```

Change port:
```bash
python -m cli_app.main serve --port 8081
```

### Static Files

**Directory:** `static/`

- `index.html` - Main HTML page
- `app.js` - Client-side JavaScript
- `style.css` - Custom styling

### CORS Configuration (Production)

For production deployments, add CORS middleware:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Logging

### Enable SQL Logging

```python
engine = create_engine(DB_PATH, echo=True)  # Set echo=True
```

### Custom Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("xghostsignal")
```

## Security Configuration

### File Permissions (Linux/Mac)

```bash
# Set restrictive permissions on database
chmod 600 xghostsignal.db

# Set restrictive permissions on reports
chmod 600 reports/
```

### Input Validation

All user inputs are validated:
- Phone numbers must match allowed country codes
- File paths are validated for directory traversal
- All database queries use parameterized statements

## Performance Tuning

### Database Optimization

```python
# Increase SQLite timeout
DB_PATH = "sqlite:///xghostsignal.db?timeout=60"

# Enable WAL mode for better concurrency
# Add after engine creation:
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))
```

### Memory Management

For large datasets:
```python
# Use pagination
entities = session.query(Entity).offset(0).limit(1000).all()
```

## Troubleshooting Configuration

### Database Locked Errors

```bash
# Close all processes using the database
# Then restart
```

### Port Already in Use

```bash
# Check what's using the port
netstat -ano | findstr :8080  # Windows
lsof -i :8080                 # Linux/Mac

# Kill the process
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # Linux/Mac
```

## Configuration Validation

Run this to verify configuration:

```bash
python -c "
from core.config import ALLOWED_MCCS, ALLOWED_COUNTRY_CODES, DB_PATH
print('MCCs:', ALLOWED_MCCS)
print('Country Codes:', ALLOWED_COUNTRY_CODES)
print('DB Path:', DB_PATH)
"
```
