# Week 3 Write-up

**Skill name**, and the repo you targeted:
> `issue-to-plan`, targeting [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp).
> The skill lives in [week3/issue-to-plan/](issue-to-plan/) and is registered as
> a project skill at [.cursor/skills/issue-to-plan/](../.cursor/skills/issue-to-plan/)
> (identical copies).

## Part I: The Workflow

**What the workflow is**, and why it's worth encoding:
> Take an open GitHub issue, work out what is actually broken, and produce an
> implementation plan naming exact files, changes, and verification commands —
> without writing the patch.
>
> yt-dlp makes this maximally repeatable: ~1,745 extractors against sites that
> change without notice, and an issue tracker where the same four shapes recur
> forever ("site X broke", "add site Y", "no formats found", "unsupported
> URL"). I ran it twice here on unrelated issues and the procedure was
> identical both times; only the site differed. It is also the part of the work
> I would otherwise re-explain every time, because the expensive step is not
> writing the fix, it is deciding *which* fix the evidence supports.

**The decision point** in it (what the agent has to judge, not just execute):
> Two, and both are judgment rather than lookup.
>
> **Which claims in the thread are still true.** An issue plus its comments is a
> pile of assertions of unknown freshness, some from maintainers. The agent has
> to decide which ones are load-bearing for the plan and re-verify exactly
> those, because the cost of being wrong is asymmetric: believing a false "the
> API is gone" turns a six-line change into a rewrite.
>
> **What the code actually branches on.** When input shape A works and shape B
> does not, the agent must find the variable the code dispatches on and judge
> whether it is the real discriminator or a proxy that merely correlated with
> it until now. Getting this wrong produces a patch that makes the first error
> disappear and a new one surface one layer deeper. This is the judgment the
> skill exists to encode; everything else is `rg` and `curl`.

**What you learned running it manually** that you would not have guessed:
> I ran it by hand on [#17802](https://github.com/yt-dlp/yt-dlp/issues/17802)
> ("Epidemic Sound URL update breaks extractor syntax").
>
> **The only maintainer comment on the thread was substantially wrong, and I
> would have believed it.** It states "The JSON API seems to have gone... Similar,
> if simpler, data is in the NextJS v13 hydration JSON in the page" and "The old
> numeric IDs are also gone", which together say: rewrite the extractor to scrape
> HTML. Two `curl` calls falsified both halves. The JSON API answers fine, and it
> still returns the same numeric IDs already baked into `_TESTS`:
>
> ```
> /json/track/4f6686e3-037e-3f03-a9cd-0855f070b05a           -> HTTP 404
> /json/track/kosmos-id/4f6686e3-037e-3f03-a9cd-0855f070b05a -> HTTP 200, id 98281 "Wave Crest"
> /json/track/kosmos-id/b66ce071-c3a0-445c-a5a8-971ef2016596 -> HTTP 200, id 148700 "Noplace"
> ```
>
> **The second surprise was the shape of the real bug.** The obvious fix — add
> `music/tracks` to `_VALID_URL` — matches the URL and then 404s, because
> `_real_extract` picks its API path from the `sfx` named group in the URL while
> the actual discriminator is the *ID format*. UUID "kosmos" IDs resolve only
> under `kosmos-id/`; short slugs only under the bare path. The path group had
> worked purely because sound-effects URLs used to be the only ones carrying
> UUIDs. I only found this because I probed the endpoint *behind* the regex
> before trusting the regex fix — which is now a rule in the skill body.
>
> I prototyped the real fix (6 lines) and confirmed all three URL shapes extract:
> `98281 | Wave Crest`, `148700 | Noplace`, `208931 | Doors, Appliance, Oven...`.
>
> The generalisation I did not expect going in: **the most authoritative-sounding
> sentence in a thread is the most dangerous one**, because it is the one nobody
> re-checks. That became the skill's first and highest-priority decision point.

## Part II: The Skill

**Your description**, verbatim:
```
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
```

**Why it's worded that way** (what a user would type to trigger it):
> Nobody types "produce a verified implementation plan". They type "where do I
> even start" or "what would it take to fix this", so those literal phrasings
> are quoted in the description rather than paraphrased, and they sit in the
> second sentence instead of behind a long capability clause.
>
> Three deliberate choices beyond that:
>
> - **The trailing exclusions are load-bearing, not decoration.** "Not for ...
>   ordinary end-user operation of the tool the issue happens to be about"
>   exists because every trigger phrase overlaps with yt-dlp *usage* questions.
>   In testing, the near-miss that cited this clause by name was correctly
>   declined (test 5 below).
> - **"Applies even when the request sounds routine"** targets the failure mode
>   where a request looks self-evident ("read issue, make plan") and the agent
>   skips the skill because it thinks it already knows the steps.
> - **"including maintainers'"** is in the description, not just the body, so
>   the agent knows before loading that this skill is about distrusting the
>   thread. That is the differentiator from generic debugging.

**Judgment encoded in the body** (what it says to do when things are ambiguous, and what not to do):
> Five decision points, each written as a rule plus the reasoning that makes it
> checkable:
>
> 1. **Trust nothing in the thread until a command confirms it** — including
>    maintainer comments. Promote a claim to a fact only after it passes, and
>    record the evidence in a "Claims checked" table so the reader can see which
>    assertions were re-tested rather than inherited.
> 2. **Classify before locating.** A three-row table maps evidence to the three
>    classes (upstream contract change / our regression / unsupported
>    capability), each of which implies a different plan. The tie-breaker is
>    concrete: run the same code path against a known-good sibling input.
> 3. **Find the dispatch axis, not the failing line** — the generalised form of
>    the Epidemic Sound bug. Operationally: before loosening any regex,
>    allowlist, or type check, confirm the code *behind* it handles the new
>    input shape.
> 4. **Ask the user, or find out yourself.** The ambiguity rule has a threshold
>    instead of a vibe: find out yourself if a read-only command answers it in
>    under two minutes; escalate only for credentials, paid accounts, specific
>    regions, or product-intent calls. "I could not determine X" is admissible
>    only after naming the command you ran.
> 5. **State the blast radius.** A plan that does not say which existing tests
>    go red is incomplete, and each failure must be labelled "this change fixes
>    it" or "this change must also update it".
>
> The explicit *don'ts*: never propose a fix for a failure you did not
> reproduce; never copy the issue's suggested fix in untested; never plan a
> rewrite when a targeted change passes the same checks; never write the full
> implementation (a diff sketch is the ceiling); don't list every file you read.
> There are also two stop conditions — if it does not reproduce, plan the
> information-gathering instead of a fix; if an open PR already does the work,
> plan the delta or stop.

**Supporting files**, if any, and why they aren't inline:

| File | Contents | Why it's separate |
|---|---|---|
| [reference-yt-dlp.md](issue-to-plan/reference-yt-dlp.md) | yt-dlp navigation and exact commands: setup, `--simulate` reproduction, how to map a URL to an extractor via `_VALID_URL` / `_extractors.py`, the key files, `devscripts.run_tests`, and four repo-specific judgment notes (match the URL before the API; check what the extractor branches on; site output drifts so expected-value mismatches are test-data updates; the project's NO AI / NO LLM policy) | Repo-specific, and the skill is written to work on any repository. Inlining 90 lines of yt-dlp trivia would cost that context on every unrelated firing and would quietly make the skill look yt-dlp-only. SKILL.md links it from one line in step 4, so it loads only when the target actually is yt-dlp. |
| [plan-template.md](issue-to-plan/plan-template.md) | A full worked example: the finished Epidemic Sound plan, including the "Claims checked" table that overturns the maintainer comment, the diff sketch, and the verification commands with expected output | SKILL.md already carries the empty template inline, because the output shape is needed on every run. The worked example is ~100 lines and is only needed when the agent is unsure how much evidence counts as enough — exactly the progressive-disclosure case. It also doubles as the calibration sample for the evidence bar. |

## Part III: Testing

**Triggering:**

A methodology note first, because my first attempt measured the wrong thing.
I initially ran the four prompts as real tasks in fresh subagents with the repo
as the working directory. One "fired" and two did not — but a direct probe
("list every skill available to you") returned **`ISSUE-TO-PLAN: ABSENT`**: a
project skill added mid-session is not in the catalogue until reload, so the
skill could not have auto-fired at all. The one apparent hit was the subagent
*finding* `SKILL.md` by exploring the repo it happened to be sitting in. Those
runs are discarded.

Since triggering is purely a description-matching decision, the results below
come from a controlled harness: a fresh agent per row, given a catalogue of ten
real skill descriptions (including confusable neighbours `review-bugbot`,
`review-security`, and `autopilot`, whose own description contains "triaging"),
the bare user message, and no indication which entry is mine.

| Prompt | Should fire? | Did it? |
|---|---|---|
| "Something broke in yt-dlp. The URL `.../music/tracks/4f6686e3-.../` used to work and now I just get 'ERROR: Unsupported URL'. Where do I even start with this?" | Yes | **Yes** — `LOAD: issue-to-plan`; "points at a concrete regression and asks where to start" |
| "Take a look at yt-dlp issue #17775 and turn it into an implementation plan." | Yes | **Yes** — `LOAD: issue-to-plan`; "points at a specific GitHub issue number and explicitly asks for it to be turned into an implementation plan" |
| "A user reports that downloading from MangoTV fails with 'no video formats found'. Can you scope what it would actually take to fix that?" | Yes | **Yes** — `LOAD: issue-to-plan`; cites the "scope this bug" / "what would it take to fix" triggers |
| "Here's a diff I wrote against `yt_dlp/extractor/epidemicsound.py` that widens the `_VALID_URL` regex. Review it and tell me if I've missed anything." | No (near-miss) | **No** — `LOAD: none`; "the user wants review of an existing diff, which `issue-to-plan` explicitly excludes" |
| "yt-dlp keeps erroring out on this playlist URL. What's the right command line to just grab the audio as mp3?" | No (second near-miss) | **No** — `LOAD: none`; "ordinary end-user usage of yt-dlp asking for the right flags, which `issue-to-plan` explicitly excludes" |

Three fire, both near-misses decline, and both declines quote the exclusion
clause as the reason — so that clause is doing real work rather than being
decoration.

Two controls, because a harness that always agrees with me proves nothing:

- **Does the harness discriminate?** Re-running near-miss 4 against a
  deliberately vague description ("Analyzes bugs and issues in a repository and
  produces an implementation plan. Use when the user is dealing with a bug, an
  error, a broken feature, or a code change...") returned `LOAD: review-bugbot`.
  The harness routes on description content, not on my preferences.
- **Did my rewrite actually help?** Honest answer: **not measurably.** Midway
  through I rewrote the description to front-load the quoted user phrasings,
  believing it had failed to fire. Re-running all three should-fire prompts
  against the *original* wording returned `LOAD: issue-to-plan` three times out
  of three. The original was never the problem; the absent catalogue was. I kept
  the revision for the quoted vocabulary and the "sounds routine" clause, but
  the evidence does not support claiming it fixed a triggering failure, and I am
  not going to pretend otherwise.

**End-to-end run** on your repo, and the result:

Run on a *fresh* issue the skill had never seen —
[yt-dlp#17787](https://github.com/yt-dlp/yt-dlp/issues/17787), "Unsupported
embed type 'redge' when downloading from LSMReplay" — in a clean agent, with
the skill explicitly loaded and the scratch yt-dlp clone at `master`. Abridged
to the load-bearing parts; the structure is the skill's template verbatim.

```
## Classification
Upstream contract change. Every one of the 11 LTV video records sampled from current
replay.lsm.lv listings reports source.name == "redge"; none reported backscreen or
youtube, the only two types LSMLTVEmbedIE handles.

## Root cause
LSMLTVEmbedIE._real_extract dispatches on data['source']['name'] and only knows
backscreen/telia and youtube; anything else raises at lsm.py:220. For redge,
source.embed_url is "" — there is no URL to hand to another extractor, so the
function's url_result tail cannot be reused at all. Separately, the reporter's
specific video is DRM-protected, so routing it correctly still cannot download it:

  #EXT-X-KEY:METHOD=SAMPLE-AES,KEYFORMAT="com.apple.streamingkeydelivery",URI="skd://skd"

## Claims checked
| Claim (source)                                            | Verdict        | Evidence |
| "needs --geo-bypass-country LV" (dirkf)                   | Confirmed, and | same token: no XFF -> 403, XFF 8.8.8.8 -> 403,
|                                                           | fixable in-tree| XFF 46.109.108.141 (LV) -> 200; _GEO_COUNTRIES=['LV'] fixes it
| "someone could reverse this module" (dirkf)               | UNNECESSARY    | lsm-player.js 0.16.0 ships its source comments intact and
|                                                           |                | spells the API out: 3 plain JSON calls, no signing
| "the no-DRM check applies" (dirkf)                        | Confirmed for  | DRM is per-asset: of 5 sampled redge items only the
|                                                           | this URL only  | reporter's 6460593 has a non-empty drm object
| Implied: the FO API is LV-only like the embed page        | FALSE          | telpa.lsm.lv returns 200 from a US IP; only
|                                                           |                | ltv.lsm.lv/embed is geo-blocked
| Implied: videoType can be hardcoded                       | FALSE          | videoType=MOVIE on live asset 6379272 -> HTTP 400;
|                                                           |                | videoType=LIVE -> 200

## Changes
| yt_dlp/extractor/lsm.py | Add _GEO_COUNTRIES = ['LV'] to LSMLTVEmbedIE
| yt_dlp/extractor/lsm.py | Add a redge branch to _real_extract returning a formats dict
| yt_dlp/extractor/lsm.py | New _extract_redge helper: FO chain keyed on item type,
|                           self.report_drm() when playlist['drm'] is non-empty
| yt_dlp/extractor/lsm.py | Replace the two dead fixtures (both 404), refresh three
|                           pic.latvijasradio.lv -> pic.lsm.lv thumbnails, add a redge test

## Verification
$ python -m yt_dlp --simulate --print "%(id)s | %(title)s | %(duration)s" \
    "https://replay.lsm.lv/lv/skaties/ieraksts/ltv/318532/tas-notika-seit-vabole"
  expect: 6421290 | Tas notika šeit. Vabole | 3469
$ python -m yt_dlp --simulate ".../dzivnieku-stasti-..."
  expect: ERROR: [LSMLTVEmbed] <id>: This video is DRM protected
$ python -m pytest test/test_download.py -k LSM -q

Blast radius: -k LSM is ALREADY 6 failed, 5 passed on pristine master, and the
prototype left that count unchanged. Three are pic.lsm.lv thumbnail drift, two are
dead fixtures, one needs a local JS runtime. The last change fixes five of six.

## Open questions
- The live path is unexercised end to end; whether live belongs in this change is
  a maintainer's scope call.
- Which records make durable _TESTS fixtures needs a maintainer's feel for LSM's
  retention, not a lookup.

## Out of scope
- Any attempt at the DRM assets; report_drm is the correct final answer.
- The vimeo embed type: confirmed missing from the same dispatch, but no page
  serving it turned up, so it cannot be verified.
- LSMReplayIE's own playback-type allowlist, which has the identical staleness
  one layer up ('playable_video_youtube'). A separate bug on a separate dispatch.
```

What the skill bought, judged against the rubric it encodes: it reproduced
before planning, it overturned a maintainer's "someone could reverse this
module" by reading the player bundle's intact source comments, it refused to
let one DRM-protected asset close the issue after finding DRM is per-asset
(4 of 5 sampled items are clean), it caught that `videoType` cannot be
hardcoded via an HTTP 400, it measured the blast radius against pristine
`master` so the 6 pre-existing failures were not misread as regressions, and it
escalated exactly the two questions a command cannot answer. The two decision
points from Part I both fired on an issue with no connection to the one they
were derived from — the claims table overturned the thread, and the
`source.name` allowlist was the dispatch axis.

It also restored the scratch clone (`git status` clean) and, per
`reference-yt-dlp.md`, flagged yt-dlp's NO AI / NO LLM policy rather than
proposing a PR.

## Submission
1. `Command (⌘) + F` for `TODO`. No results means you're done.
2. Confirm the skill directory itself is committed under `week3/`.
3. Push all changes to your remote repository and submit via Gradescope.
