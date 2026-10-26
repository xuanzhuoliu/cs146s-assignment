# Week 4 Write-up

**Repo chosen** and link to your fork:
> [iamkun/dayjs](https://github.com/iamkun/dayjs). Fork: https://github.com/xuanzhuoliu/dayjs/tree/agent-config (`CLAUDE.md` is at the repo root on the `agent-config` branch)

**File you wrote** (`AGENTS.md` or `CLAUDE.md`):
> `CLAUDE.md`, at the root of the fork and copied to [`week4/CLAUDE.md`](CLAUDE.md). I picked `CLAUDE.md` because Part III runs Claude Code, which loads that file automatically.

I first chose yt-dlp, which I used in Week 3. It has since added a strict NO AI / NO LLM policy (`CONTRIBUTING.md` and `.NO_AI/README.md`) that asks agents not to interact with the repo at all. Making it agent-ready would go directly against the maintainers' wishes, so I switched to dayjs, which has no such policy.


## Part I: Exploration

| | Finding |
|---|---|
| Build / run | `npm ci`, then `NODE_OPTIONS=--openssl-legacy-provider npm run build`. Rollup builds UMD bundles for the core, each plugin and each locale, then a `size-limit` check runs against a **2.99 KB** gzipped cap (currently 2.79 KB). `npm run babel` builds the ESM tree into `esm/`. Without the OpenSSL flag, the build crashes on Node 17+ with `ERR_OSSL_EVP_UNSUPPORTED` in the size step (webpack 4 inside size-limit), after the bundles are already written. `release.yml` sets the same flag, which is how I found the fix. |
| Test | `TZ=UTC npm test`. The script runs the timezone tests under 4 pinned TZs, then the whole Jest suite in **the shell's TZ** with a 100% line-coverage threshold. On my Mac (America/Los_Angeles), 6 tests in `dayOfYear`, `localizedFormat` and `timezone` fail on a clean checkout. Under `TZ=UTC` (what CI uses on ubuntu-latest), all 794 pass. For one file: `npx jest test/plugin/isToday.test.js --coverage=false`. |
| Lint / format | `npm run lint` (ESLint 4, airbnb-base, no semicolons, no trailing commas). The `pre-commit` npm package installs a git hook that runs it on every commit. Prettier only formats `docs/**/*.md`. |
| Key directories and entry points | `src/index.js` (the `Dayjs` class and `dayjs()` factory), `src/utils.js` (one-letter helpers), `src/constant.js`, `src/plugin/<name>/index.js` (about 37 plugins), `src/locale/<key>.js` (143 locales), `types/` (hand-written `.d.ts`), `test/` (mirrors `src/`), `build/` (Rollup and ESM scripts). |
| Unstated conventions | Plugins are `export default (o, c, d) => { const proto = c.prototype ... }`. Instance state is in `$`-prefixed fields (`$d`, `$y`, `$M`, `$L`, `$u`, `$x`). Tests mock "now" with `MockDate` in `beforeEach`/`afterEach` and assert **against Moment** (pinned 2.29.2). A locale's first line must be `// Name [key]`, because the build and `keys.test.js` parse it with a regex. Every plugin needs a `types/plugin/<name>.d.ts`, which `declarations.test.js` enforces. Locales and plugins import the bare `'dayjs'`, which Jest maps through `test/__mocks__/dayjs.js` and Rollup treats as external. PRs target `dev`, and `master` is release-only. |
| Off-limits (generated, vendored) | Build outputs at the repo root, all gitignored: `dayjs.min.js`, `plugin/`, `locale/`, `esm/`, `index.d.ts`, `locale.json`, `coverage/`. The root `plugin/*.js` files look like source but are minified bundles. `CHANGELOG.md` and the `0.0.0-development` version are owned by semantic-release. `patches/` is a patch-package fix for semantic-release. |

**How you figured it out**: what you asked the agent, what you had to read yourself:
> I had the agent read `package.json`, the CI workflows, `build/*.js`, `.eslintrc.json`, `.gitignore`/`.npmignore` and a sample plugin, locale and test file. Then it **ran** every command instead of trusting the scripts. Running them is what exposed the two most useful facts. The timezone-dependent failures only appear when you run the suite locally in a DST zone. The OpenSSL crash only appears on modern Node. Neither is documented anywhere except indirectly (the `TZ` prefixes in `package.json`, `NODE_OPTIONS` in `release.yml`). The locale-header rule came from reading `build/index.js` and `test/locale/keys.test.js`, which use the same regex. I read the CONTRIBUTING file myself and found it was only 3 short bullets, which is why most of these rules had never been written down.


## Part II: The File

**Anything you deliberately left out**, and why:
> I left out the API surface (formatting tokens, the plugin list, the locale list), because the agent can `ls src/plugin` or read the README. I left out the translated READMEs in `docs/` and the Sauce Labs browser tests (`npm run test:sauce`), because they need credentials and no small task touches them. I left out generic advice like "write tests" and "keep functions small." I kept only the commands I had run successfully, so there's nothing like "run prettier on src," which this repo doesn't do.

**The hardest call** on what to include:
> Whether to spend lines on the `TZ=UTC` caveat and the "edit `src/`, not root `plugin/`" warning. They make the file longer, and both are environment- or build-dependent rather than always true. I kept both. Each is a case where a competent agent would do the plausible thing and draw the wrong conclusion: it would "fix" code that isn't broken, or edit a minified bundle that the next build overwrites. Those wrong-but-plausible traps are the most valuable lines in the file.


## Part III: Trying It Out

Each task ran in a fresh Claude Code agent with no prior context, working in the fork with `CLAUDE.md` as its project instructions. I reviewed every command it ran and every file it changed.

| # | Task | Did the agent use your commands and conventions? |
|---|---|---|
| 1 | "Run the test suite and tell me whether it passes." | **Yes.** Its single command was `TZ=UTC npm test`, taken word for word from the file. It reported 794/794 passing and noted the coverage threshold. Without being asked, it also warned that running in the local US timezone would show 6 known failures. That is the exact trap the file exists to prevent: without it, the agent would have run plain `npm test`, seen 6 failures, and gone looking for a bug. |
| 2 | "Add an isWeekend() plugin: dayjs().isWeekend() should return true on Saturday and Sunday." | **Yes, on every checklist item.** It read `isToday` as a model and then created exactly the three files the "new plugin checklist" names: `src/plugin/isWeekend/index.js` in the `(o, c) => { const proto = c.prototype ... }` shape, `types/plugin/isWeekend.d.ts` augmenting `interface Dayjs`, and `test/plugin/isWeekend.test.js` with the `MockDate` `beforeEach`/`afterEach` and `../../src` imports. There were no semicolons or trailing commas, so lint was clean on the first try. It didn't touch the root `plugin/` bundles. It ran the fast single-file command first (`npx jest test/plugin/isWeekend.test.js test/plugin/declarations.test.js --coverage=false`), then `npm run lint` and `TZ=UTC npm test`. Result: 798/798 passing, and the new plugin is at 100% coverage. It didn't commit, and it pointed out that a real PR should branch from `dev`, which comes straight from the guardrails. |

**One thing you'd change** about the file after watching it get used:
> The "test against Moment" rule needs an escape hatch. Moment has no `isWeekend()`, but the agent still followed the rule literally. It built a Moment comparison out of `moment(date).day()`, then asserted the same value twice: once against a hard-coded table and once against that derived Moment value. The second assertion adds nothing. I'd change the line to: *"Compare against Moment when Moment has the same API. For dayjs-only plugins, assert fixed expected values on dates you pick by hand."* More generally, rules written as "always do X" get applied even where X doesn't fit, so each one should say when it applies.
