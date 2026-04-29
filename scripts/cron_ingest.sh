#!/bin/bash
# PollAgg daily ingestion wrapper — runs run_ingestion.py inside backend container,
# captures failures to alerts.log, posts to Slack/ntfy webhook if configured.
set -uo pipefail

PROJECT_DIR="/home/ubuntu/pollagg"
LOG="$PROJECT_DIR/logs/ingest.log"
ALERT="$PROJECT_DIR/logs/alerts.log"
LOCK="/tmp/pollagg-ingest.lock"
TS=$(date "+%Y-%m-%d %H:%M:%S %Z")

# webhook env (sourced from optional file)
if [[ -f "$PROJECT_DIR/.cron.env" ]]; then
  set -a; source "$PROJECT_DIR/.cron.env"; set +a
fi

# Single-instance guard
exec 9>"$LOCK"
if ! flock -n 9; then
  echo "[$TS] another ingestion already running — skip" >> "$LOG"
  exit 0
fi

mkdir -p "$PROJECT_DIR/logs"
echo "════════════ $TS START ════════════" >> "$LOG"

cd "$PROJECT_DIR" || { echo "[$TS] cd failed" >> "$ALERT"; exit 2; }

# Use timeout so a stuck scrape (eg network hang) cant block forever
if /usr/bin/timeout 600 /usr/bin/docker compose exec -T backend \
     python pipeline/run_ingestion.py >> "$LOG" 2>&1; then
  echo "════════════ $TS OK ════════════" >> "$LOG"
  exit 0
fi

EC=$?
MSG="[PollAgg cron FAIL] exit=$EC at $TS — see $LOG"
echo "════════════ $TS FAIL exit=$EC ════════════" >> "$LOG"
echo "$MSG" >> "$ALERT"

# Best-effort notifications (silent if not configured)
if [[ -n "${SLACK_WEBHOOK:-}" ]]; then
  curl -fsS -X POST -H "Content-Type: application/json" \
       --data "{\"text\":\"$MSG\"}" "$SLACK_WEBHOOK" >/dev/null 2>&1 || true
fi
if [[ -n "${NTFY_TOPIC:-}" ]]; then
  curl -fsS -d "$MSG" "https://ntfy.sh/$NTFY_TOPIC" >/dev/null 2>&1 || true
fi

exit "$EC"
