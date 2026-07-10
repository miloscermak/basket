#!/bin/zsh
# Kompletní stahovací a parsovací pipeline. Bezpečně navazuje na přerušenou práci.
set -e
cd "$(dirname "$0")"
PY=../.venv/bin/python

echo "=== 1/5 detaily zápasů ==="
$PY download_details.py
echo "=== 2/5 parsování box scores ==="
$PY parse_details.py
echo "=== 3/5 profily hráčů ==="
$PY download_players.py
echo "=== 4/5 parsování profilů ==="
$PY parse_players.py
echo "=== 5/5 přegenerování overview ==="
$PY ../analysis/build_overview.py
$PY ../analysis/build_records.py
$PY ../analysis/build_careers.py
$PY ../analysis/build_pbp_insights.py
$PY ../analysis/build_shots.py
$PY ../analysis/build_names.py
$PY ../analysis/build_search.py
$PY ../analysis/bundle_data.py
echo "=== PIPELINE HOTOVA ==="
