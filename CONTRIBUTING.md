# Contributing to XGhostSignal

Thank you for your interest in contributing! This document provides guidelines for forkers, contributors, and maintainers.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Adding Features](#adding-features)

---

## Code of Conduct

- Be respectful and constructive
- Focus on what's best for the community and the tool
- Accept constructive criticism gracefully

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/XGhostSignal.git
   cd XGhostSignal
   ```
3. **Set up** the development environment (see below)
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## How to Contribute

### Reporting Bugs
- Check if the issue already exists
- Include steps to reproduce, expected behavior, and actual behavior
- Include your Python version and OS

### Suggesting Features
- Open an issue with the `enhancement` label
- Describe the use case and expected behavior

### Code Contributions
- Bug fixes, new features, documentation improvements, and tests are all welcome
- Keep PRs focused — one feature/fix per PR

## Development Setup

```bash
# Clone
git clone https://github.com/getxeyronoxz/XGhostSignal.git
cd XGhostSignal

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install with dev dependencies
pip install -e ".[dev]"

# Initialize database
xgs init

# Run tests
pytest tests/ -v
```

## Coding Standards

- **Python 3.9+** compatible
- Follow existing code style (no formatter enforced, but stay consistent)
- Use type hints where appropriate
- Keep functions focused and modular
- Document complex logic with brief comments

### Naming Conventions
- `snake_case` for functions and variables
- `PascalCase` for classes
- `UPPER_SAFE_CASE` for constants

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_core.py -v

# Run a specific test
pytest tests/test_core.py::test_config_constraints -v
```

Tests use in-memory SQLite (`sqlite:///:memory:`) — no app database is touched.

## Pull Request Process

1. Update documentation if your change affects usage
2. Add tests for new functionality
3. Ensure all tests pass: `pytest tests/ -v`
4. Update `CHANGELOG.md` under `[Unreleased]`
5. Submit PR with clear description of changes

## Project Structure

```
core/          Config + SQLAlchemy models
cli_app/       Typer CLI commands
api/           FastAPI REST endpoints
services/      Business logic (export, reports, LLM, graph)
parsers/       Unified Parser Engine (BaseParser ABC)
plugins/       Plugin system + default plugins
static/        Web frontend (vanilla HTML/CSS/JS)
tests/         Test suite
docs/          Documentation
```

## Adding Features

### Adding a Parser

Create a new file in `parsers/`:

```python
from parsers.base import BaseParser

class MyCustomParser(BaseParser):
    def parse_file(self, file_path: str) -> list:
        records = []
        # Parse file and create records
        records.append(self.create_unified_record(
            source="my_source",
            protocol="MY_PROTOCOL",
            mcc="404",
            cell_id="12345",
            latitude="28.6139",
            longitude="77.2090",
            confidence="high"
        ))
        return records
```

Then register it in `cli_app/main.py` and `api/routes.py`.

### Adding a Plugin

Create a file in `plugins/custom/`:

```python
PLUGIN_NAME = "my_plugin"
VERSION = "1.0.0"

def run(arg1: str, arg2: int = 10) -> dict:
    """Plugin entry point."""
    return {"status": "success", "result": f"Processed {arg1}"}
```

Plugins are auto-loaded by the registry.

### Adding a CLI Command

Add to `cli_app/main.py`:

```python
@app.command()
def my_command(arg: str):
    """Description of command."""
    console.print(f"Processing {arg}...")
```

### Adding an API Endpoint

Add to `api/routes.py`:

```python
@router.get("/my-endpoint")
def my_endpoint():
    """Endpoint description."""
    return {"status": "ok"}
```

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
