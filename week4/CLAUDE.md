# Day.js

A ~2KB immutable date library that copies Moment.js's API. The core stays tiny, and everything else ships as opt-in plugins (`dayjs.extend(x)`) and locales (`dayjs.locale(x)`). Keeping it small and matching Moment's behavior are the two hard constraints.

## Layout

- `src/index.js`: the core `Dayjs` class and the `dayjs()` factory. Instance state lives in `$`-prefixed fields: `$d` (the Date), `$y $M $D $W $H $m $s $ms`, `$L` (locale), `$u` (utc), `$x` (plugin extras). `src/utils.js` exports one-letter helpers (`U.s` padStart, `U.p` prettyUnit, `U.u` isUndefined, ...), and the core adds `Utils.l`, `.i`, `.w`. `src/constant.js` holds the unit names and the parse/format regexes.
- `src/plugin/<name>/index.js`: one directory per plugin, always `export default (o, c, d) => { const proto = c.prototype; ... }`. `o` is the options, `c` the Dayjs class, `d` the factory.
- `src/locale/<key>.js`: one file per locale. Each `import dayjs from 'dayjs'`, builds a `locale` object, calls `dayjs.locale(locale, null, true)` and `export default locale`.
- `types/`: hand-written `.d.ts` files. Every plugin needs `types/plugin/<name>.d.ts` that augments `declare module 'dayjs' { interface Dayjs {...} }`.
- `test/` mirrors `src/`: `test/*.test.js` (core), `test/plugin/<name>.test.js`, `test/locale/<key>.test.js`. `test/__mocks__/dayjs.js` maps the bare `'dayjs'` import to `src/`.
- `build/`: the Rollup UMD build (`index.js`) and the ESM post-processing (`esm.js`).

## Commands (Node + npm; there is no yarn lockfile)

```
npm ci
npm run lint                                  # eslint src/* test/* build/*; add -- --fix to autofix
npx jest test/plugin/isToday.test.js --coverage=false   # one file, fast
TZ=UTC npm test                               # full suite, the way CI runs it
NODE_OPTIONS=--openssl-legacy-provider npm run build    # UMD + size-limit check
npm run babel                                 # ESM build into esm/
```

- `npm test` runs the timezone tests under 4 pinned TZs, then the whole suite in **the shell's TZ** with a **100% line-coverage threshold**. In a US DST zone, 6 tests in `dayOfYear`, `localizedFormat` and `timezone` fail on a clean checkout. Use `TZ=UTC` before you assume your change broke something.
- Without the OpenSSL flag, `npm run build` crashes with `ERR_OSSL_EVP_UNSUPPORTED` in the `size` step (webpack 4 inside size-limit). By then the bundles are already written.

## Conventions

- Style is ESLint airbnb-base: **no semicolons, no trailing commas**, 2 spaces, single quotes, no file extensions in imports. Prettier only applies to `docs/**/*.md`.
- Tests are Jest (v22) using `it(...)` blocks. Most files start with `MockDate.set(new Date())` in `beforeEach` and `MockDate.reset()` in `afterEach`. Behavior is checked **against Moment** (pinned `moment@2.29.2`): `expect(dayjs(x).format(f)).toBe(moment(x).format(f))`. Write new tests that way too.
- Import from source in tests: `import dayjs from '../../src'`, `import foo from '../../src/plugin/foo'`, `import '../../src/locale/xx'`.
- Every new line in `src/` must be covered, or the 100% threshold fails `npm test`.
- New plugin checklist: `src/plugin/<name>/index.js`, `types/plugin/<name>.d.ts` (`test/plugin/declarations.test.js` fails without it), and `test/plugin/<name>.test.js`.
- New locale checklist: the first line must be `// <English Name> [<key>]`, because `build/index.js` and `test/locale/keys.test.js` parse it with `/\/\/ (.*) \[/`. `name` must equal the lowercase filename. `ordinal` must return a value for 1–31.
- Commits use Conventional Commits (`fix(plugin): ...`, `feat: ...`, `docs: ...`). semantic-release reads them to pick the version.

## Guardrails

- **Edit `src/`, never the build outputs.** The root-level `dayjs.min.js`, `plugin/`, `locale/`, `esm/`, `index.d.ts`, `locale.json` and `coverage/` are generated and gitignored. The root `plugin/isToday.js` looks like source but is a minified bundle. The root `index.d.ts` is a copy of `types/index.d.ts`.
- Keep `import dayjs from 'dayjs'` in locale and plugin files. Don't rewrite it to a relative path: Rollup treats `'dayjs'` as external, and Jest maps it through `__mocks__`.
- Don't hand-edit `CHANGELOG.md` or `package.json` `version` (`0.0.0-development`). semantic-release owns both.
- The core bundle is capped at **2.99 KB gzipped** (`size-limit`). Put new features in a plugin unless the core genuinely needs them.
- Branch from `dev`, and target PRs at `dev`. `master` is release-only: pushing there publishes to npm.
- Don't upgrade the toolchain (jest 22, eslint 4, babel 7 beta, rollup 2) as a side effect of another change.
- `docs/` holds translated READMEs, not API docs. The API docs live in a separate repo (day.js.org).
