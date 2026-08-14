#!/usr/bin/env bash
# health-watchdog.sh — conservative restart watchdog for kvm-service container.
#
# Invoked by kvm-healthcheck.service on a 5-minute timer.
# Restarts the container only after MAX_CONSECUTIVE consecutive unhealthy checks
# AND only if RESTART_COOLDOWN seconds have passed since the last restart.
#
# Why conservative?  The two most likely hardware faults (latched-up SV04 RS-232
# controller, unplugged adapter) cannot be fixed by restarting the container.
# Aggressive restarts would churn forever and achieve nothing.  Several minutes
# of confirmed unhealthy state, plus a per-hour rate cap, keeps the watchdog
# useful while preventing restart storms.

set -euo pipefail

CONTAINER=kvm-service

# Number of consecutive unhealthy polls required before acting (5 min timer =>
# the container must be unhealthy for at least ~15 minutes before a restart).
MAX_CONSECUTIVE=3

# Minimum seconds between restarts.  One restart per hour prevents looping.
RESTART_COOLDOWN=3600

# systemd StateDirectory= creates this directory and sets ownership to the
# service user before the script runs.
STATE_DIR=/var/lib/kvm-healthcheck
CONSECUTIVE_FILE="$STATE_DIR/consecutive_unhealthy"
LAST_RESTART_FILE="$STATE_DIR/last_restart_epoch"

mkdir -p "$STATE_DIR"

# --- Read Docker health status -------------------------------------------
# Suppress docker errors (container not found, daemon down, etc.) and treat
# them as "unknown" so the script does not crash or restart blindly.
HEALTH=$(docker inspect --format '{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || true)

# docker inspect outputs "<no value>" when the container exists but has no
# HEALTHCHECK defined.  Normalise that to an empty-ish string for the case
# statement below.

case "$HEALTH" in
  healthy)
    echo "[watchdog] $CONTAINER is healthy. Resetting consecutive counter."
    echo 0 > "$CONSECUTIVE_FILE"
    exit 0
    ;;
  unhealthy)
    # fall through to restart logic below
    ;;
  *)
    # Covers: "" (container missing / inspect failed), "starting",
    # "<no value>" (no healthcheck configured).
    # In all of these cases do nothing — we have no confirmed health signal.
    echo "[watchdog] $CONTAINER health status: '${HEALTH:-<empty>}' — no action taken."
    echo 0 > "$CONSECUTIVE_FILE"
    exit 0
    ;;
esac

# --- Container is unhealthy — increment consecutive counter ---------------
CONSECUTIVE=$(cat "$CONSECUTIVE_FILE" 2>/dev/null || echo 0)
CONSECUTIVE=$(( CONSECUTIVE + 1 ))
echo "$CONSECUTIVE" > "$CONSECUTIVE_FILE"
echo "[watchdog] $CONTAINER unhealthy (consecutive check: $CONSECUTIVE / $MAX_CONSECUTIVE)."

if (( CONSECUTIVE < MAX_CONSECUTIVE )); then
  echo "[watchdog] Below threshold — waiting for more checks before acting."
  exit 0
fi

# --- Threshold reached — enforce rate limit --------------------------------
NOW=$(date +%s)
LAST=$(cat "$LAST_RESTART_FILE" 2>/dev/null || echo 0)
ELAPSED=$(( NOW - LAST ))

if (( ELAPSED < RESTART_COOLDOWN )); then
  WAIT=$(( RESTART_COOLDOWN - ELAPSED ))
  echo "[watchdog] Rate limited: last restart was ${ELAPSED}s ago;" \
       "cooldown is ${RESTART_COOLDOWN}s. Next restart allowed in ${WAIT}s. Skipping."
  exit 0
fi

# --- Restart --------------------------------------------------------------
echo "[watchdog] Restarting $CONTAINER after $CONSECUTIVE consecutive unhealthy checks" \
     "(last restart ${ELAPSED}s ago)."
docker restart "$CONTAINER"
echo "$NOW" > "$LAST_RESTART_FILE"
echo 0 > "$CONSECUTIVE_FILE"
echo "[watchdog] Restart complete."
