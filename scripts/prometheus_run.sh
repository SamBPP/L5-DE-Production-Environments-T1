#!/usr/bin/env bash
set -euo pipefail

PROM_VERSION="${PROM_VERSION:-2.54.1}"
BIN_DIR="${BIN_DIR:-.prometheus-bin}"
DATA_DIR="${DATA_DIR:-.prometheus-data}"
CFG="${CFG:-prometheus/prometheus.yml}"

mkdir -p "$BIN_DIR" "$DATA_DIR"

if [ ! -x "$BIN_DIR/prometheus" ]; then
  echo "Installing Prometheus $PROM_VERSION..."
  curl -L -o /tmp/prometheus.tar.gz \
    "https://github.com/prometheus/prometheus/releases/download/v${PROM_VERSION}/prometheus-${PROM_VERSION}.linux-amd64.tar.gz"
  tar -xzf /tmp/prometheus.tar.gz --strip-components=1 -C "$BIN_DIR"
  rm /tmp/prometheus.tar.gz
fi

exec "$BIN_DIR/prometheus" \
  --config.file="$CFG" \
  --storage.tsdb.path="$DATA_DIR" \
  --web.enable-lifecycle