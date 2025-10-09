#!/usr/bin/env bash
set -euo pipefail

# --- resolve paths ---
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"           # parent of scripts/
BIN_DIR="${BIN_DIR:-"$REPO_ROOT/.grafana"}"    # override with BIN_DIR if you want
GRAFANA_VERSION="${GRAFANA_VERSION:-11.5.9}"

mkdir -p "$BIN_DIR"

# --- install (once) into ../.grafana ---
if [ ! -x "$BIN_DIR/bin/grafana-server" ]; then
  echo "Installing Grafana ${GRAFANA_VERSION} into: $BIN_DIR"
  TMPDIR="$(mktemp -d)"
  curl -fsSL -o "$TMPDIR/grafana.tar.gz" \
    "https://dl.grafana.com/oss/release/grafana-${GRAFANA_VERSION}.linux-amd64.tar.gz"
  tar -xzf "$TMPDIR/grafana.tar.gz" --strip-components=1 -C "$BIN_DIR"
  rm -rf "$TMPDIR"
fi

# Optional: make sure provisioning (datasources/dashboards) is picked up from .grafana/conf/provisioning
export GF_PATHS_PROVISIONING="${BIN_DIR}/conf/provisioning"

echo "Starting Grafana from $BIN_DIR (UI → port 3000)"
exec "$BIN_DIR/bin/grafana-server" --homepath "$BIN_DIR"
