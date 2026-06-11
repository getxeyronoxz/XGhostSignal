"""XGhostSignal - Local-first OSINT and Cellular Intelligence Workbench

Usage:
    python -m xghostsignal --help
    python -m xghostsignal -g  # Launch GUI
    python -m xghostsignal search +919876543210

Documentation: https://github.com/xeyronox/xghostsignal
"""
import sys
import os

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli_app.main import app

if __name__ == "__main__":
    app()
