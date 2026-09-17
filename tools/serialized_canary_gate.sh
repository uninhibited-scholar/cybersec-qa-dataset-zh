#!/bin/zsh
set -euo pipefail

# Deliberately refuses to run unless the operator opts in. This gate keeps the
# production adapter and candidate adapter physically separate and never allows
# two 4B model workers to remain resident during evaluation.
if [[ "${RUN_SERIALIZED_CANARY:-}" != "1" ]]; then
  print -u2 "Set RUN_SERIALIZED_CANARY=1 to run the serialized candidate gate."
  exit 2
fi

SERVICE="gui/$(id -u)/com.uninhibited-scholar.cyber-agent-api"
PLIST="$HOME/Library/LaunchAgents/com.uninhibited-scholar.cyber-agent-api.plist"
CANDIDATE_PORT="18778"
BASE="/Users/jiehan/models/Qwen3-4B-mlx-4bit-phase3-wrapper"
ADAPTER="/Users/jiehan/models/phase87-clean-retrain-20260917"

restore() {
  kill "${CANDIDATE_PID:-}" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null || true
}
trap restore EXIT INT TERM

curl -fsS http://127.0.0.1:18765/health >/dev/null
launchctl bootout "$SERVICE"
CYBER_API_PORT="$CANDIDATE_PORT" CYBER_MODEL_PATH="$BASE" \
  CYBER_ADAPTER_PATH="$ADAPTER" \
  nohup /opt/homebrew/bin/python3.14 /Users/jiehan/cyber-agent/phase88_api.py \
  >/tmp/phase89-serialized-canary.log 2>&1 &
CANDIDATE_PID=$!
sleep 8
curl -fsS "http://127.0.0.1:${CANDIDATE_PORT}/health" >/dev/null
/opt/homebrew/bin/python3.14 /Users/jiehan/cyber-agent/phase89_blind.py

print "Serialized candidate evaluation finished; production will be restored by trap."
