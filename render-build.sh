#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "=== [1/4] Installing dependencies ==="
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "=== [2/4] Generating reduced-scale synthetic healthcare dataset for free tier ==="
# Reduced flags for 512 MB RAM environment:
# Defaults: --facilities 235, --commodities 45, --months 24
# Reduced:  --facilities 100, --commodities 15, --months 3
python generate_data.py --facilities 100 --commodities 15 --months 3 --output-dir output --no-sqlite

echo "=== [3/4] Running ETL pipeline to generate analytics/analytics.db ==="
python etl_pipeline.py --input-dir output --output-dir analytics

echo "=== [4/4] Removing raw intermediate CSVs to conserve disk space ==="
rm -rf output
rm -f analytics/*.csv

echo "=== Build completed successfully ==="
