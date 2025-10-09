# Topic 5: Monitoring

## Installing and running Prometheus

Here’s a clean, repeatable way to run Prometheus inside your GitHub Codespace and point it at your Airflow metrics. It wallks you through a "quick run" you can paste into a terminal, plus a slightly more polished setup that auto-starts whenever the Codespace opens.

---

### 1) Expose the Prometheus port in your devcontainer

Open `.devcontainer/devcontainer.json` and make sure 9090 is forwarded (add 8080 and 3000 if you’ll also use Airflow + Grafana):

```json
{
  "forwardPorts": [8080, 9090, 3000]
}
```

Rebuild/reopen in container if you changed this.

---

### 2) Create a Prometheus config that scrapes Airflow

If you’re using the Airflow Prometheus exporter, create `prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "airflow"
    metrics_path: /admin/metrics
    static_configs:
      - targets: ["localhost:8080"]
```

---

### 3) Quick way: download and run Prometheus in a terminal

In your Codespaces terminal at the repo root, run:

```bash
# pick a recent version
PROM_VERSION=2.54.1

# download + unpack
curl -L -o prometheus.tar.gz \
  "https://github.com/prometheus/prometheus/releases/download/v${PROM_VERSION}/prometheus-${PROM_VERSION}.linux-amd64.tar.gz"
mkdir -p .prometheus-bin
tar -xzf prometheus.tar.gz --strip-components=1 -C .prometheus-bin
rm prometheus.tar.gz

# create a local data dir
mkdir -p .prometheus-data

# run (foreground so you can see logs)
./.prometheus-bin/prometheus \
  --config.file=prometheus/prometheus.yml \
  --storage.tsdb.path=.prometheus-data \
  --web.enable-lifecycle
```

Keep that terminal open while you work. Codespaces will auto-forward port **9090**—open the forwarded link and check:

* **/targets** shows your Airflow target **UP**.
* **/graph** lets you query e.g. `process_start_time_seconds`.

If you change `prometheus.yml`, you can hot-reload without restarting:

```bash
curl -X POST http://localhost:9090/-/reload
```

> Tip: limit disk usage during dev with `--storage.tsdb.retention.time=2d` or `--storage.tsdb.retention.size=512MB`.

---

### 4) Make it feel “built-in”: add a small run script (optional)

Add `scripts/prometheus_run.sh`:

```bash
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
```

Make it executable and run it:

```bash
chmod +x scripts/prometheus_run.sh
scripts/prometheus_run.sh
```

### 5) Validate end-to-end

1. Start Airflow (`airflow standalone` is fine) and confirm you can hit the UI on port 8080.
2. Start Prometheus (steps above) and open the forwarded **9090** URL → **Status → Targets** should be green.
3. In Grafana (port **3000**), add a Prometheus data source pointing to `http://localhost:9090`. Import a dashboard (e.g., one tailored for the exporter) and you should see Airflow metrics populate within a minute.

---

### Common “why can’t I see anything?” fixes

* **Target down in /targets:** usually the Airflow exporter path or port is wrong. If you use the exporter, make sure `/admin/metrics` responds at `localhost:8080` inside the container (and that the webserver is actually running).
* **Nothing on Prometheus UI:** confirm port 9090 is forwarded and Prometheus is running; the foreground logs will tell you if the config path is wrong.
* **StatsD path:** if you went with StatsD, ensure `statsd_exporter` is running on **9102** and Airflow is emitting to **UDP 9125** (env vars set and scheduler restarted).

## Installing and running Grafana

Here’s a clean, Codespaces-friendly way to get **Grafana** running next to your Airflow/Prometheus stack. Here you'll see a no-root “tarball” method (fastest in Codespaces), plus a tiny run script and an optional auto-start.

---

# Quick run (no root): download tarball & run

1. **Forward the port** (once, in `.devcontainer/devcontainer.json`):

```json
{
  "forwardPorts": [8080, 9090, 3000]
}
```

Rebuild the devcontainer so port **3000** is forwarded by Codespaces.

2. **Download & run Grafana** in your Codespaces terminal:

```bash
# Pick a version (check releases for latest stable)
GRAFANA_VERSION=11.5.9

# Download & unpack to a workspace-local folder
curl -L -o grafana.tar.gz \
  "https://dl.grafana.com/oss/release/grafana-${GRAFANA_VERSION}.linux-amd64.tar.gz"
mkdir -p .grafana
tar -xzf grafana.tar.gz --strip-components=1 -C .grafana
rm grafana.tar.gz

# Start Grafana (foreground; keep this terminal open)
./.grafana/bin/grafana-server --homepath ./.grafana
```

Open the forwarded **3000** link in the Codespaces UI. (If you prefer, confirm the latest stable tag on the releases page.)

3. **Log in (first time)**
   Username: `admin` · Password: `admin` (you’ll be prompted to change it).

> Tip: The `--homepath` flag tells Grafana where its `conf/`, `public/`, and `data/` live when you run it from outside that folder. If you see a “could not find config defaults / set homepath” error, it means the server couldn’t locate its install dir—use `--homepath` or `cd` into the extracted directory and run `bin/grafana-server`.

---

# Optional quality-of-life: a tiny run script + auto-start

**`scripts/grafana_run.sh`**

```bash
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
```

```bash
chmod +x scripts/grafana_run.sh
scripts/grafana_run.sh
```

To auto-start each time the Codespace opens, add to `.devcontainer/devcontainer.json`:

```json
{
  "postStartCommand": "bash scripts/grafana_run.sh"
}
```

(And keep `"forwardPorts": [3000]` so the UI is reachable.) ([GitHub Docs][1])

---

# Hooking Grafana to Prometheus (1-minute provisioning)

If you already have Prometheus on **:9090**, you can provision a datasource so Grafana “just works”:

**`provisioning/datasources/prometheus.yml`**

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://localhost:9090
    access: proxy
    isDefault: true
```

Start Grafana with the provisioning folder visible (the tarball defaults to `./conf/provisioning` under `--homepath`). With the script above, place the file at:

```
.grafana/conf/provisioning/datasources/prometheus.yml
```

and restart. Grafana will load the Prometheus datasource automatically. (General provisioning and configuration behavior is documented in Grafana’s admin/config docs.) ([Grafana Labs][6])

---

## Quick checklist

* **Ports forwarded:** 3000 (Grafana), 9090 (Prometheus), 8080 (Airflow). ([GitHub Docs][1])
* **Start Grafana:** tarball = `bin/grafana-server --homepath .grafana`; apt = `/usr/sbin/grafana-server --homepath /usr/share/grafana`. ([Grafana Labs][5])
* **Login:** `admin` / `admin` → change when prompted. ([Grafana Labs][3])

If you want, tell me which path you picked (tarball vs apt), and I’ll hand you a tiny repo patch with the run script, provisioning file, and the devcontainer tweaks already wired in.

[1]: https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace?utm_source=chatgpt.com "Forwarding ports in your codespace"
[2]: https://github.com/grafana/grafana/releases?utm_source=chatgpt.com "Releases · grafana/grafana"
[3]: https://grafana.com/docs/grafana/latest/setup-grafana/sign-in-to-grafana/?utm_source=chatgpt.com "Sign in to Grafana | Grafana documentation"
[4]: https://grafana.com/docs/grafana/latest/administration/cli/?utm_source=chatgpt.com "Grafana server CLI | Grafana documentation"
[5]: https://grafana.com/docs/grafana/latest/setup-grafana/installation/debian/?utm_source=chatgpt.com "Install Grafana on Debian or Ubuntu"
[6]: https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/?utm_source=chatgpt.com "Configure Grafana | Grafana documentation"
