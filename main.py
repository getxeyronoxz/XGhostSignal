"""XGhostSignal - Local-first OSINT and Cellular Intelligence Workbench

Main entry point - serves both as CLI launcher and web server initializer.
"""
import sys

# Detect if we're being run as a script or imported
if len(sys.argv) > 1 and sys.argv[1] in ['serve', 'init', 'search', 'report', 'summarize', 'ingest', 'stream', '--help', '-g']:
    # CLI mode - import the CLI app
    from cli_app.main import app
    app()
else:
    # Web server mode - start the API server
    import uvicorn
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles

    from api.routes import router

    app = FastAPI(title="XGhostSignal UI Backend")

    # API routes
    app.include_router(router, prefix="/api")

    # Mount vanilla static frontend
    import os
    os.makedirs("static", exist_ok=True)
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

    def start_server(host="127.0.0.1", port=8080):
        print(f"[*] Starting XGhostSignal local enclave on http://{host}:{port}")
        uvicorn.run(app, host=host, port=port, log_level="info")

    if __name__ == "__main__":
        start_server()
