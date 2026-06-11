# XGhostSignal - API Documentation

## Overview

XGhostSignal provides a comprehensive REST API for programmatic access to all features.

**Base URL:** `http://localhost:8080/api`

## Authentication

No authentication is required as this is a local-only application. All endpoints are accessible on the localhost interface.

## Endpoints

### Statistics

#### Get Overall Stats
```http
GET /api/stats
```

**Response:**
```json
{
  "entities_count": 15,
  "towers_count": 23,
  "observations_count": 156
}
```

#### Get Detailed Stats
```http
GET /api/stats/detailed
```

**Response:**
```json
{
  "entity_types": {
    "PHONE_NUMBER:cli_search": 5,
    "CELL_TOWER:parser": 10
  },
  "towers_with_coordinates": 142,
  "recent_observations_24h": 35,
  "total_links": 8
}
```

---

### Entities

#### List All Entities
```http
GET /api/entities?limit=100&offset=0&type_filter=PHONE_NUMBER
```

**Response:**
```json
{
  "total": 15,
  "offset": 0,
  "limit": 100,
  "data": [
    {
      "id": 1,
      "type": "PHONE_NUMBER",
      "value": "+919876543210",
      "normalized_value": "+919876543210",
      "source": "cli_search",
      "created_at": "2026-06-10T10:30:00"
    }
  ]
}
```

#### Get Entity Details
```http
GET /api/entities/{entity_id}
```

**Response:**
```json
{
  "id": 1,
  "type": "PHONE_NUMBER",
  "value": "+919876543210",
  "observations": [...]
}
```

---

### Towers

#### List Towers
```http
GET /api/towers?limit=100&offset=0
```

#### Towers in Bounding Box
```http
GET /api/towers/bbox?min_lat=18.5&max_lat=20.0&min_lon=73.0&max_lon=75.0
```

#### Towers by MCC
```http
GET /api/towers/mcc/404?limit=100
```

---

### Search

#### Search Phone Number
```http
POST /api/search
Content-Type: application/json

{
  "number": "+919876543210"
}
```

**Response:**
```json
{
  "number": "+919876543210",
  "location": "Maharashtra",
  "carrier": "Bharti Airtel",
  "country_code": 91
}
```

#### Search with Full Enrichment
```http
POST /api/search/enrich
Content-Type: application/json

{
  "number": "+919876543210"
}
```

**Response:**
```json
{
  "number": "+919876543210",
  "phone_intel": {...},
  "leak_check": {...},
  "observations": [...]
}
```

---

### Export

#### Export Data
```http
POST /api/export
Content-Type: application/json

{
  "format": "csv",
  "all_entities": true
}
```

**Response:**
```json
{
  "success": true,
  "format": "csv",
  "filepath": "exports/export_20260610_120000.csv"
}
```

Supported formats: `csv`, `json`, `kml`, `md`, `db`

---

### Graph

#### Get Correlation Graph
```http
GET /api/graph
```

**Response:**
```json
[
  {"data": {"id": "1", "type": "PHONE_NUMBER", "value": "+123"}},
  {"data": {"source": "1", "target": "2", "type": "CO_LOCATED"}}
]
```

#### Get Graph Neighbors
```http
GET /api/graph/neighbors/{entity_id}?depth=1
```

---

### Import

#### Import Data File
```http
POST /api/import
Content-Type: application/json

{
  "file_path": "/path/to/data.csv",
  "parser_type": "opencellid"
}
```

**Response:**
```json
{
  "success": true,
  "parser": "opencellid",
  "records_imported": 156
}
```

Available parsers: `opencellid`, `cellmapper`, `rtl_power`, `pcap`

---

### Reports

#### Generate Report
```http
GET /api/report/{identifier}
```

**Response:**
```json
{
  "success": true,
  "filepath": "reports/dossier_+919876543210_1718012400.md",
  "content": "# XGhostSignal Intelligence Dossier..."
}
```

---

### Health

#### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "features": [
    "entity_search",
    "tower_mapping",
    "graph_correlation",
    "export_csv",
    "export_json",
    "export_kml",
    "leak_check",
    "phone_intel"
  ]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid phone number format."
}
```

### 404 Not Found
```json
{
  "detail": "Entity 123 not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error message"
}
```

---

## Command Line Integration

The API can be accessed via `curl` or `httpie`:

```bash
# Get stats
curl http://localhost:8080/api/stats

# Search phone
curl -X POST http://localhost:8080/api/search \
  -H "Content-Type: application/json" \
  -d '{"number": "+919876543210"}'

# Export data
curl -X POST http://localhost:8080/api/export \
  -H "Content-Type: application/json" \
  -d '{"format": "csv", "all_entities": true}'
```

---

## Webhooks (Future)

Future versions will support webhooks for real-time alerts:

```json
{
  "event": "new_observation",
  "data": {
    "entity_id": 123,
    "type": "CELL_TOWER",
    "coordinates": [19.0760, 72.8777]
  },
  "timestamp": "2026-06-10T12:00:00Z"
}
```
