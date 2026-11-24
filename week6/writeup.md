# Assignment 6 — Agent Cost-Optimization

## Scope and reproducibility

Author: Xuanzhuo Liu. Experiments were conducted with AI assistance on November 22–23, 2026 (Pacific). Codex configured and evaluated the workflow and drafted this write-up from recorded results; Claude Code generated every service repair and `out/impact.json` through the official metering gateway. No repair or impact answer was supplied in the submission setup.

Starter release: upstream commit `6fa9ddab2bd1b60e6fc81f7485d8bb47eab666fa`. The application, incident and task remain byte-identical to that release. Before the first graded submission, assignment.md and tools/starter/score.py were updated to official commit f4f9d18834e1cd2f6d011c8931cf2ad50bcb0079. Its scorer change awards correct report figures even when F1 is zero; it does not change either final practice run (both had F1 = 1). The agent never received `tools/starter/`. Each practice invocation used a fresh temporary workspace and the official rate card, $2 cap, and default 600-second limit. Local dependencies were Claude Code 2.1.330, Node 24.22.1, Go 1.27.4, and Python 3. Runs used distinct gateway/service ports when overlapping. Local runtime paths are not in `run.sh`.

Command: `python3 tools/practice.py --keep`. For concurrent experiments only, `--port` and `SWITCHYARD_PORT_BASE` were varied to isolate services. Machine-readable summaries and gateway usage are in [evidence/](evidence/). Full local transcripts and generated patches remain in ignored `runs/`; they are excluded from the submission zip, so subsequent agents cannot read solution patches. Setup snapshots for the two rejected variants and the baseline are in `evidence/`.

## Part I: Baseline

The unmodified official baseline uses Sonnet with high effort and its default harness context.

| Run | Repair | Impact | Cost | Model requests | Time |
| --- | --- | --- | --- | --- | --- |
| Baseline | 1.0000 | 1.0000 | $1.527088 | 37 | 418.1 s |

| Model | Input | Output | Cache read | Cache write (1 hour) | Cost |
| --- | --- | --- | --- | --- | --- |
| claude-sonnet-5-5 | 76 | 52,735 | 3,761,977 | 155,847 | $1.527088 |

The gateway recorded no 5-minute cache writes. Its 1-hour write rate is $4/M tokens. Cache writes cost $0.623388 (40.8% of total), output $0.527350 (34.5%), cache reads $0.376198 (24.6%), and uncached input $0.000152. Cache-read tokens dominated volume, while cache writes dominated dollars. The first request wrote 21,362 cache tokens before the investigation grew. The transcript then shows broad reads of assignment/write-up material, historical repository guidance, deployment material, service implementations, and extensive generated reasoning/code. Re-reading a growing context was cheap per token but not free.

| Category | Passed |
| --- | --- |
| Incident | 9/9 |
| Regressions | 10/10 |
| Compatibility | 2/2 |

Impact precision and recall were both 1.00, and all six report figures were correct. There were **no observed baseline scoring failures**. The baseline identified process-local idempotency memory and used durable state plus upgrade-time handling. It explicitly noticed conflicts between old documentation and current contracts. Thus this experiment did not establish that stale instructions caused baseline failure; the optimization target was its unnecessary context and cost. Passing these starter tests also does not prove correctness for every contract edge case or the held-out incident.

## Part II: Experiments

All costs below use the official gateway's token accounting. A full pass means both repair and impact equal 1.00; aborted or incomplete runs count as failures. The baseline was run once, model-only Haiku once, compact Haiku once, compact Sonnet twice, and the final reviewed Sonnet setup twice: seven trials total.

| Change | Hypothesis | Full passes / attempted | Mean repair / impact | Mean cost | Kept? |
| --- | --- | --- | --- | --- | --- |
| Haiku only | Lower unit prices with all baseline settings unchanged | 0/1 | 1.0000 / 0.0000 | $0.248290 | No |
| Compact Haiku | Focused contracts-first context and bounded tools reduce wasted tokens | 0/1 | 0.4444 / 1.0000 | $0.030082 | No |
| Compact Sonnet | Restore model capability while retaining focused context | 1/2 | 0.7222 / 0.9667 | $0.556993 | No: inconsistent |
| Compact Sonnet + acceptance review | A second turn catches incomplete requirements and evidence parsing assumptions | 2/2 | 1.0000 / 1.0000 | $0.809451 | Yes |

**A change that did not work: model price alone.** Model-only Haiku used 80 requests and 127,862 output tokens, versus the baseline's 37 requests and 52,735 output tokens. The official runner stopped it at the 600-second limit. Its repair passed all 21 scenarios, but `out/impact.json` was absent, giving impact 0.00. This was an incomplete run, not a valid cheap solution. A subsequent attempted manual process stop found that the run had already exited and terminated nothing. This illustrates why throughput and finishing both deliverables matter alongside unit price.

**A second failure: compact Haiku.** It finished normally in 338.5 seconds for $0.030082 and produced an exact impact report, but passed only 4/9 incident scenarios. Its own final response admitted that it had not cancelled old queued repeats or leased work automatically. All regression and compatibility scenarios passed, and the three smoke checks passed. Forward-looking prevention alone did not satisfy the ticket's existing-state requirements.

**Why compact Sonnet was not enough.** The first run passed fully for $0.579096; the independent repeat cost $0.534889 but again passed only 4/9 incident scenarios. Impact was 0.9333: precision/recall were both 1.00 and five of six figures matched, but it counted 162 corrupted rows rather than the correct 97. The transcript explicitly acknowledged a gap for queued events whose keys had never reached the router. This is direct evidence of inconsistency; a single passing trial would have led to a premature decision.

**The change that recovered the failures.** The final setup adds a second Sonnet turn in the same metered session. It re-reads the ticket and contracts, checks every mandatory outcome, requires a regression beginning with old-release persisted state, and audits corruption detection against the documented formats rather than invented required fields. It asks the agent to repair gaps instead of presenting mandatory omissions as caveats. It contains no starter IDs, expected totals, precomputed report, service replacement code, or grader answers. In its first run, the transcript shows the review adding automated reconciliation for existing state and writing an upgrade regression. Results from both trials are below.

**What saved money.** The context controls retained Sonnet but replaced the large default system prompt with a concise engineering role, restricted tools to Bash/Read/Edit/Write/Glob/Grep, disabled unrelated skills/MCP servers, and pointed investigation toward the current contracts and deployed services. Compact Sonnet's first run reduced output to 21,314 tokens, cache reads to 999,605, and cache writes to 66,474, from baseline 52,735 / 3,761,977 / 155,847. Context controls were bundled, so their individual causal effects were not isolated. The added acceptance review costs more than stopping after the first turn; its purpose is completeness. The final mean cost is $0.809451, 47.0% below the measured baseline.

### Final setup

1. `run.sh` reads its task argument and works in the submission directory.
2. At runtime, it replaces historical `app/AGENTS.md` and `app/CLAUDE.md` guidance with short pointers to the task, contracts and workflow. The assignment permits this. No service code is injected.
3. It runs a headless Sonnet high-effort call using the compact system prompt, `workflow.md`, the actual task and six local tools. The agent diagnoses and implements the repair, writes its own parser, generates `out/impact.json`, and checks the work.
4. A second headless Sonnet high-effort call uses `--continue` to audit and repair the same session's work. The review is a general requirements/upgrade/evidence audit. Stream-JSON output preserves both turns for local inspection.

Both calls retain the grader-provided gateway environment. There are no external model calls, embedded credentials, alternate accounts, canned patches, or impact answers. The workflow requests bounded reads rather than dumping logs, stable-ID evidence joins rather than cross-host timestamp equality, integer money arithmetic, corrupted-row accounting, and tests beyond smoke scenarios. The agent must infer the actual diagnosis and report inclusion rules from the new ticket.

### Final setup on the starter incident

| Run | Repair | Impact | Cost | Model requests | Time |
| --- | --- | --- | --- | --- | --- |
| Reviewed Sonnet 1 | 1.0000 | 1.0000 | $0.718762 | 27 | 260.2 s |
| Reviewed Sonnet 2 | 1.0000 | 1.0000 | $0.900140 | 34 | 304.3 s |

Both runs used identical `run.sh` and `workflow.md`. They passed 2 of 2 full trials. Variation in cost reflects different tool calls, generated code and reasoning trajectories. No model requests were refused in these experiments. Two successful local trials do not establish a production failure probability. Practice isolates workspaces but still uses local installed tools/subscription rather than an entirely cold grading container; generated temporary scripts are neither shipped nor needed by the setup.

**Transfer to a new incident.** Authority ordering, focused navigation, durable-state and upgrade reasoning, compatibility checks, stable-ID joins, and documented corruption rules apply across Switchyard incidents. The verification addition was motivated by a specific failure, but it asks for completeness of the current ticket, not a fixed idempotency algorithm. Correct grouping, inclusion and repair still depend on the unseen task. The observed duplicate-event implementation and expected report figures are not embedded in prompts. Costs, completeness and timing may change on a different incident, and the local smoke/regression checks cannot prove full hidden-contract coverage.

## Part III: Graded submissions

**No graded run has been created.** On November 23 both Assignment 6 entries became visible. Uploading the prepared 265-file archive to Assignment 6 (Autograder), assignment 9065912, was rejected with: “The outline for this assignment has not been set up yet. Notify your instructor to fix this problem.” The dashboard still shows No Submission; no submission ID or graded result was returned. Evidence is in `evidence/gradescope-upload-blocked-2026-11-23.json`. This configuration issue must be resolved by course staff before the held-out run can proceed.

| Submission | Repair | Impact | Passed? | Cost | Status |
| --- | --- | --- | --- | --- | --- |
| Upload attempt, no graded submission created | Not measured | Not measured | Not measured | Not measured | Rejected: assignment outline not configured |

Starter-versus-held-out transfer cannot yet be measured. Practice numbers are not awarded grades. The published cost score saturates at $0.75 and reaches zero at $1.50, but the held-out run's own cost and correctness determine the score. When the course fixes the Autograder entry, upload the prepared zip, record the actual results here, push the revision, and update the Writeup submission to the new commit hash. The Writeup entry requests both a repository URL and the exact commit hash, so a later push alone does not update the version to be graded.

The confirmed due date is November 29, 2026, 11:59 PM Pacific; Gradescope also displays a late deadline of December 6. The normal deadline matches [the staff release announcement](https://edstem.org/us/courses/106077/discussion/8535869).
