#!/usr/bin/env bash
set -euo pipefail

for session in eduyj-backend eduyj-frontend eduyj-tunnel; do
  screen -S "$session" -X quit >/dev/null 2>&1 || true
done

pkill -f "eduyj-local-demo-supervisor.sh" >/dev/null 2>&1 || true

echo "EduYJ local demo sessions stopped."
