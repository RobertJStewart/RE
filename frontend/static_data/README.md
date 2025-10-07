# Static Data Files

This directory contains static JSON files copied from the ETL pipeline for GitHub Pages deployment.

## Files

- `connections.json` - Connection registry with full metadata
- `data_sources.json` - Data sources in frontend-compatible format
- `aggregations/` - Geographic aggregation data
- `statistics/` - Statistical calculations

## Generation

These files are automatically copied by running:
```bash
python backend/scripts/static_generator.py
```

## Last Updated

Generated on: 2025-10-06T22:40:09.874269

## Usage

These files are used by the static frontend mode to provide data without requiring a server.
