---
name: issue-to-plan
description: >-
  Turns a GitHub issue, bug report, or traceback into a verified implementation
  plan for a specific repository. Use whenever the user says any of: "turn this
  issue into a plan", "scope this bug", "what would it take to fix", "where do I
  start", "triage this", "why did this stop working", or otherwise points at an
  issue number, a bug report, or an error and wants it investigated and planned
  rather than immediately patched. Applies even when the request sounds routine
  and the next step seems obvious. The skill reproduces the failure first,
  locates the code that owns it, independently re-verifies every claim made in
  the issue thread including maintainers', and outputs a plan naming exact
  files, changes, and verification commands. Not for writing the final patch,
  reviewing an existing diff or PR, or ordinary end-user operation of the tool
  the issue happens to be about.
---

# Issue to implementation plan

Produce a **plan**, not a patch. The plan is only worth reading if every
load-bearing claim in it was confirmed by a command you ran.

## When not to use this

- The user wants the code written or the bug fixed now, not scoped.
- The user wants an existing diff or PR reviewed.
- The user just wants to *use* the tool (e.g. "download this video with
  yt-dlp"). A URL plus the project's name is not an issue report.

## Workflow

1. **Read the issue in full**, including every comment and any linked issue or
   PR. Extract: the exact input, the exact observed output, the version, and
   each factual claim anyone makes about the cause.
2. **Check for prior art** before planning anything.
   ```bash
   curl -s "https://api.github.com/search/issues?q=repo:<owner>/<repo>+is:pr+is:open+<keyword>"
   ```
   If an open PR already does the work, read it and plan only the delta, or say
   it is already handled and stop.
3. **Reproduce** on a clean checkout at current `master`, with the project's own
   verbose flag. If it does not reproduce, stop and go to step 7 with an
   information-gathering plan instead of a fix plan.
4. **Locate the owning code** by searching for the string in the error, then for
   the pattern that routes the input to a handler. See
   [reference-yt-dlp.md](reference-yt-dlp.md) when the target is yt-dlp.
5. **Verify each claim** from step 1 independently (see Decision points).
6. **Find the dispatch axis**, not just the failing line (see Decision points).
7. **Write the plan** using the template below.

## Decision points

These are the judgments the plan depends on. Getting them wrong produces a
confident plan for the wrong change.

### Trust nothing in the thread until a command confirms it

Issue bodies go stale and **maintainer comments are not exempt**. For every
claim that would change the shape of the plan ("the API is gone", "the IDs
changed", "these tests are invalid"), run the smallest command that tests it
and record the result. Promote a claim to a fact only after it passes.

This is the highest-value step. A thread claiming an upstream API is gone, when
it still returns HTTP 200, is the difference between planning a rewrite and
planning a six-line change.

### Classify before locating

| Class | Signal | What the plan must do |
|---|---|---|
| Upstream contract change | A sibling input still works; only the new shape fails | Adapt our code to their new contract |
| Our regression | It worked in an older version with the same input | Find the introducing commit, then decide revert vs forward-fix |
| Unsupported capability | It never worked; no code claims this input | Plan an addition, and say so, rather than calling it a fix |

Decide with evidence: run the *same* code path against a known-good sibling
input. If the sibling passes, the defect is specific to the new input.

### Find the dispatch axis, not just the failing line

When input shape A works and shape B does not, find the variable the code
branches on, then ask whether that variable is the *real* discriminator or a
proxy for it. Code frequently branches on something incidental (which URL path
was used) that merely correlated with the thing that actually matters (which ID
format was supplied). Widening the proxy makes the first error disappear and
the next one appear one layer deeper.

Concretely: if you are about to loosen a regex, an allowlist, or a type check so
an input is accepted, first confirm the code *behind* it handles that input.
Fetch the downstream endpoint, or call the downstream function, with the new
shape before you put the loosened pattern in the plan.

### Ask the user, or find out yourself

Find out yourself if a read-only command gets it in under two minutes. Only
escalate when the answer needs credentials, a paid account, a specific
region or IP, physical hardware, or a product-intent decision that is not
yours to make. "I could not determine X" is only acceptable after you name the
command you ran.

### State the blast radius

A plan that does not say which existing tests go red is incomplete. Before
writing it, run the target's existing tests for the code you intend to change
and list each failure as either "this change fixes it" or "this change must
also update it".

## What not to do

- Do not propose a fix for a failure you did not reproduce.
- Do not copy the issue's suggested fix into the plan without testing it.
- Do not plan a rewrite when a targeted change passes the same checks.
- Do not write the full implementation. A diff sketch of the changed lines is
  the maximum; the user asked for a plan.
- Do not list every file you read. Cite only files the plan touches.

## Output template

Keep it to one screen. Fill in every heading or delete it.

```markdown
## Classification
<upstream contract change | our regression | unsupported capability> - <one line of evidence>

## Root cause
<what actually breaks, in two sentences, with the command output that proves it>

## Claims checked
| Claim (source) | Verdict | Evidence |
|---|---|---|

## Changes
| File | Change |
|---|---|

## Verification
<exact commands, and the expected output of each>

## Open questions
<only what a command could not answer, and who can answer it>

## Out of scope
```

For a full worked example of a finished plan, see
[plan-template.md](plan-template.md).
