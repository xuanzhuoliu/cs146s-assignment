# Week 5 Write-up: Agent-Readiness Reports for Day.js, yt-dlp, and Redis

All three Factory readiness reports finished and were stored. Every number below comes from those reports' per-criterion scores. The evidence files are linked in [Raw output](#i7-raw-output) and at the end of this document. Preparation notes are in [`docs/REPO_NOTES.md`](docs/REPO_NOTES.md), and the run procedure is in [`docs/READINESS_RUNBOOK.md`](docs/READINESS_RUNBOOK.md).

## Repositories and run setup

| Repo | Language | Size (tracked blobs / bytes) | GitHub created | Owner type |
|---|---|---|---|---|
| [iamkun/dayjs](https://github.com/iamkun/dayjs) @ `436bde0b` (`dev`) | JavaScript, plus TS declarations | 380 / 2,490,486 | 2018-04-10 | User |
| [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) @ `b3b18f8f` (`master`) | Python ≥3.11 | 1,235 / 12,280,453 | 2020-10-26 | Organization |
| [redis/redis](https://github.com/redis/redis) @ `8e2ba8c4` (`unstable`) | C core, Tcl tests | 1,957 / 24,921,894 | 2009-03-21 | Organization |

Size counts every blob returned by `git ls-tree HEAD`, so it includes vendored and generated files and is not a SLOC count. Creation dates are GitHub repository creation dates, and a project's lineage can be older. Sources: [`repository-snapshots.json`](evidence/repository-snapshots.json) and [`github-repository-metadata.json`](evidence/github-repository-metadata.json).

| Repo | Droid CLI | Model | Session ID | Report ID | Stored (UTC) |
|---|---|---|---|---|---|
| dayjs | 1.2.0 | GPT-6.1 Sol (High) | `a1af5d1a-64fa-412a-8447-0827f44b0522` | `6309d0e4-f28b-4f1b-867d-c918f13f45a4` | 2026-11-09 01:34:49 |
| yt-dlp | 1.2.0 | GPT-6.1 Sol (High) | `24f0d7f4-6045-4369-bc6c-244c70ab2840` | `85a98749-5843-4b3f-9403-cb374fd2978d` | 2026-11-09 01:35:27 |
| redis | 1.2.0 | GPT-6.1 Sol (High) | `fa33509e-129d-4a25-bccc-0998807d8759` | `454d62e7-5c6f-479b-a3eb-5dbc770a13b9` | 2026-11-09 01:36:20 |

- **Timing.** All three runs happened on the evening of 2026-11-08, America/Chicago time, which was 2026-11-09 in UTC. Source: [`run-metadata.json`](evidence/run-metadata.json).
- **Version.** In its Day.js follow-up message, the CLI says "the CLI version was not recorded." That statement is about the CLI's own output only. We recorded the startup version, v1.2.0, separately in `run-metadata.json`. The raw transcript was left unedited.
- **Clean worktrees.** None of the three worktrees changed. Each stored report has `hasLocalChanges: false` and `hasNonRemoteCommits: false`, and independent post-run `git status --porcelain` checks were empty for all three ([post-run checks](evidence/post-run-checks.json)).
- **Audit environment.** Node/npm, `pytest`, `gh`/`glab`, and the devcontainer CLI were not installed, and Redis had not been built. We did not install any dependencies. Part II explains why these gaps matter.

---

## Part I: Report Results

### I.1 Maturity level and what blocks the next level

| Repo | Reported level | Passed / evaluated (skipped) | Score | Next level needs | Additional passes |
|---|---|---|---|---|---|
| Day.js | **Level 2** | 20 / 59 (25) | 33.90% (the web export rounds to 34%) | >40%: 24/59 = 40.68% | **+4** |
| yt-dlp | **Level 3** | 29 / 62 (22) | 46.77% | >60%: 38/62 = 61.29% | **+9** |
| Redis | **Level 3** | 32 / 64 (20) | 50.00% | >60%: 39/64 = 60.94% | **+7** |

**How these levels were computed.** In its Day.js follow-up ([`dayjs-cli-messages.txt`](evidence/raw/dayjs-cli-messages.txt)), the CLI describes the scoring it actually used: `score = mean(numerator/denominator)` over the criteria that were not skipped. Every criterion has a denominator of 1. The level boundaries are:

- Level 1: ≤20%
- Level 2: >20% to 40%
- Level 3: >40% to 60%
- Level 4: >60% to 80%
- Level 5: >80%

All three reported levels match this rule. The "next level" column assumes the same denominators, meaning no criterion moves between skipped and evaluated.

**No single criterion blocks the next level.** Under the rule above, each repo's score is just the share of evaluated criteria that passed. Any failed criterion that turned into a pass would count the same, so all 39, 33, and 32 failures are interchangeable candidates. The sets below are possible paths built only from criteria that already failed. They are not predictions that these criteria would pass on a rerun.

- **Day.js (+4):** `build_cmd_doc`, `single_command_setup`, `env_template`, `interactive_qa_exists`. Another path is `agents_md`, `agents_md_validation`, `pr_templates`, `codeowners`.
- **yt-dlp (+9):** `unit_tests_runnable`, `gitignore_comprehensive`, `pr_templates`, `codeowners`, `issue_labeling_system`, `dependency_update_automation`, `test_coverage_thresholds`, `type_check`, `large_file_detection`.
- **Redis (+7):** `unit_tests_runnable`, `interactive_qa_runnable`, `formatter`, `pre_commit_hooks`, `gitignore_comprehensive`, `pr_templates`, `codeowners`.

**The documentation describes a different rule.** The course-linked [Factory article](https://factory.ai/news/agent-readiness) describes gated progression: a repo must pass 80% of one level's criteria before it moves up. The [current Factory overview](https://docs.factory.com/agent-readiness/overview) also describes 80% previous-level gates. The stored reports do not tag any criterion with a level, so we cannot say which criteria would gate which level under that scheme, and we do not invent such a mapping. We report the levels Factory actually produced, and we treat the mismatch between implementation and documentation as a finding (see Part II).

### I.2 Native Factory category scores (nine categories)

The official Factory web export ([`dayjs-factory-export.md`](evidence/raw/dayjs-factory-export.md), unmodified) groups all 84 criteria into **nine** native categories. The CLI's narrative output used **seven** ad-hoc headings and put some criteria under the wrong one. Examples:

- Day.js: `log_scrubbing` appears under Debugging & Observability, and the Task Discovery items appear under Documentation.
- yt-dlp: `unused_dependencies_detection` appears under Style & Validation.
- Redis: `gitignore_comprehensive` appears under Dev Environment.

The tables in this write-up therefore use [`comparison.json`](evidence/comparison.json) (`factory_category`). That file applies the criterion-to-category mapping from the official export to each report's 84 per-criterion scores. All three reports contain the same 84 criterion keys. All three official web exports were downloaded and checked against the submitted criterion objects; they use the same category mapping. The nine-category table below matches those exports (with exact fractions rather than rounded display percentages).

Each cell reads **passed / evaluated (skipped)** followed by the pass rate.

| Factory category | Day.js | yt-dlp | Redis |
|---|---|---|---|
| Style & Validation | 5/12 (1), 41.7% | 5/12 (1), 41.7% | 4/11 (2), 36.4% |
| Build System | 4/10 (9), 40.0% | 5/9 (10), 55.6% | 5/10 (9), 50.0% |
| Testing | 5/8 (2), 62.5% | 7/10 (0), 70.0% | 7/10 (0), 70.0% |
| Documentation | 3/7 (1), 42.9% | 4/7 (1), 57.1% | 4/7 (1), 57.1% |
| Development Environment | 0/2 (3), 0.0% | 1/2 (3), 50.0% | 1/2 (3), 50.0% |
| Debugging & Observability | 1/9 (2), 11.1% | 1/9 (2), 11.1% | 4/10 (1), 40.0% |
| Security | 1/6 (6), 16.7% | 5/8 (4), 62.5% | 6/9 (3), 66.7% |
| Task Discovery | 1/3 (1), 33.3% | 1/3 (1), 33.3% | 1/3 (1), 33.3% |
| Product & Experimentation | 0/2 (0), 0.0% | 0/2 (0), 0.0% | 0/2 (0), 0.0% |
| **Total** | **20/59 (25)** | **29/62 (22)** | **32/64 (20)** |

### I.3 Eight-pillar comparison (analyst regrouping)

> **Disclaimer.** The assignment asks for eight pillars, including Code Quality. Factory did not produce eight pillar scores. This table is **our own regrouping** of Factory's unmodified pass/fail/skip results, built with the explicit crosswalk in [`criterion-mapping.json`](evidence/criterion-mapping.json) (`assignment_pillar`). No result was changed, and each criterion appears exactly once.
>
> The crosswalk makes three changes to Factory's nine categories:
> 1. **Code Quality** collects eight criteria. Seven come from Style & Validation: `cyclomatic_complexity`, `large_file_detection`, `duplicate_code_detection`, `code_modularization`, `tech_debt_tracking`, `dead_code_detection`, and `n_plus_one_detection`. One comes from Debugging & Observability: `code_quality_metrics`.
> 2. **Task Discovery** (four criteria) merges into Security & Governance.
> 3. **Product & Experimentation** (two criteria) merges into Observability.

Each repo cell reads **passed / evaluated (skipped)**. Failures equal evaluated minus passed.

| Pillar (regrouped) | Day.js | yt-dlp | Redis | Pooled failures / evaluated |
|---|---|---|---|---|
| Style & Validation | 4/6 (0) | 4/6 (0) | 2/5 (1) | 7/17 (41%) |
| Build System | 4/10 (9) | 5/9 (10) | 5/10 (9) | 15/29 (52%) |
| Testing | 5/8 (2) | 7/10 (0) | 7/10 (0) | 9/28 (32%) |
| Documentation | 3/7 (1) | 4/7 (1) | 4/7 (1) | 10/21 (48%) |
| Dev Environment | 0/2 (3) | 1/2 (3) | 1/2 (3) | 4/6 (67%) |
| Code Quality | 2/7 (1) | 1/6 (2) | 3/7 (1) | 14/20 (70%) |
| Observability | 0/10 (2) | 1/11 (1) | 3/11 (1) | 28/32 (88%) |
| Security & Governance | 2/9 (7) | 6/11 (5) | 7/12 (4) | 17/32 (53%) |
| **Total** | **20/59 (25)** | **29/62 (22)** | **32/64 (20)** | **104/185** |

### I.4 Failed criteria by pillar (accounts for 39, 33, and 32)

**24 criteria failed in all three repos.** To get a repo's full list of failures for a pillar, combine the "All three" column with that repo's additional column. Additional failures are not necessarily unique: some are shared by two repos.

| Pillar | All three repos (24) | Day.js additional (+15) | yt-dlp additional (+9) | Redis additional (+8) |
|---|---|---|---|---|
| Style & Validation | none | `type_check`, `strict_typing` | `type_check`, `strict_typing` | `formatter`, `pre_commit_hooks`, `naming_consistency` |
| Build System | `vcs_cli_tools`, `agentic_development`, `feature_flag_infrastructure`, `unused_dependencies_detection` | `build_cmd_doc`, `single_command_setup` | none | `version_drift_detection` |
| Testing | none | `test_performance_tracking`, `interactive_qa_exists`, `interactive_qa_runnable` | `unit_tests_runnable`, `test_performance_tracking`, `test_coverage_thresholds` | `unit_tests_runnable`, `test_coverage_thresholds`, `interactive_qa_runnable` |
| Documentation | `agents_md`, `skills`, `agents_md_validation` | `service_flow_documented` | none | none |
| Dev Environment | `devcontainer` | `env_template` | none | none |
| Code Quality | `tech_debt_tracking`, `cyclomatic_complexity`, `duplicate_code_detection`, `code_modularization` | `large_file_detection` | `large_file_detection` | none |
| Observability | `runbooks_documented`, `structured_logging`, `distributed_tracing`, `error_tracking_contextualized`, `alerting_configured`, `deployment_observability`, `product_analytics_instrumentation`, `error_to_insight_pipeline` | `metrics_collection`, `profiling_instrumentation` | `metrics_collection`, `profiling_instrumentation` | none |
| Security & Governance | `codeowners`, `gitignore_comprehensive`, `issue_labeling_system`, `pr_templates` | `dependency_update_automation`, `min_release_age`, `log_scrubbing` | `dependency_update_automation` | `min_release_age` |
| **Total failed** | 24 | 24 + 15 = **39** | 24 + 9 = **33** | 24 + 8 = **32** |

### I.5 Skipped criteria: inapplicable vs. missing environment or access

A `null` score means skipped, and skipped criteria are left out of the denominator. We sorted each skip into one of two groups based on the report's stated rationale. This sorting is our classification, not Factory's.

| Repo | Inapplicable or prerequisite not met | Missing tool or access in the audit environment |
|---|---|---|
| Day.js (25) | 14: `progressive_rollout`, `rollback_automation`, `monorepo_tooling`, `version_drift_detection`, `dead_feature_flag_detection`, `local_services_setup`, `database_schema`, `n_plus_one_detection`, `api_schema_docs`, `health_checks`, `circuit_breakers`, `dast_scanning`, `pii_handling`, `privacy_compliance` | 11: seven that need `gh`/`glab`*, plus `flaky_test_detection` (needs `gh`), `automated_security_review` (needs `gh`), `unit_tests_runnable` (no Node/npm), `devcontainer_runnable` (no devcontainer CLI) |
| yt-dlp (22) | 13: `progressive_rollout`, `rollback_automation`, `monorepo_tooling`, `heavy_dependency_detection`, `version_drift_detection`, `dead_feature_flag_detection`, `local_services_setup`, `database_schema`, `n_plus_one_detection`, `api_schema_docs`, `health_checks`, `privacy_compliance`, `dast_scanning` | 9: the seven `gh`-dependent*, plus `code_quality_metrics` (remote check unavailable), `devcontainer_runnable` |
| Redis (20) | 12: `strict_typing`, `n_plus_one_detection`, `progressive_rollout`, `rollback_automation`, `monorepo_tooling`, `heavy_dependency_detection`, `dead_feature_flag_detection`, `api_schema_docs`, `local_services_setup`, `database_schema`, `circuit_breakers`, `dast_scanning` | 8: the seven `gh`-dependent*, plus `devcontainer_runnable` |

\* The seven criteria that need `gh`/`glab` in every repo: `automated_pr_review`, `fast_ci_feedback`, `build_performance_tracking`, `deployment_frequency`, `branch_protection`, `secret_scanning`, `backlog_health`.

### I.6 The report's own top remediation suggestions

These are quoted directly from each report's `# Action Items` section.

| Repo | #1 | #2 | #3 |
|---|---|---|---|
| Day.js | "Add root `AGENTS.md` with a supported Node version, checkout setup, build/test commands, environment requirements, and an executable library smoke check." | "Configure strict declaration/type checking in CI." | "Add Renovate with a minimum release age, and update `.gitignore` to exclude `.env` secrets while retaining templates." |
| yt-dlp | "Install declared test dependencies and repeat collection; add retained timing/coverage reports and coverage gates." | "Add strict Python type checking, complexity thresholds, and architectural-boundary checks." | "Exclude `.env` secrets, configure secret scanning, and add a testing-performed section to the PR template." |
| Redis | "Add `AGENTS.md` and a repository skill covering setup, focused tests, QA, and conventions; validate their commands in CI." | "Configure formatting, naming checks, and pre-commit hooks. Add missing secret-file and OS-file exclusions." | "Build the core before focused test and QA checks, then enforce a minimum Codecov coverage threshold." |

### I.7 Raw output

The raw output for each repo is stored in `week5/evidence/raw/`. Factory's Markdown exporter truncates some long rationales with `...`; the report-input JSON preserves the full wording. We link it here instead of pasting full transcripts.

| Repo | Report narrative (CLI) | Per-criterion scores and rationales | Tool transcript | Terminal recording | Official web export |
|---|---|---|---|---|---|
| Day.js | [`dayjs-cli-messages.txt`](evidence/raw/dayjs-cli-messages.txt) | [`dayjs-report-input.json`](evidence/raw/dayjs-report-input.json) | [`dayjs-tool-transcript.json`](evidence/raw/dayjs-tool-transcript.json) | [`dayjs-readiness-20261108.typescript.gz`](evidence/raw/dayjs-readiness-20261108.typescript.gz) | [`dayjs-factory-export.md`](evidence/raw/dayjs-factory-export.md) |
| yt-dlp | [`yt-dlp-cli-messages.txt`](evidence/raw/yt-dlp-cli-messages.txt) | [`yt-dlp-report-input.json`](evidence/raw/yt-dlp-report-input.json) | [`yt-dlp-tool-transcript.json`](evidence/raw/yt-dlp-tool-transcript.json) | [`yt-dlp-readiness-20261108.typescript.gz`](evidence/raw/yt-dlp-readiness-20261108.typescript.gz) | [`yt-dlp-factory-export.md`](evidence/raw/yt-dlp-factory-export.md) |
| Redis | [`redis-cli-messages.txt`](evidence/raw/redis-cli-messages.txt) | [`redis-report-input.json`](evidence/raw/redis-report-input.json) | [`redis-tool-transcript.json`](evidence/raw/redis-tool-transcript.json) | [`redis-readiness-20261108.typescript.gz`](evidence/raw/redis-readiness-20261108.typescript.gz) | [`redis-factory-export.md`](evidence/raw/redis-factory-export.md) |

---

## Part II: Where Repos Fall Short

### Which pillars failed most, and was it consistent?

The ranking below uses the regrouped pillars from I.3. We report both raw failure counts and failure rates (failures / evaluated), because the pillars have very different numbers of evaluated criteria.

| Pillar | Day.js fails (rate) | yt-dlp | Redis | Pooled |
|---|---|---|---|---|
| Observability | 10 (100%) | 10 (91%) | 8 (73%) | **28 (88%)** |
| Security & Governance | 7 (78%) | 5 (45%) | 5 (42%) | 17 (53%) |
| Build System | 6 (60%) | 4 (44%) | 5 (50%) | 15 (52%) |
| Code Quality | 5 (71%) | 5 (83%) | 4 (57%) | 14 (**70%**) |
| Documentation | 4 (57%) | 3 (43%) | 3 (43%) | 10 (48%) |
| Testing | 3 (38%) | 3 (30%) | 3 (30%) | 9 (32%) |
| Style & Validation | 2 (33%) | 2 (33%) | 3 (60%) | 7 (41%) |
| Dev Environment | 2 (100%) | 1 (50%) | 1 (50%) | 4 (67%) |

**Observability failed most, by both count and rate.** It had the most failures in every repo; its failure rate tied Dev Environment in Day.js and was highest in the other two. **Code Quality had the second-highest failure rate**, and its failures were very consistent: the same four analyzer-style criteria (complexity, duplication, modularization, and debt tracking) failed in all three repos. Dev Environment has a 67% failure rate, but only six criteria were evaluated across all three repos, so that number carries little weight. Testing had the lowest pooled failure rate, with three failures in each repo.

**Most failures were shared.** The 24 criteria that failed everywhere make up 72 of the 104 total failures (69%). They fall into four groups:

- **Agent-specific artifacts:** `agents_md`, `skills`, `agents_md_validation`, `agentic_development`.
- **Production-operations instrumentation:** tracing, alerting, deployment observability, runbooks, product analytics, error-to-insight.
- **Code-analysis platforms:** the four Code Quality criteria above.
- **Repository governance files:** CODEOWNERS, PR templates, label taxonomy, and `.env` in `.gitignore`.

The repo-specific failures are where the projects actually differ:

- **Day.js** lacks contributor-facing build, setup, and QA documentation (`build_cmd_doc`, `single_command_setup`, `interactive_qa_exists`, `env_template`) and dependency-update automation.
- **yt-dlp** has no coverage gate, which its `pyproject.toml` deliberately says is "not implemented". Its unit tests also could not be collected in this environment.
- **Redis** lacks a repo-wide formatter, pre-commit hooks, and naming enforcement. It also failed both runnable checks.

Pre-registered H1 predicted that Style, Testing, and Build would vary less across repos than Observability and Dev Environment. The data partly supports it. Native Style & Validation (36–42%) and Testing (63–70%) were close across repos. Observability varied mostly because Redis gained three passes, and Dev Environment rests on only two evaluated criteria per repo.

### What explains the pattern?

**The shared failures suggest a mixture of missing safeguards and framework assumptions.** The 24 universally failed criteria account for 69% of failure observations. Some, such as contributor guidance or review templates, could help all three projects; others, such as product analytics and distributed tracing in a small library, have questionable applicability. The recurrence across this sample supports examining project-type fit, but does not establish that the framework caused most failures or that the projects lack quality.

We tested the suspects named in the assignment against the evidence:

| Suspect | What the data shows | What three repos can support |
|---|---|---|
| **Age** | Redis (2009) scored 50.0%, Day.js (2018) 33.9%, and yt-dlp (2020) 46.8%. The scores are not ordered by age. | No monotonic age–score relationship in this sample. Creation date also understates yt-dlp's lineage. |
| **Size** | The ranking matches size: 380 blobs → 33.9%, 1,235 → 46.8%, 1,957 → 50.0%. | A *hypothesis* that larger projects build up more CI and security infrastructure. Size moves together with owner type and project type, so we cannot isolate it. |
| **Language** | Each repo uses a different language, so language cannot be tested as a whole. It does affect individual criteria through how they are written. C passes `type_check` because compiler warnings count, and its `strict_typing` is skipped. JS and Python fail both because neither repo configures a type checker. | Effects on individual criteria only. No language-level effect can be tested. |
| **Governance** | Day.js is owned by a User account, has `author: iamkun`, and scored lowest. Both Organization-owned repos scored higher, mostly in Security (62.5% and 66.7% vs. 16.7%). | Only a correlation, and a weak one. An owner type or author field does not prove a project has a single maintainer. Day.js also had more of its Security criteria skipped (6 of 12). |
| **Project type** | Three of Redis's four Debugging & Observability passes (`metrics_collection`, `health_checks`, `profiling_instrumentation`) come from built-in server features: INFO/LATENCY, PING, and SLOWLOG. Remove those three and Redis would score 29/61 = 47.5%, close to yt-dlp's 46.8%. | This is the most concrete mechanism we found: the Redis lead is mostly a server-type bonus. H2 (project type matters more than language) is consistent with this, but each repo changes both variables at once. |

**The test environment also affected the scores, unevenly across repos.** The same kind of missing tool produced different outcomes:

- Day.js's `unit_tests_runnable` was **skipped** because Node/npm were missing. No tests were attempted.
- yt-dlp's was **failed** because `pytest` was missing. In the same run, a bounded offline CLI run parsed a repo-local DASH fixture and returned three formats, so `interactive_qa_runnable` passed.
- Redis's was **failed** after a bounded `runtest` timed out with no `src/redis-server` binary, and a server launch attempt exited with code 127.

`vcs_cli_tools` failed in all three repos only because `gh` was not installed on the audit machine. That says nothing about the repositories. None of these results means the test suites are broken, and none means they pass. They show what the scanner found in an environment we did not provision.

The levels hold up against these effects. Suppose `vcs_cli_tools` and the runnable-test and runnable-QA criteria had all passed (for Day.js, this means also scoring its skipped `unit_tests_runnable` as a pass): Day.js would score at most 23/60 = 38.3% and stay at Level 2, yt-dlp 31/62 = 50.0% (Level 3), and Redis 35/64 = 54.7% (Level 3).

### The cheapest high-leverage fix, per repo

These are recommendations only. We made no upstream changes and opened no issues or PRs. A higher score is also not the same thing as an agent succeeding.

| Repo | Our single change | Why this instead of the report's top suggestion |
|---|---|---|
| **Day.js** | Add a short "From a fresh clone" section to `CONTRIBUTING.md`. It would give the supported Node version, `npm ci`, the build command, one focused Jest command plus `npm test`, an explicit statement of environment requirements for offline core tests and a separate note for optional remote browser testing, and a three-line Node smoke snippet that imports the built library and formats a date. | We agree with the content of report #1. We would put it in the tool-neutral contributor guide, which helps human and agent contributors alike, rather than in a new agent-only file. A one-line `AGENTS.md` pointer could follow. The section targets the four Day.js-only failures in I.1 (build documentation, setup, environment, and QA path) at a cost of roughly one page of text. Report #2, strict typing, means upgrading a TypeScript 2.8-era toolchain, which is much more expensive. Caveat: we could not run Node, so we have not checked that these commands work. |
| **yt-dlp** | Narrowly extend the contributor docs' non-Hatch path. It would say how to install the test dependencies already declared in `pyproject.toml`, then show one offline collection/run command (the existing `offlinetest` target excludes the `download` marker). | Report #1 starts with this step but then adds timing reports, coverage reports, and coverage gates. Maintainers have explicitly marked coverage as not implemented, and coverage is expensive across about 940 extractor modules. Report #2 (strict typing, complexity, boundaries) is larger still. Our change addresses the observed failure, where `pytest` was missing and collection exited with code 1. It is honest about scale: Hatch users already have `hatch test`. It also respects the `.NO_AI` policy. We do **not** recommend `AGENTS.md` or skills for a project that forbids AI contributions, and we will not contribute upstream. |
| **Redis** | Add a focused "build core, run one test, drive the server" recipe. It would show the core-only build, then `./runtest --single unit/type/string --only "SET and GET an item"`, then a loopback `redis-server` launch plus `redis-cli PING`. A one-line precondition note should say that `runtest` requires a built `src/redis-server`. | The failure we observed was ordering: tests and QA were attempted before any build, and the harness timed out instead of failing fast. Report #3 names that sequence directly. Report #1 (`AGENTS.md` + skill + CI validation of commands) wraps the same content in agent-specific files and adds ongoing CI maintenance. The recipe is the useful core of it, and an `AGENTS.md` could point to it later. Report #2, adopting a repo-wide formatter, would cause major churn and `git blame` disruption in a 17-year-old C codebase. |

### Where the framework falls short

1. **Observability counts for more than it should for non-services, and it is applied inconsistently.** Day.js failed all 10 evaluated Observability criteria, including distributed tracing, alerting, and product analytics, for a 2 KB date library. Yet `health_checks` and `circuit_breakers` were *skipped* for the same library as not applicable. Product analytics and error-to-insight pipelines failed in all three repos. For a downloader that redacts sensitive values, or a database, instrumenting product usage could even be undesirable. These criteria should have been skipped as inapplicable, not counted as failures.
2. **Criteria check the form of a solution, not whether it works.** Redis failed `structured_logging` because its logger lives in `src/server.c` rather than in "a logging library or dedicated module", even though the same report credits its native INFO, LATENCY, and SLOWLOG diagnostics. yt-dlp's custom `_YDLLogger` failed for the same reason. The reverse also happens: having a configuration file is not the same as the behavior. Redis's Dependabot pass notes "live activity unverified", and coverage criteria pass because a config file exists.
3. **The auditor's machine leaks into the score.** `vcs_cli_tools` measures the scanner's own tools, not the repo. Seven criteria were skipped in every repo for lack of `gh` access. The same missing-runtime situation produced a skip for Day.js and failures for yt-dlp and Redis. A shared, provisioned audit environment, or a separate "environment-blocked" status, would make cross-repo comparison more trustworthy.
4. **It ignores a project's stance on AI.** yt-dlp's `.NO_AI/README.md` is a governance decision that matters directly to agents. Following the framework's suggestions (`agents_md`, `skills`, `agentic_development`) would conflict with that policy. The report mentioned the policy in prose, but no criterion captures whether agent use is even permitted.
5. **History-based checks break on shallow clones.** `documentation_freshness` passed in all three repos based on the single commit in each depth-1 clone. A shallow boundary can make older file contents appear in the recent boundary commit; a recent HEAD can therefore inflate apparent freshness. Cloning recently does not itself make the underlying commit recent. The co-authorship evidence for `agentic_development` came from that same single commit, so it cannot settle the question.
6. **The taxonomy and the scoring rule are unstable.** The assignment names eight pillars, the web export uses nine categories, and the CLI narrative used seven headings with some criteria misplaced. The level rule that was actually implemented (mean pass rate with fixed bands) differs from the 80% gated progression described in the public article. A reader cannot tell which criteria block a level without knowing which of these versions is in force.
7. **It misses the cost of setup.** Redis passes `single_command_setup` for its core build, but a full module build needs LLVM 21, CMake, and Rust 1.94. How long it takes to reach a first green test is a major factor for agents, and no criterion measures it.

## AI and tools disclosure

Factory Droid CLI 1.2.0, running GPT-6.1 Sol (High), produced all three readiness evaluations, including every score, rationale, and action item quoted here. Codex orchestrated the workflow and the evidence export and checked the evidence files. Claude Code helped synthesize the evidence and draft this write-up from those files. Factory's output was not edited. This write-up does not claim any separate manual verification: every statement about how a repository behaves comes from the reports' own bounded checks.

## Raw evidence and methodological caveats

**Evidence (all in `week5/evidence/`):**

- Per-criterion scores and rationales: [`raw/dayjs-report-input.json`](evidence/raw/dayjs-report-input.json), [`raw/yt-dlp-report-input.json`](evidence/raw/yt-dlp-report-input.json), [`raw/redis-report-input.json`](evidence/raw/redis-report-input.json).
- CLI report narratives: [`raw/dayjs-cli-messages.txt`](evidence/raw/dayjs-cli-messages.txt), [`raw/yt-dlp-cli-messages.txt`](evidence/raw/yt-dlp-cli-messages.txt), [`raw/redis-cli-messages.txt`](evidence/raw/redis-cli-messages.txt).
- Official web exports: [`Day.js`](evidence/raw/dayjs-factory-export.md), [`yt-dlp`](evidence/raw/yt-dlp-factory-export.md), [`Redis`](evidence/raw/redis-factory-export.md).
- Derived tables and crosswalk: [`comparison.json`](evidence/comparison.json), [`criterion-mapping.json`](evidence/criterion-mapping.json).
- Run and repository metadata: [`run-metadata.json`](evidence/run-metadata.json), [`repository-snapshots.json`](evidence/repository-snapshots.json), [`github-repository-metadata.json`](evidence/github-repository-metadata.json).

**Caveats:**

1. **The sample is tiny.** With n = 3 and selection done on purpose, age, language, size, governance, and project type all change together. Every explanation above is a hypothesis.
2. **There was one run per repo** with one model and one CLI version. An LLM-driven audit may score borderline criteria differently on a rerun.
3. **The audit environment was not provisioned.** There was no Node, `pytest`, `gh`, devcontainer CLI, or Redis build, and this affects runnable, remote, and VCS criteria unevenly.
4. **The eight-pillar table is our regrouping.** The nine-category table follows all three official Factory exports; the eight-pillar crosswalk is an analyst-defined partition.
5. **Clones were shallow.** Freshness and co-authorship evidence comes from a single commit.
6. **Scoring is ambiguous.** Levels follow the implemented mean-pass-rate rule, which differs from Factory's published 80% gating.
