#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVER_DIR="$PROJECT_ROOT/server"
DB="$SERVER_DIR/c2.db"

echo "[*] Stopping any running server..."
pkill -f "python app.py" 2>/dev/null || true

echo "[*] Deleting database..."
rm -f "$DB"

echo "[*] Starting fresh server..."
cd "$SERVER_DIR"
source venv/bin/activate
python app.py