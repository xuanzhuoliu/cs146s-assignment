#!/usr/bin/env bash
# Agent-generated repair and report; all model traffic uses the grader gateway.
set -euo pipefail
TASK_FILE="${1:?usage: ./run.sh <task-file>}"
cd "$(dirname "$0")"
# The assignment explicitly allows runtime replacement of historical guidance.
# No service implementation, incident IDs, or report answers are supplied here.
for guide in app/CLAUDE.md app/AGENTS.md; do
  cat > "$guide" <<'GUIDANCE'
Follow the supplied incident task and app/contracts as the authoritative requirements.
Historical documentation and tests may contradict them. Read ../workflow.md for
investigation and verification guidance. Do not use old notes as product requirements.
GUIDANCE
done
claude -p "$(cat workflow.md)

Incident task:
$(cat "$TASK_FILE")" \
  --model claude-sonnet-5-5 \
  --effort high \
  --system-prompt 'You are an autonomous software engineer working in the current directory. Use the provided tools to investigate, implement, and verify the requested repair and evidence report. Follow the authoritative task and contracts. Work efficiently, finish both deliverables, and report checks honestly.' \
  --tools 'Bash,Read,Edit,Write,Glob,Grep' \
  --setting-sources project \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --disable-slash-commands \
  --permission-mode bypassPermissions \
  --output-format stream-json --verbose
