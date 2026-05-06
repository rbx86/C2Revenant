#!/bin/bash

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BEACON_DIR="$PROJECT_ROOT/beacon-rs"
ASSETS_DIR="$PROJECT_ROOT/assets"

echo "[*] Building beacon for Windows (x86_64)..."
cd "$BEACON_DIR"
cargo build --release --target x86_64-pc-windows-gnu

echo "[*] Copying beacon.exe to assets/..."
mkdir -p "$ASSETS_DIR"
cp "$BEACON_DIR/target/x86_64-pc-windows-gnu/release/beacon.exe" "$ASSETS_DIR/beacon.exe"

echo "[+] Done! Beacon at assets/beacon.exe"