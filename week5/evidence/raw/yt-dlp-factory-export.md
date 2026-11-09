# Agent Readiness Report: yt-dlp

**Level:** 3/5  
**Overall Score:** 47%  
**Generated:** 2026-11-09 01:35:27 UTC  
**Commit:** `b3b18f8`  
**Branch:** master  

## Summary

| Metric | Value |
|--------|-------|
| Total Criteria | 84 |
| Passed | 29 |
| Failed | 33 |
| Skipped | 22 |

## Pass Rate by Category

| Category | Pass Rate |
|----------|-----------|
| Style & Validation | 42% |
| Build System | 56% |
| Testing | 70% |
| Documentation | 57% |
| Development Environment | 50% |
| Debugging & Observability | 11% |
| Security | 63% |
| Task Discovery | 33% |
| Product & Experimentation | 0% |

## Style & Validation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Type Checker | 0/1 | 🔴 Failed | No mypy, Pyright, or equivalent static type-checker configuration or CI invocation was found. Ruff is not a Python type checker. |
| Strict Typing | 0/1 | 🔴 Failed | Python supports stricter checking, but no strict mypy/Pyright configuration or equivalent checker is present. |
| Cyclomatic Complexity | 0/1 | 🔴 Failed | No complexity threshold/analyzer is configured. Ruff selects no C901 or PLR complexity rules; no Radon, Lizard, or Sonar configuration was found. |
| Large File Detection | 0/1 | 🔴 Failed | No file-size hook, CI threshold, LFS rule, or module-length linter rule was found. |
| Duplicate Code Detection | 0/1 | 🔴 Failed | No copy/paste detector such as jscpd, CPD, or Sonar duplication analysis is configured. |
| Code Modularization Enforcement | 0/1 | 🔴 Failed | The large extractor/downloader/networking architecture has meaningful boundaries, but no import-linter or architecture-boundary tests enforce them. Deprecated-API bans are not layer boundaries. |
| Technical Debt Tracking | 0/1 | 🔴 Failed | No debt inventory or TODO/FIXME tracking automation was found. Ruff TODO syntax rules do not track outstanding debt; author/link requirements TD002/TD003 are disabled. |
| Linter Configuration | 1/1 | 🟢 Passed | pyproject.toml configures Ruff rules, and quick-test.yml runs ruff check --output-format github . |
| Code Formatter | 1/1 | 🟢 Passed | autopep8 is configured in pyproject.toml and invoked through Hatch, pre-commit hooks, Makefile, and CI. |
| Pre-commit Hooks | 1/1 | 🟢 Passed | .pre-commit-config.yaml runs Ruff and autopep8; .pre-commit-hatch.yaml runs hatch fmt. CONTRIBUTING.md documents installing the hook. |
| Naming Consistency | 1/1 | 🟢 Passed | Ruff explicitly enables naming rules N803 and N804, with pep8-naming configuration; CONTRIBUTING.md also documents coding conventions. |
| Dead Code Detection | 1/1 | 🟢 Passed | Ruff enables the Pyflakes F rules, including unused imports and unused local variables, enforced in pre-commit and CI. |
| N+1 Query Detection | N/A | Skipped | No application database or ORM is used; database N+1 query detection is not applicable. |

## Build System

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| VCS CLI Tools | 0/1 | 🔴 Failed | Neither gh nor glab is installed, so authenticated VCS CLI access could not be established. |
| Agentic Development | 0/1 | 🔴 Failed | No active coding-agent workflow/configuration was found. CONTRIBUTING.md and .NO_AI/README.md expressly prohibit AI contributions. The shallow checkout exposes only one commit. |
| Feature Flag Infrastructure | 0/1 | 🔴 Failed | No feature-flag service or custom staged-feature rollout system was found. CLI configuration and compatibility switches alone are not evidence of rollout flags. |
| Unused Dependencies Detection | 0/1 | 🔴 Failed | No deptry, pip-extra-reqs, or other unused-dependency checker is configured. |
| Build Command Documentation | 1/1 | 🟢 Passed | README.md#compile documents dependency installation, python -m bundle.pyinstaller, make, and make yt-dlp. |
| Dependencies Pinned | 1/1 | 🟢 Passed | Committed uv.lock pins dependencies; bundle/requirements/*.txt also contain exact versions and hashes used by CI. |
| Single Command Setup | 1/1 | 🟢 Passed | CONTRIBUTING.md documents installing Hatch, hatch run setup, hatch shell, and direct python -m yt_dlp execution. |
| Release Notes Automation | 1/1 | 🟢 Passed | .github/workflows/release.yml generates release notes using devscripts/make_changelog.py; build/release workflows update the changelog. |
| Release Automation | 1/1 | 🟢 Passed | Reusable release/build workflows publish GitHub releases and PyPI packages, with nightly schedules and master-push triggers. |
| Automated PR Review Generation | N/A | Skipped | Skipped because neither gh nor glab is installed. Label-policy comments are not substantive automated code reviews. |
| Fast CI Feedback | N/A | Skipped | Skipped because no authenticated gh/glab CLI is available to measure PR check start-to-finish durations. |
| Build Performance Tracking | N/A | Skipped | No build-duration monitoring or build-artifact cache was found, and authenticated CI timing access is unavailable. Nightly commit-hash caching alone does not establish build performance tracking. |
| Deployment Frequency | N/A | Skipped | Nightly and master release automation exists, but actual successful release/deployment frequency cannot be verified without authenticated gh/glab access. |
| Progressive Rollout | N/A | Skipped | Not an infrastructure repository or hosted service. Stable/nightly/master binary channels are not percentage-based service rollouts. |
| Rollback Automation | N/A | Skipped | Not an infrastructure repository. The CLI documents version downgrade options, but infrastructure rollback automation is not applicable. |
| Monorepo Tooling | N/A | Skipped | Single root application and Python distribution. Extractors, bundle tooling, and test fixture packages are not independently deployed applications. |
| Heavy Dependency Detection | N/A | Skipped | CLI/library rather than a browser-bundled application. Release executable bundling does not make frontend bundle-size analysis applicable. |
| Version Drift Detection | N/A | Skipped | One build package/module. Platform requirement exports and test plugin fixtures do not create independent build modules. |
| Dead Feature Flag Detection | N/A | Skipped | Skipped because feature_flag_infrastructure does not pass; there is no identified feature-flag system to audit. |

## Testing

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Unit Tests Runnable | 0/1 | 🔴 Failed | Bounded command: PYTHONDONTWRITEBYTECODE=1 python -m pytest --collect-only test/test_compat.py -p no:cacheprovider, from repo root (absolute test path used). Python 3.14.9 exited 1: No module named... |
| Test Performance Tracking | 0/1 | 🔴 Failed | No explicit pytest duration reporting, retained timing/JUnit reports, or test-performance analytics was found. CI timeouts and ordinary elapsed summaries alone do not qualify. |
| Test Coverage Thresholds | 0/1 | 🔴 Failed | No minimum coverage gate exists. Hatch run-cov explicitly prints 'Code coverage not implemented' and exits 1. |
| Unit Tests Exist | 1/1 | 🟢 Passed | test/ contains many unit tests, including the bounded sample test_compat.py, test_aes.py, test_cache.py, and test_utils.py. |
| Integration Tests Exist | 1/1 | 🟢 Passed | test_execution.py tests CLI subprocess execution; test_downloader_http.py exercises the downloader against an in-process HTTP server; download tests cover extractors. |
| Flaky Test Detection | 1/1 | 🟢 Passed | CI passes --reruns 2 --reruns-delay 3.0 using pytest-rerunfailures. test/conftest.py and devscripts/run_tests.py also implement flaky-test quarantine controls. |
| Test File Naming Conventions | 1/1 | 🟢 Passed | CONTRIBUTING.md documents extractor test names; devscripts/run_tests.py maps names to test_* methods, and test/test_download.py explicitly generates consistent test_<extractor> names. |
| Test Isolation | 1/1 | 🟢 Passed | Hatch test environments configure pytest-randomly and pytest-xdist, providing randomized ordering and parallel-test support. |
| Interactive QA Exists | 1/1 | 🟢 Passed | README documents Python 3.11+, optional dependencies, CLI invocation/options and sample interactions; CONTRIBUTING.md documents running the checkout with python -m yt_dlp. Local/public extraction n... |
| Interactive QA Runnable | 1/1 | 🟢 Passed | Python 3.14.9 successfully ran python -m yt_dlp in simulate/JSON mode against test/testdata/mpd/unfragmented.mpd using --enable-file-urls, --ignore-config, --no-cache-dir, and --no-check-formats. E... |

## Documentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| AGENTS.md File | 0/1 | 🔴 Failed | No AGENTS.md exists at the repository root or elsewhere in the tracked tree. |
| Skills Configuration | 0/1 | 🔴 Failed | No repository-local SKILL.md files or valid skill directories were found. |
| AGENTS.md Freshness Validation | 0/1 | 🔴 Failed | No AGENTS.md exists, and no automation validates or generates agent instructions. |
| README File | 1/1 | 🟢 Passed | Root README.md provides installation, dependency, build, CLI usage, configuration, and embedding instructions. |
| Automated Documentation Generation | 1/1 | 🟢 Passed | Makefile and devscripts generate README option text, supported-site lists, manpages, completions, issue templates, and changelogs. |
| Documentation Freshness | 1/1 | 🟢 Passed | git log --since="180 days ago" shows README.md and CONTRIBUTING.md changed in commit b3b18f8 dated 2026-11-04. |
| Service Architecture Documented | 1/1 | 🟢 Passed | README documents its external SponsorBlock API integration and endpoint, alongside external networking/runtime dependencies. Architecture diagrams are not required when service dependencies are doc... |
| API Schema Docs | N/A | Skipped | CLI/library exposes no service HTTP API. Recursive OpenAPI/Swagger/GraphQL schema searches found no application API schema. |

## Development Environment

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Dev Container | 0/1 | 🔴 Failed | No .devcontainer/devcontainer.json or other devcontainer configuration was found. Release-build Docker files are not a development container. |
| Environment Template | 1/1 | 🟢 Passed | README.md documents environment variables and defaults, including XDG_CONFIG_HOME, XDG_CACHE_HOME, HOME, APPDATA, and YTDLP_NO_LAZY_EXTRACTORS. |
| Local Services Setup | N/A | Skipped | CLI/library needs no managed local database or service stack. External websites are remote inputs; bundle/docker/compose.yml is release-build infrastructure. |
| Database Schema | N/A | Skipped | No application database or ORM schema exists; JSON cache/config files and browser-cookie readers are not an application-owned database. |
| Devcontainer Runnable | N/A | Skipped | devcontainer CLI is not installed; no development-container configuration exists. |

## Debugging & Observability

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Structured Logging | 0/1 | 🔴 Failed | Custom _YDLLogger lives inside general utils, and networking adapters use standard logging, but no dedicated logger module or declared logging-library dependency meets the criterion. |
| Distributed Tracing | 0/1 | 🔴 Failed | No trace/request ID propagation or distributed-tracing instrumentation was found. PO-token diagnostic 'trace' verbosity is not distributed tracing. |
| Metrics Collection | 0/1 | 🔴 Failed | No application metrics/telemetry exporter or monitoring instrumentation was found. Download progress output alone is not metrics collection. |
| Error Tracking Contextualized | 0/1 | 🔴 Failed | No contextualized Sentry, Bugsnag, Rollbar, or equivalent production error-tracking integration was found. |
| Alerting Configured | 0/1 | 🔴 Failed | No PagerDuty/OpsGenie integration or application alerting rules were found. |
| Runbooks Documented | 0/1 | 🔴 Failed | No incident-response runbook/playbook directory or explicit operational runbook pointer was found. General FAQ and troubleshooting links alone do not qualify. |
| Deployment Observability | 0/1 | 🔴 Failed | No deployment-impact dashboard pointers or deployment monitoring/notification integrations were found. |
| Profiling Instrumentation | 0/1 | 🔴 Failed | Performance profiling is meaningful for this downloader/parser, but no configured profiler, APM agent, memory profiler, or flamegraph workflow was found. |
| Circuit Breakers | 1/1 | 🟢 Passed | RetryManager implements bounded external-call retries with configurable sleep functions; README documents exponential backoff via --retry-sleep fragment:exp=1:20. |
| Code Quality Metrics Dashboard | N/A | Skipped | No coverage/maintainability metrics platform or retained metrics reports were found. CodeQL security analysis does not alone prove those metrics; remote code-scanning analyses cannot be inspected w... |
| Health Checks | N/A | Skipped | Not a hosted service; HTTP health endpoints, readiness/liveness probes, and load-balancer checks are not applicable. |

## Security

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| CODEOWNERS File | 0/1 | 🔴 Failed | No CODEOWNERS file exists in the root, .github, or tracked repository tree. |
| Dependency Update Automation | 0/1 | 🔴 Failed | No Dependabot/Renovate configuration or dependency-update PR workflow was found. Auto-generated dlp-bot Makefile variables alone do not establish configured dependency-update PR automation. |
| Gitignore Comprehensive | 0/1 | 🔴 Failed | .gitignore covers Python caches, build/dist, cookies/netrc, IDE files, and OS files, but does not exclude .env files. |
| Automated Security Review Generation | 1/1 | 🟢 Passed | .github/workflows/codeql.yml runs CodeQL analysis for Python, JavaScript/TypeScript, and Actions on pushes, PRs, and a schedule, producing readable code-scanning findings. |
| PII Handling | 1/1 | 🟢 Passed | Config.hide_login_info masks usernames/passwords; PO-token provider documentation explicitly prohibits logging tokens or sensitive information. This provides PII-aware handling guidance. |
| Secrets Management | 1/1 | 🟢 Passed | Release workflows use GitHub Actions secrets for signing and publication credentials, including secrets.RELEASE_KEY, secrets.GPG_SIGNING_KEY, and secrets.ARCHIVE_REPO_TOKEN. |
| Sensitive Data Log Scrubbing | 1/1 | 🟢 Passed | yt_dlp/utils/_utils.py Config.hide_login_info replaces sensitive CLI option values with PRIVATE before configuration debug output. |
| Minimum Dependency Release Age | 1/1 | 🟢 Passed | pyproject.toml configures [tool.uv] exclude-newer = "7 days"; uv.lock records P7D. Explicit exceptions exist for pip, protobug, pyinstaller, uv, and yt-dlp-ejs. |
| Branch Protection | N/A | Skipped | No gh/glab CLI is installed, so administrative access and remote branch-protection rules cannot be verified. |
| Secret Scanning | N/A | Skipped | No local secret-scanning hook or workflow was found. Native scanning is unknown because authenticated administrative VCS access is unavailable. |
| DAST Scanning | N/A | Skipped | CLI/library is not deployed as a web service; staging-endpoint DAST is not applicable. |
| Privacy Compliance | N/A | Skipped | Local CLI/library has no identified application-owned end-user analytics or centralized personal-data collection. Local credential handling is assessed separately. |

## Task Discovery

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Issue Labeling System | 0/1 | 🔴 Failed | Templates consistently assign type/area labels such as bug, enhancement, and site-bug, but no priority label taxonomy is evidenced locally; remote labels could not be checked. |
| PR Templates | 0/1 | 🔴 Failed | .github/PULL_REQUEST_TEMPLATE.md includes description, issue context, and contribution attestations, but no general testing-performed section. Extractor-only add/update-tests guidance is insufficient. |
| Issue Templates | 1/1 | 🟢 Passed | .github/ISSUE_TEMPLATE contains structured YAML forms for core/site bugs, features, support requests, and questions. |
| Backlog Health | N/A | Skipped | No authenticated gh/glab CLI is available to inspect open-issue titles, labels, age, and recent activity. |

## Product & Experimentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Product Analytics Instrumentation | 0/1 | 🔴 Failed | No Mixpanel, Amplitude, PostHog, Heap, GA4, or equivalent feature-usage analytics instrumentation was found. |
| Error to Insight Pipeline | 0/1 | 🔴 Failed | No application-error tracker connected to automatic issue creation or error-to-issue workflow was found. |

---

*Generated by Factory Agent Readiness*