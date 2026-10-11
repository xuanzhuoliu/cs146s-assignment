# Worked example

A finished plan, produced by this skill from
[yt-dlp#17802](https://github.com/yt-dlp/yt-dlp/issues/17802) ("Epidemic Sound
URL update breaks extractor syntax"). Read it for the level of evidence
expected, not for the Epidemic Sound details.

What makes it a passing plan: the "Claims checked" table overturns the most
authoritative statement in the thread, and the root cause names a dispatch axis
rather than a line number.

---

## Classification

Upstream contract change. `/track/mj8GTTwsZd/` still extracts correctly on
current `master`, so the extractor is not broken in general; only the site's new
`/music/tracks/<uuid>` URL shape is unrouted.

## Root cause

Two independent failures stacked. `EpidemicSoundIE._VALID_URL` accepts only
`sound-effects/tracks/` and `track/`, so the new `music/tracks/` URL matches no
extractor and falls through to `[generic]`, giving `ERROR: Unsupported URL`.
Behind that, `_real_extract` chooses its API path from the `sfx` named group in
the URL, but the real discriminator is the **ID format**: UUID-shaped
"kosmos" IDs resolve only at `/json/track/kosmos-id/<id>`, short public slugs
only at `/json/track/<id>`. Since the new music URLs carry UUIDs, widening the
regex alone routes them to the slug endpoint and yields HTTP 404.

```
$ curl -s -o /dev/null -w '%{http_code}\n' \
    https://www.epidemicsound.com/json/track/4f6686e3-037e-3f03-a9cd-0855f070b05a
404
$ curl -sL -o /dev/null -w '%{http_code}\n' \
    https://www.epidemicsound.com/json/track/kosmos-id/4f6686e3-037e-3f03-a9cd-0855f070b05a
200
```

## Claims checked

| Claim (source) | Verdict | Evidence |
|---|---|---|
| "Just changing the URL pattern won't be enough" (maintainer comment) | Confirmed | Slug endpoint returns 404 for a UUID; the branch must change too |
| "The JSON API seems to have gone" (maintainer comment) | **False** | `/json/track/kosmos-id/<uuid>` returns HTTP 200 with complete track JSON |
| "The old numeric IDs are also gone" (maintainer comment) | **False** | That endpoint returns `id: 148700`, the value already in `_TESTS` |
| "The first two test URLs are invalid" (maintainer comment) | Half true | `yFfQVRpSPz` 404s; `mj8GTTwsZd` still returns 200 |
| "The 3rd test URL's extracted data isn't the same" (maintainer comment) | Confirmed | Title is now `Doors, Appliance, Oven, Grill, Door Open, Close 01` |
| Reporter could not determine the canonical URL | Resolved | `publicSlug` in the response maps the UUID back to `/track/<slug>/` |

Because claims 2 and 3 are false, the NextJS hydration-scraping rewrite the
thread proposes is unnecessary.

## Changes

| File | Change |
|---|---|
| `yt_dlp/extractor/epidemicsound.py` | Add `music/tracks` to `_VALID_URL`; drop the `sfx` named group |
| `yt_dlp/extractor/epidemicsound.py` | In `_real_extract`, select `kosmos-id` on a UUID-shaped ID instead of on `sfx` |
| `yt_dlp/extractor/epidemicsound.py` | Replace the dead `yFfQVRpSPz` test; refresh the SFX test's expected `title`; add a `music/tracks` test |

```python
_VALID_URL = r'https?://(?:www\.)?epidemicsound\.com/(?:(?:music|sound-effects)/tracks|track)/(?P<id>[0-9a-zA-Z-]+)'

def _real_extract(self, url):
    video_id = self._match_id(url)
    is_kosmos_id = re.fullmatch(r'[\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12}', video_id, re.IGNORECASE)
    json_data = self._download_json(join_nonempty(
        'https://www.epidemicsound.com/json/track',
        is_kosmos_id and 'kosmos-id', video_id, delim='/'), video_id)
```

## Verification

All three URL shapes must extract:

```bash
python -m yt_dlp --simulate --print "%(id)s | %(title)s" \
  "https://www.epidemicsound.com/music/tracks/4f6686e3-037e-3f03-a9cd-0855f070b05a/" \
  "https://www.epidemicsound.com/track/mj8GTTwsZd/" \
  "https://www.epidemicsound.com/sound-effects/tracks/2f02f54b-9faa-4daf-abac-1cfe9e9cef69/"
```

Expected: `98281 | Wave Crest`, `148700 | Noplace`, `208931 | Doors, Appliance,
Oven, Grill, Door Open, Close 01`.

```bash
python -m devscripts.run_tests EpidemicSound
ruff check yt_dlp/extractor/epidemicsound.py
```

Before the test-data refresh, `run_tests EpidemicSound` fails on
`yFfQVRpSPz` with HTTP 404; that failure is expected and is what the third
change addresses.

## Open questions

- Which track should replace the dead `yFfQVRpSPz` SFX test? Needs a
  maintainer's preference for a stable fixture, not a lookup.

## Out of scope

- Migrating extraction to the NextJS hydration JSON. Only justified if the
  `/json/track/` endpoints are retired; they answer today.
- Any other extractor. The ID-format-versus-path confusion may exist elsewhere,
  but that is a separate audit.
