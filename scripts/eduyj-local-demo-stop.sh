#!/usr/bin/env bash
set -euo pipefail

for session in eduyj-backend eduyj-frontend eduyj-tunnel; do
  screen -S "$session" -X quit >/dev/null 2>&1 || true
done

pkill -f "eduyj-local-demo-supervisor.sh" >/dev/null 2>&1 || true
pkill -f "cloudflared tunnel --no-autoupdate --loglevel info run --token-file .*summit1123[.]token" >/dev/null 2>&1 || true

echo "EduYJ local demo sessions stopped."
