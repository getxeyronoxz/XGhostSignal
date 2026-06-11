# XGhostSignal - Technical Documentation

## Overview

This document provides detailed technical documentation for XGhostSignal developers and contributors.

## Architecture

### Core Components

```
xghostsignal/
├── cli_app/          # CLI commands (Typer)
├── api/              # FastAPI routes
├── core/             # Database models & config
├── services/         # Business logic
├── plugins/          # Plugin system
├── parsers/          # Data parsers
├── static/           # Web UI (HTML, JS, CSS)
└── tests/            # Test suite
```

### Data Flow

1. **Input** → Raw data (CSV, PCAP, SDR, ADS-B)
2. **Parser** → Normalized records
3. **Database** → SQLite Evidence Vault
4. **Analysis** → Graph correlation, geospatial
5. **Export** → CSV, JSON, KML, Markdown

## Database Schema

### Tables

#### entities
```sql
CREATE TABLE entities (
    id INTEGER PRIMARY KEY,
    type TEXT,              -- PHONE_NUMBER, CELL_TOWER, RF_EMITTER, etc.
    value TEXT UNIQUE,      -- Original value
    normalized_value TEXT,  -- Normalized format
    source TEXT,            -- Source identifier
    created_at DATETIME
);
```

#### observations
```sql
CREATE TABLE observations (
    id INTEGER PRIMARY KEY,
    entity_id INTEGER,      -- Foreign key to entities
    observation_type TEXT,  -- Type of observation
    protocol TEXT,          -- Protocol name
    frequency TEXT,         -- Frequency in Hz
    mcc TEXT,               -- Mobile Country Code
    mnc TEXT,               -- Mobile Network Code
    lac_tac TEXT,           -- Location Area Code / Tracking Area Code
    cell_id TEXT,           -- Cell identifier
    latitude FLOAT,
    longitude FLOAT,
    signal_strength TEXT,
    confidence TEXT,        -- low, medium, high
    source TEXT,
    timestamp DATETIME
);
```

#### towers
```sql
CREATE TABLE towers (
    id INTEGER PRIMARY KEY,
    mcc INTEGER,
    mnc INTEGER,
    lac_tac INTEGER,
    cell_id INTEGER,
    band TEXT,
    latitude FLOAT,
    longitude FLOAT,
    sector FLOAT,
    source TEXT
);
```

#### links
```sql
CREATE TABLE links (
    id INTEGER PRIMARY KEY,
    left_entity_id INTEGER,
    right_entity_id INTEGER,
    link_type TEXT,
    confidence FLOAT,
    reason TEXT
);
```

#### imports
```sql
CREATE TABLE imports (
    id INTEGER PRIMARY KEY,
    filename TEXT,
    file_hash TEXT,
    imported_at DATETIME,
    source_type TEXT,
    record_count INTEGER
);
```

## Parser Interface

All parsers must implement the `BaseParser` interface:

```python
from parsers.base import BaseParser

class CustomParser(BaseParser):
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse file and return normalized records."""
        records = []
        # Parse file...
        for item in parsed_items:
            record = self.create_unified_record(
                source="custom_parser",
                protocol=item.protocol,
                frequency=item.frequency,
                mcc=item.mcc,
                mnc=item.mnc,
                cell_id=item.cell_id,
                latitude=item.latitude,
                longitude=item.longitude,
                confidence="high"
            )
            records.append(record)
        return records
```

### Record Schema

Each record must be a dictionary with these fields:
- `timestamp` (optional): ISO format timestamp
- `source` (optional): Source identifier
- `protocol` (required): Protocol name
- `frequency` (optional): Frequency in Hz
- `mcc` (optional): Mobile Country Code
- `mnc` (optional): Mobile Network Code
- `lac_tac` (optional): Location Area/Tracking Area Code
- `cell_id` (optional): Cell identifier
- `latitude` (optional): WGS84 latitude
- `longitude` (optional): WGS84 longitude
- `signal_strength` (optional): Signal strength
- `confidence` (optional): "low", "medium", or "high"

## Plugin System

### Creating a Plugin

1. Create a Python file in `plugins/default/` or `plugins/custom/`:

```python
# plugins/custom/my_plugin.py
PLUGIN_NAME = "my_plugin"
VERSION = "1.0.0"

def run(number: str, region: str = None) -> dict:
    """Plugin entry point."""
    try:
        # Your logic here
        return {
            "status": "success",
            "data": "result"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

2. The plugin will be automatically loaded by the registry.

### Plugin Registry API

```python
from plugins.registry import registry

# Load plugins from directory
registry.load_plugins("plugins/default")

# Get active plugins
active = registry.get_active_plugins()

# Run a plugin
result = registry.run_plugin("my_plugin", number="+1234567890")
```

## API Routes

### Authentication (None - Local Only)

Since this is a local-first application, no authentication is implemented. All endpoints are available on the localhost interface.

### Rate Limiting (Recommended)

For production deployments, add rate limiting:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

# Add to main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.get("/health")
@limiter.limit("10/minute")
def health_check(request: Request):
    return {"status": "healthy"}
```

## Security Considerations

### Input Validation

Always validate user input:

```python
from pydantic import BaseModel, field_validator

class SearchRequest(BaseModel):
    number: str

    @field_validator('number')
    @classmethod
    def validate_number(cls, v):
        if not v:
            raise ValueError('Phone number is required')
        return v.strip()
```

### SQL Injection Prevention

Use SQLAlchemy's parameterized queries (automatically handled):

```python
# Safe - parameterized query
entity = session.query(Entity).filter_by(value=req.number).first()

# Never do this - string concatenation
# query = f"SELECT * FROM entities WHERE value = '{req.number}'"
```

### Path Traversal Prevention

Validate file paths:

```python
import os
from fastapi import HTTPException

def safe_file_path(user_path: str, base_dir: str) -> str:
    full_path = os.path.abspath(os.path.join(base_dir, user_path))
    if not full_path.startswith(os.path.abspath(base_dir)):
        raise HTTPException(status_code=400, detail="Invalid file path")
    return full_path
```

## Testing

### Running Tests

```bash
pytest tests/ -v
```

### Writing Tests

```python
import pytest
from core.database import Base, Entity, init_db

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="module")
def test_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_database_models(test_session):
    entity = Entity(
        type="phone",
        value="+123",
        source="test"
    )
    test_session.add(entity)
    test_session.commit()
    
    queried = test_session.query(Entity).filter_by(value="+123").first()
    assert queried is not None
    assert queried.type == "phone"
```

## Performance Considerations

### Database Optimization

1. Use indexes on frequently queried columns
2. Implement pagination for large result sets
3. Use connection pooling (already configured in SQLAlchemy)

### Memory Management

```python
# Process data in chunks
for chunk in chunks(data, 1000):
    process(chunk)
```

## Deployment

### Local Deployment

```bash
python -m cli_app.main serve --host 127.0.0.1 --port 8080
```

### Production Deployment

For production use, run with a proper ASGI server:

```bash
# Install uvicorn[standard] for production
pip install uvicorn[standard]

# Run with more workers
uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## Troubleshooting

### Common Issues

1. **RTL-SDR not detecting device**
   - Check USB permissions (Linux: `sudo usermod -a -G plugdev $USER`)
   - Reinstall Zadig driver (Windows)
   - Check `lsusb` output

2. **Web UI not loading**
   - Check port is not in use: `netstat -ano | findstr :8080`
   - Check static files exist in `static/` directory
   - Check browser console for errors

3. **Database locked errors**
   - Close any other processes using the database
   - Increase SQLite timeout: `DB_PATH = "sqlite:///xghostsignal.db?timeout=60"`

## Contributing Guidelines

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all public functions
- Keep functions under 50 lines

### Pull Request Process

1. Create a feature branch
2. Run tests: `pytest tests/ -v`
3. Update documentation if needed
4. Submit PR with clear description

## License

MIT License - See LICENSE file for details.
