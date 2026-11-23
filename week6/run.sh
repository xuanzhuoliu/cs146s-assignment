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

# A second turn audits mandatory outcomes using the same metered session.
# This is a general acceptance review, with no starter answers or fixed patches.
claude -p "Perform an acceptance review of your completed work before stopping. Re-read the actual task and authoritative contracts. Enumerate every mandatory outcome and check that the code achieves it, including existing durable state created by the old release, work already queued or in flight, repeated upgrades, and compatibility. A fix only applied to future requests does not resolve an incident affecting existing state. If a service lacks information, trace where that information is durably stored and implement a general automated reconciliation; do not leave a mandatory requirement as a caveat. Write and run a regression that starts with old-release state, applies the new release and checks the required outcome; new-state-only unit tests are insufficient. Independently audit your evidence parser: corruption must match the formats and explicit corruption rules in contracts/evidence.md, not extra assumed required fields. Semantically unfamiliar or incomplete-but-valid records are not automatically corrupted. Exclude a genuinely corrupted row entirely and count each occurrence once; deduplicate valid shipped copies for event accounting. Validate each figure and the requested grouping against your parsed evidence, repair code or report errors you find, and rerun the relevant checks. Keep scripts and scratch files within this workspace. Finish the mandatory repair and out/impact.json; report what you actually verified briefly." \
  --continue \
  --model claude-sonnet-5-5 --effort high \
  --tools 'Bash,Read,Edit,Write,Glob,Grep' \
  --setting-sources project \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --disable-slash-commands \
  --permission-mode bypassPermissions \
  --output-format stream-json --verbose
