# Week 5 Repo Notes (preparation evidence)

> **Status: completed.** All three Factory readiness reports have been generated: Day.js Level 2 (20/59 passed, 25 skipped), yt-dlp Level 3 (29/62, 22 skipped), Redis Level 3 (32/64, 20 skipped). Results and analysis are in [`../writeup.md`](../writeup.md), and the raw evidence is in `../evidence/raw/`. The notes below were written before the runs and are kept as preparation evidence.
>
> The notes themselves are **not** Factory readiness results. Each claim below comes from reading a file in the local shallow clones under `../study-repos/`, and the paths are relative to each repo root. No repo commands, tests, or installs were run. Where a file was *not found*, this means not found by filename search in this checkout at the listed SHA.

## Preparation checklist

- [x] Three repos cloned (shallow) outside the coursework repo: `study-repos/{dayjs,yt-dlp,redis}`
- [x] HEAD SHAs read from `.git/refs/heads/*`; each `.git/shallow` contains only that SHA (depth-1 clone)
- [x] Languages, build/test/lint commands and CI documented below with file citations
- [x] `writeup.md` first drafted with placeholder report fields; it has since been replaced by the final write-up.
- [x] Runbook written: `docs/READINESS_RUNBOOK.md`
- [x] Factory account created and local Droid authenticated.
- [x] Subscription block resolved. The first run had returned `No active subscription found` (see `evidence/account-status-20261108.txt`, `evidence/dayjs-attempt-summary.txt`).
- [x] `/readiness-report` run in each repo root. Raw output is saved under `week5/evidence/raw/` (`*-cli-messages.txt`, `*-report-input.json`, `*-tool-transcript.json`, `*-readiness-20261108.typescript`, and the official `dayjs-factory-export.md`).
- [x] CLI version (1.2.0), model (GPT-6.1 Sol (High)), UTC date (2026-11-09), and report IDs recorded in `evidence/run-metadata.json`.
- [x] All three worktrees were unchanged by the runs (each report records `hasLocalChanges: false`).
- [x] GitHub creation and last-push timestamps collected in `evidence/github-repository-metadata.json`; these do not measure activity intensity.
- [x] Part I tables filled in from the reports, and Part II written from the data.

## Pinned snapshots

| Repo | Branch | HEAD SHA | Source |
|---|---|---|---|
| dayjs | `dev` | `436bde0bcded312781cbe45dc2b0ef079a36d8e3` | `.git/refs/heads/dev`, `.git/shallow` |
| yt-dlp | `master` | `b3b18f8fc606e782ee7c82b0780a40c67b829072` | `.git/refs/heads/master`, `.git/shallow` |
| redis | `unstable` | `8e2ba8c4ef6ccf76d327c689cddd5fbe64daa5e5` | `.git/refs/heads/unstable`, `.git/shallow` |

---

## dayjs (iamkun/dayjs)

**Language / architecture**
- JavaScript library: "2KB immutable date time library alternative to Moment.js" (`package.json:4`). Core is in `src/index.js` and `src/constant.js`. Locales are in `src/locale/*.js` (143 files), and plugins are in `src/plugin/<name>/index.js` (37).
- TypeScript type declarations in `types/index.d.ts`, `types/locale/index.d.ts`. `package.json:6` points to `index.d.ts`.
- Built with Rollup + Babel (`build/rollup.config.js`, `build/index.js`, `babel.config.js`). Bundle size limit is 2.99 KB (`package.json:22-27`).
- License MIT, author `iamkun` (`package.json:47-48`).

**Documented check commands**
- `npm run lint` → `eslint src/* test/* build/*` (`package.json:11`; `CONTRIBUTING.md:10`).
- `npm test` runs Jest under several `TZ` values, then the full suite with a **100% line-coverage threshold** (`package.json:8`). `CONTRIBUTING.md:23-24` says "Help us keep 100% test coverage" and "use `npm test`".
- Pre-commit hook runs `lint` via the `pre-commit` npm package (`package.json:19-21`).
- Style configs: `.eslintrc.json`, `prettier.config.js`, `.editorconfig`.

**CI / governance**
- `.github/workflows/check.yml` calls `.github/workflows/lint-test.yml` on push/PR to `dev`. That workflow runs `npm install`, `npm run lint`, `npm test`, and an optional Codecov upload (`lint-test.yml:18-30`).
- Release through semantic-release (`.releaserc`, `.github/workflows/release.yml`).
- Not found in this checkout: `SECURITY.md`, `CODEOWNERS`, `dependabot.yml`, CodeQL workflow, PR template, `AGENTS.md`/`CLAUDE.md`, Dockerfile/devcontainer, `.nvmrc`. (`.github/` contains only `FUNDING.yml`, one issue template, and three workflows.)
- Dev tool versions are old: `eslint ^4.19.1`, `jest ^22.4.3`, `typescript ^2.8.3` (`package.json:64,70,84`).

## yt-dlp (yt-dlp/yt-dlp)

**Language / architecture**
- Python ≥3.11, CPython and PyPy (`pyproject.toml:18,29-44`). Built with Hatchling (`pyproject.toml:1-3`). Entry point `yt_dlp:main` (`pyproject.toml:140-141`).
- Plugin-style extractor architecture: 940 `.py` files directly under `yt_dlp/extractor/`. Core modules include `yt_dlp/YoutubeDL.py`, `yt_dlp/options.py`, `yt_dlp/networking/`. Developer scripts are in `devscripts/`, and packaging is in `bundle/` (PyInstaller, Docker in `bundle/docker/linux/Dockerfile`).
- License Unlicense (`pyproject.toml:27`). Named maintainer team in `pyproject.toml:10-15` and `Maintainers.md`.

**Documented check commands**
- Recommended: `hatch run setup` (installs a pre-commit hook), `hatch fmt`, `hatch test` (`CONTRIBUTING.md:165-182`).
- Without hatch: `python -m devscripts.run_tests`, `ruff check .`, `autopep8 --diff .` (`CONTRIBUTING.md:186-208`). The same commands are in `Makefile:79-88` (`codetest`, `test`, `offlinetest` which excludes the `download` marker).
- Lint config: Ruff with a large explicit `select`/`ignore` list and banned-API rules (`pyproject.toml:257-407`). autopep8 config is at `pyproject.toml:409-470`. Pytest uses `strict_config`/`strict_markers` (`pyproject.toml:472-482`).
- Coverage is explicitly **not implemented**: `run-cov = "echo Code coverage not implemented && exit 1"` (`pyproject.toml:235`).
- Hash-pinned requirement files are in `bundle/requirements/*.txt`, installed with `--require-hashes` in CI (`.github/workflows/quick-test.yml:34-35`).

**CI / governance**
- 13 workflow files in `.github/workflows/`. `quick-test.yml` runs the required checks "Core test" and "Code check" (ruff, autopep8, file mode) on every push/PR (`quick-test.yml:15-69`). `core.yml` runs a matrix over OS/Python versions, with retries for flaky networking tests (`core.yml:42-105`). `codeql.yml` is also present.
- Workflow hardening: `permissions: {}` at top level, actions pinned by SHA, `persist-credentials: false` (`quick-test.yml:9,24-26`). Also `.github/zizmor.yml` and `.github/actionlint.yml`.
- `.github/PULL_REQUEST_TEMPLATE.md` and six issue-form templates are present.
- Not found: `SECURITY.md`, `CODEOWNERS`, `dependabot.yml`, `AGENTS.md`/`CLAUDE.md`.
- **AI policy:** `.NO_AI/README.md` says the project "strictly forbids the usage of LLMs, agents, or any other AI tools for any kind of contribution" (issues, PRs, review comments, translation). Relevant to the Documentation/Governance discussion, the sample is retained for local read-only analysis; no contributions will be submitted.

## redis (redis/redis)

**Language / architecture**
- C server: 221 `.c`/`.h` files directly under `src/`. Vendored dependencies are in `deps/` (e.g. `deps/jemalloc`, `deps/croaring`; see `deps/README.md`). Optional modules are fetched with `make modules-update` (`README.md:233-236`).
- Test suite in Tcl: `tests/test_helper.tcl`, `tests/unit/*.tcl`. It "involves starting and manipulating local `redis-server` instances" (`tests/README.md:4-5`).
- License: RSALv2/SSPLv1/AGPLv3 tri-license with a contributor license agreement (`CONTRIBUTING.md:1-5`).

**Documented check commands**
- Build: `make` / `make build redis` (core only), `make BUILD_TLS=yes` (`README.md:298-368`). The full module build needs LLVM 21, CMake 3.25–3.31.6, and Rust 1.94 (`README.md:219-221`).
- Test: `make test`. With TLS: `./utils/gen-test-certs.sh && ./runtest --tls` (`README.md:388-399`).
- Dev environment: `docker/Dockerfile.noble` is the recommended build container. `make bootstrap` installs system packages and "may override existing versions" (`README.md:248-270`). `make bootstrap list` / `dry-run` are available to check prerequisites without installing them (`README.md:272-294`).
- Style: no repo-level formatter config found (`.clang-format` exists only under `deps/jemalloc/`). Spell checking uses `.config/typos.toml` + `.github/workflows/spell-check.yml`. Compiler warnings fail the CI build (`REDIS_CFLAGS='-Werror'`, `ci.yml:18`).

**CI / governance**
- `.github/workflows/ci.yml` builds with `-Werror` on Ubuntu, macOS, 32-bit, libc malloc, CentOS, and old toolchains. It runs `./runtest --tags -slow` and an AddressSanitizer job, and checks that the generated `commands.def` is up to date (`ci.yml:11-105`).
- Other workflows: `codeql-analysis.yml`, `coverity.yml`, `codecov.yml` (+ root `codecov.yml`), `daily.yml`, `external.yml`, `reply-schemas-linter.yml`, `spell-check.yml`.
- `SECURITY.md` has a supported-versions table and a disclosure process (`SECURITY.md:12-40`). `.github/dependabot.yml` updates **GitHub Actions only**, weekly (`dependabot.yml:6-10`).
- Not found: `CODEOWNERS`, PR template, `AGENTS.md`/`CLAUDE.md`. `.dockerignore:21,27` excludes `.cursor` / `.cursor/plans`, but no agent-instruction file is committed.

---

## Cross-repo differences relevant to the eight pillars (observations, not scores)

| Pillar | dayjs | yt-dlp | redis |
|---|---|---|---|
| Style & Validation | ESLint + Prettier + pre-commit lint | Ruff + autopep8 + pre-commit, required CI check | `-Werror` + typos spell-check; no repo formatter config found |
| Build System | npm scripts + Rollup | Hatch / Makefile, hash-pinned reqs | Make; heavy system toolchain for modules |
| Testing | Jest, 100% line-coverage gate | pytest via `devscripts/run_tests.py`; coverage "not implemented" | Tcl `runtest` against real server processes; ASan job |
| Documentation | Short `CONTRIBUTING.md`; multilingual `docs/` | Long `CONTRIBUTING.md` developer section | Long README build section; `tests/README.md` |
| Dev Environment | No container/version file found | Hatch envs; Docker for bundling only | `docker/Dockerfile.noble`, `make bootstrap` |
| Code Quality | Coverage gate; size-limit | Banned-API lint rules | Sanitizer, CodeQL, Coverity |
| Observability | (library; N/A-ish, to be checked) | (CLI; to be checked) | (server; to be checked) |
| Security & Governance | No SECURITY.md / CODEOWNERS / dependabot found | Hardened workflows, CodeQL, zizmor; no SECURITY.md; NO-AI policy | SECURITY.md, CodeQL, dependabot (actions only), CLA |

When this table was written, the Observability row was left open on purpose. It has since been resolved by the reports. In the eight-pillar regrouping, Observability passed 0/10 criteria for Day.js, 1/11 for yt-dlp, and 3/11 for Redis. Redis's three passes come from native server diagnostics: INFO/LATENCY, PING, and SLOWLOG. Several criteria, such as product analytics and distributed tracing, were scored as failures for all three repos instead of being skipped as inapplicable. The framework critique in `../writeup.md` (Part II) covers this.
