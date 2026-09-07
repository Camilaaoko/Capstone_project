#!/usr/bin/env bash
# Render Build Script
set -e

echo "=== [1/3] Upgrading pip and installing production dependencies ==="
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "=== [2/3] Checking SQLite database existence ==="
if [ ! -f "analytics/analytics.db" ]; then
    echo "[INFO] analytics.db not detected. Running data generator and ETL pipeline..."
    python generate_data.py --seed 42
    python etl_pipeline.py
else
    echo "[INFO] analytics.db already present."
fi

echo "=== [3/3] Build completed successfully ==="

