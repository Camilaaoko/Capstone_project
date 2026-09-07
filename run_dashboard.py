#!/usr/bin/env python3
"""Launcher script for the KEMSA Healthcare Supply Chain Intelligence Dashboard."""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.data_service import DB_PATH
from dashboard.app import app

# Expose WSGI server for Gunicorn / Render deployments
server = app.server


def main():
    parser = argparse.ArgumentParser(description="Run KEMSA Healthcare Supply Chain Intelligence Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host IP to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8050, help="Port to run the dashboard on (default: 8050)")
    parser.add_argument("--debug", action="store_true", default=False, help="Enable debug mode")
    args = parser.parse_args()

    # Pre-flight check
    if not DB_PATH.exists():
        print("=" * 70)
        print("❌ ERROR: Analytics Database not found!")
        print(f"   Missing expected database at: {DB_PATH.resolve()}")
        print("   Please run the ETL pipeline first:")
        print("      python etl_pipeline.py")
        print("=" * 70)
        sys.exit(1)

    print("=" * 70)
    print("🚀 Starting KEMSA Healthcare Supply Chain Intelligence Dashboard...")
    print(f"📍 Database: {DB_PATH.resolve()}")
    print(f"🌐 Dashboard URL: http://{args.host}:{args.port}/")
    print("=" * 70)

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()

