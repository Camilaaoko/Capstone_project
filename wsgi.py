"""
WSGI Application Entry Point
Exposes the Flask 'server' object for production WSGI servers (Gunicorn, Render, Heroku).
"""

import os
import sys
from pathlib import Path

# Ensure workspace root is in python path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Auto-initialize database on cold-start if analytics.db does not exist
db_file = ROOT_DIR / "analytics" / "analytics.db"
if not db_file.exists():
    print("[RENDER BOOT] analytics.db not found. Initializing pipeline...")
    try:
        from generate_data import DataGenerator
        from etl_pipeline import ETLPipeline
        
        # Fast generation if not present
        os.makedirs(ROOT_DIR / "output", exist_ok=True)
        os.makedirs(ROOT_DIR / "analytics", exist_ok=True)
        
        gen = DataGenerator(seed=42)
        gen.generate_all(output_dir=str(ROOT_DIR / "output"))
        
        etl = ETLPipeline(input_dir=str(ROOT_DIR / "output"), output_dir=str(ROOT_DIR / "analytics"))
        etl.run()
        print("[RENDER BOOT] Database initialized successfully.")
    except Exception as e:
        print(f"[RENDER BOOT ERROR] Failed to initialize database: {e}")

from dashboard.app import app, server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)

