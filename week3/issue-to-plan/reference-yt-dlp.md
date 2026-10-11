# yt-dlp reference

Read this only when the target repository is `yt-dlp/yt-dlp`.

## Setup

```bash
git clone --depth 1 https://github.com/yt-dlp/yt-dlp.git
cd yt-dlp
python -m devscripts.install_deps --include-group dev   # adds pytest ~=9.0, ruff, requests
python -m yt_dlp --version                              # runs from source, no install needed
```

`python -m devscripts.install_deps --print` lists dependencies without
installing them. Core yt-dlp runs from a bare checkout; the dev group is only
needed to run tests.

## Reproducing

```bash
python -m yt_dlp -v --simulate "<url>"                            # no download
python -m yt_dlp --simulate --print "%(id)s | %(title)s" "<url>"  # just the fields
```

Always use `--simulate` while diagnosing. `-v` reproduces the `[debug]` block
that issue reporters paste, which makes your output directly comparable to
theirs.

`WARNING: [generic] Falling back on generic information extractor` followed by
`ERROR: Unsupported URL` means **no extractor's `_VALID_URL` matched**. That is
a routing failure, not an extraction failure, and it is a different fix from a
`_download_json` 404.

## Finding the owning extractor

Extractors are one class per site in `yt_dlp/extractor/<site>.py`, class name
ends in `IE`, and each is imported in `yt_dlp/extractor/_extractors.py`.

```bash
ls yt_dlp/extractor/ | rg -i <sitename>
rg -n "_VALID_URL|class .*IE\(|_TESTS" yt_dlp/extractor/<site>.py
rg -n "<site>" yt_dlp/extractor/_extractors.py     # confirm it is registered
```

An extractor that exists but is not imported in `_extractors.py` is never
loaded. Check this before concluding a site is unsupported.

## Key files

| Path | What it holds |
|---|---|
| `yt_dlp/extractor/common.py` | `InfoExtractor` base class; the info-dict field spec |
| `yt_dlp/extractor/_extractors.py` | The import list that makes an extractor live |
| `yt_dlp/utils/` | `traverse_obj`, `join_nonempty`, `int_or_none` and friends |
| `test/test_download.py` | Drives each extractor's `_TESTS` entries |

Mandatory info-dict fields are `id`, `title`, and either `url` or `formats`.
Everything else must degrade to `None` rather than raise.

## Testing

```bash
python -m devscripts.run_tests <ExtractorName>    # e.g. EpidemicSound; hits the network
python -m devscripts.run_tests core               # offline, fast
python -m devscripts.run_tests -k <expression>
ruff check yt_dlp/extractor/<site>.py
```

Extractor tests are live network tests driven by the `_TESTS` list in the
extractor itself. A failure can mean the code broke **or** that the test's
fixture URL died upstream. Distinguish these before planning: fetch the test's
URL directly. If it 404s for everyone, the test data is stale and replacing it
is part of the work, not evidence about the code.

## yt-dlp specific judgment

- **Match the URL before the API.** Confirm `_VALID_URL` matches, then confirm
  the endpoint that `_real_extract` derives from it responds. These fail
  separately and a URL-only fix is the classic incomplete patch.
- **Check what the extractor branches on.** Many extractors select an API path
  from a named group in `_VALID_URL`. If the site adds a new URL prefix that
  carries the *old* ID format, or an old prefix that carries a *new* one, the
  named group is the wrong discriminator and the branch must key on the ID
  instead.
- **Site output drifts.** Titles and format lists in `_TESTS` go stale without
  any code change. Report an expected-value mismatch as a test-data update, not
  as a bug.
- **The project forbids AI-generated contributions.** Read
  `CONTRIBUTING.md#no-ai--no-llm-policy`. Plans produced here are for the user's
  own understanding; do not open a PR against yt-dlp from this workflow.
