#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="${EDUYJ_ROOT:-/Users/gimdonghyeon/Desktop/educationforyeongju-backend}"
LOG_DIR="${EDUYJ_LOG_DIR:-/tmp/eduyj-deploy-logs}"
CLOUDFLARED_BIN="${CLOUDFLARED_BIN:-/opt/homebrew/bin/cloudflared}"
CLOUDFLARED_TOKEN_FILE="${CLOUDFLARED_TOKEN_FILE:-$HOME/.cloudflared/summit1123.token}"
BACKEND_PORT="${EDUYJ_BACKEND_PORT:-4000}"
FRONTEND_PORT="${EDUYJ_FRONTEND_PORT:-3000}"
CHECK_INTERVAL_SEC="${EDUYJ_CHECK_INTERVAL_SEC:-30}"

mkdir -p "$LOG_DIR"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOG_DIR/supervisor.log"
}

screen_exists() {
  screen -ls | grep -q "[.]$1[[:space:]]"
}

network_ready() {
  curl -fsS --max-time 5 https://www.cloudflare.com/cdn-cgi/trace >/dev/null 2>&1
}

port_ready() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

start_backend() {
  if screen_exists "eduyj-backend" && port_ready "$BACKEND_PORT"; then
    return
  fi
  screen -S eduyj-backend -X quit >/dev/null 2>&1 || true
  log "starting backend on :$BACKEND_PORT"
  screen -S eduyj-backend -dm zsh -lc "
    cd '$ROOT_DIR/backend' || exit 1
    while true; do
      .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port '$BACKEND_PORT' --reload 2>&1 | tee -a '$LOG_DIR/backend.log'
      sleep 1
    done
  "
}

start_frontend() {
  if screen_exists "eduyj-frontend" && port_ready "$FRONTEND_PORT"; then
    return
  fi
  screen -S eduyj-frontend -X quit >/dev/null 2>&1 || true
  log "starting frontend on :$FRONTEND_PORT"
  screen -S eduyj-frontend -dm zsh -lc "
    cd '$ROOT_DIR/frontend' || exit 1
    while true; do
      npm run dev -- --hostname 0.0.0.0 --port '$FRONTEND_PORT' 2>&1 | tee -a '$LOG_DIR/frontend.log'
      sleep 1
    done
  "
}

start_tunnel() {
  if screen_exists "eduyj-tunnel" && pgrep -f "cloudflared.*summit1123.token" >/dev/null 2>&1; then
    return
  fi
  screen -S eduyj-tunnel -X quit >/dev/null 2>&1 || true
  log "starting cloudflare tunnel"
  screen -S eduyj-tunnel -dm zsh -lc "
    '$CLOUDFLARED_BIN' tunnel --no-autoupdate --loglevel info run --token-file '$CLOUDFLARED_TOKEN_FILE' 2>&1 | tee -a '$LOG_DIR/cloudflared-eduyj.log'
  "
}

log "EduYJ local demo supervisor started"

while true; do
  if network_ready; then
    start_backend
    start_frontend
    start_tunnel
  else
    log "network is not ready; waiting"
  fi
  sleep "$CHECK_INTERVAL_SEC"
done
