# Week 2 Write-up

## Part I: The Server

**API chosen**, and why:
> GitHub Issues, through a **GitHub App** rather than an OAuth App. I read and
> file issues constantly, so I have opinions about what a useful tool call
> looks like, and I can judge whether the agent picked the right one. The
> GitHub App choice is deliberate: classic OAuth App tokens never expire and
> carry no refresh token, which would make the "silent refresh" half of Part
> III impossible to demonstrate honestly. A GitHub App's user-to-server token
> expires in 8 hours and ships with a refresh token, and its permissions are
> per-repository rather than account-wide.

**How to run it** (one command):
```
python -m week2.github_mcp.server
```
(One-time setup — GitHub App creation, `cp week2/.env.example .env`, and
`python -m week2.github_mcp.auth login` — is in [week2/README.md](README.md).)

| Tool | What it does | Read/Write | Composes with |
|---|---|---|---|
| `whoami` | Returns the authenticated login | Read | Cheap pre-flight before a write; confirms the token is alive |
| `search_repos` | Query -> repositories | Read | Emits `full_name`, the `repo` argument of every other tool |
| `list_issues` | Issues in a repo, PRs filtered out | Read | Takes `repo` from `search_repos`; emits `number` |
| `get_issue` | One issue, body included, truncated at 4000 chars | Read | Takes `repo` + `number` from `list_issues` |
| `create_issue` | Files an issue; previews by default | **Write** | Takes `repo` from `search_repos`; returns the new `number` |

The chain is `search_repos -> list_issues -> get_issue -> create_issue`, and
each hop consumes an identifier the previous hop produced.


## Part II: Agent Ergonomics

| Decision | Where | Why |
|---|---|---|
| Schema-level constraint | [server.py:52-58](github_mcp/server.py#L52) (`RepoName` regex), [server.py:121](github_mcp/server.py#L121) and [server.py:148-150](github_mcp/server.py#L148) (`Literal` enums), [server.py:122](github_mcp/server.py#L122) / [server.py:155](github_mcp/server.py#L155) (`Field(ge=…, le=…)`) | `sort: Literal["stars", "forks", …]` puts the legal set in the JSON Schema, so an illegal value is rejected before a request is made and the validation error *names the alternatives*. `str` + a docstring sentence gives the agent a 422 from GitHub and nothing to act on. The `owner/name` regex catches the most common mistake (passing a bare repo name) at the boundary instead of as a confusing 404. |
| Output shaping (fields kept vs. dropped) | [server.py:67-90](github_mcp/server.py#L67) (`_shape_repo`, `_shape_issue`), [server.py:202-206](github_mcp/server.py#L202) (body truncation) | GitHub's issue object is ~40 fields, most of them parallel URL spellings (`url`, `repository_url`, `labels_url`, `events_url`, `node_id`). I keep 9. A raw `list_issues` page is tens of thousands of tokens; the shaped version is a few hundred, and it also decouples my contract from GitHub's — if they add fields, my output doesn't move. `list_issues` omits bodies entirely and tells the agent to call `get_issue` for one, so a browse doesn't pay for text nobody read. |
| Structured errors (retry vs. don't-retry) | [errors.py:23-33](github_mcp/errors.py#L23) (the `kind -> retryable` table), [github_client.py:73-138](github_mcp/github_client.py#L73) (status -> kind mapping), [server.py:63-64](github_mcp/server.py#L63) (`_as_error`) | Every failure comes back as `{"error", "kind", "retryable", "retry_after"?, "hint"?}`. `kind="not_found"` with `retryable=false` tells the agent to fix the identifier; `kind="rate_limited"` with `retry_after=42` tells it to wait, and the 42 comes from `Retry-After` or `X-RateLimit-Reset` ([github_client.py:43-51](github_mcp/github_client.py#L43)). The distinction that matters most is 403-because-rate-limit versus 403-because-not-installed — same status code, opposite correct response — so I split them on `X-RateLimit-Remaining` ([github_client.py:86-104](github_mcp/github_client.py#L86)). The fallback for unrecognised statuses is deliberately non-retryable ([github_client.py:132-137](github_mcp/github_client.py#L132)); see Part II's closing note for the live failure that taught me this. Nothing raises; an exception escaping a tool ends the agent's turn. |
| Docstring that chains tools together | [server.py:174-180](github_mcp/server.py#L174) (`list_issues`), [server.py:193-199](github_mcp/server.py#L193) (`get_issue`), plus `FastMCP(instructions=…)` at [server.py:23-41](github_mcp/server.py#L23) | Each docstring names the *source* of every identifier: "`issue_number` is the `number` from `list_issues` for the same `repo`, not a GitHub internal id and not a position in the list." The negative cases are there because both are plausible guesses. The server-level `instructions` carry what no single tool owns: the four-step workflow, and the rule that `retryable=false` means change the arguments rather than call again. |
| Brake on the write tool | [server.py:218-226](github_mcp/server.py#L218) (the `dry_run` parameter), [server.py:240-247](github_mcp/server.py#L240) (the preview branch), [server.py:44-51](github_mcp/server.py#L44) (`ToolAnnotations`) | `create_issue` is the only tool that changes public state and notifies watchers, so it defaults to `dry_run=true`: it returns `{"dry_run": true, "created": false, "would_create": {…}}` and makes no request. Creating requires a deliberate second call with `dry_run=false`. The default lives in the schema, so even an agent that ignores the docstring gets the safe path. Readers carry `readOnlyHint: true`; the writer carries `readOnlyHint: false`, `destructiveHint: false` (creating an issue is additive, not destructive) and `idempotentHint: false` (calling twice files two issues). |

**One thing you changed after watching the agent misuse a tool:**
> Two, both found the first time an agent drove the server for real rather than
> against mocks.
>
> **The one that mattered.** The agent called `create_issue(..., dry_run=false)`
> on a repository where the Issues feature happened to be switched off. GitHub
> answers that with **410 Gone**, which my status mapping did not name, so it
> fell through to a catch-all that returned `{"kind": "upstream", "retryable":
> true}`. That is precisely the wrong answer: 410 here is permanent, and I had
> just told the agent to try again forever. I added an explicit 410 branch
> ([github_client.py:111-117](github_mcp/github_client.py#L111)) mapping to a new
> `unavailable` kind — not retryable, with a hint naming the repository setting
> to change. More importantly I changed the *default*: an unrecognised status is
> now non-retryable ([github_client.py:132-137](github_mcp/github_client.py#L132)).
> Guessing "retryable" for a status you have never thought about turns one
> unhandled case into a loop; guessing "not retryable" costs at most one missed
> retry. The lesson generalises past this bug — the fallback branch of an error
> mapping is a design decision, not a formality.
>
> **The one that was subtler.** `search_repos` returned
> `{"total_count": 0, "results": []}` for a repository that exists and that the
> agent could read a second later. GitHub's search index only covers public
> repos, and this one is private. An empty array is indistinguishable from "no
> such repository", and an agent reading it will reasonably stop and report
> failure. The fix is not a new tool, it is saying what the silence means: the
> empty result now carries a `note`
> ([server.py:147-156](github_mcp/server.py#L147)) explaining the public-only
> index and telling the agent to pass a known `owner/name` straight to
> `list_issues`, and the docstring says the same
> ([server.py:130-132](github_mcp/server.py#L130)). In the transcript below the
> agent does exactly that and recovers in one step.
>
> A third live-integration fix, found the same way: GitHub 301-redirects
> repositories whose owner has renamed their account, and my client did not
> follow redirects, so the redirect body came back shaped like an issue list and
> crashed the response shaper. Fixed at
> [github_client.py:157-161](github_mcp/github_client.py#L157), with a guard at
> [server.py:191-196](github_mcp/server.py#L191) that turns any unexpected payload
> shape into a structured error instead of a traceback.


## Part III: OAuth

**Flow**: how a token is obtained, cached, and refreshed:
> Authorization code, split across two processes on purpose.
>
> *Obtained* — `python -m week2.github_mcp.auth login` ([auth.py:205](github_mcp/auth.py#L205))
> generates a random `state`, starts a one-shot HTTP listener on
> `127.0.0.1:8765/callback`, and opens the browser at GitHub's authorize URL.
> On redirect it compares the returned `state` to the one it generated
> ([auth.py:240-242](github_mcp/auth.py#L240)) and aborts on a mismatch, so a
> page I happen to have open can't drive my local listener into exchanging a
> code I never authorized. It then POSTs the code to GitHub's token endpoint.
>
> *Cached* — the access token, refresh token and absolute expiry timestamps go
> to `~/.config/cs146s-github-mcp/token.json`, outside the repository. The file
> is created via `os.open(..., 0o600)` ([auth.py:85-92](github_mcp/auth.py#L85))
> so it is never even briefly group- or world-readable.
>
> *Refreshed* — `get_valid_token()` ([auth.py:165](github_mcp/auth.py#L165))
> runs inside the server on every API call. It refreshes when the token is
> within 300 seconds of expiry ([config.py:28](github_mcp/config.py#L28)), not
> at expiry, so a call that starts just under the wire doesn't fail in flight.
> GitHub rotates the refresh token on every exchange, so the new one is
> persisted immediately ([auth.py:160-162](github_mcp/auth.py#L160)); dropping
> it would make the *following* expiry unrecoverable. Note that GitHub reports
> OAuth failures with HTTP 200 and an `error` key, so the status code alone is
> not a success check ([auth.py:131-136](github_mcp/auth.py#L131)).

**Scopes requested**, and why each is necessary:
> GitHub Apps use per-resource permissions rather than OAuth scope strings, so
> the ask is narrower than `repo` would be, and it is scoped to the specific
> repositories I install the app on rather than everything I can reach.
>
> | Permission | Level | Why it is necessary |
> |---|---|---|
> | Repository -> Metadata | Read-only | Mandatory for any repository access; backs `search_repos`. There is no level below this. |
> | Repository -> Issues | Read and write | `list_issues` and `get_issue` need read. `create_issue` is the one tool that needs write, and it is the only reason this is not read-only. |
>
> Nothing else is requested. In particular: no `Contents` (the server never
> reads or writes code), no `Pull requests` (`list_issues` filters PRs out
> rather than asking for permission to see them properly), no `Administration`,
> and no account-level permissions. No webhook is configured.

**Secrets**: what's in env, what's gitignored:
> `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` are read from the environment
> only, via `os.environ` in [config.py:34-40](github_mcp/config.py#L34), with
> `python-dotenv` loading a repo-root `.env` for convenience. No credential has
> ever been in a commit — the committed artifacts are
> [week2/.env.example](.env.example) and
> [week2/.mcp.json.example](.mcp.json.example), both placeholders.
>
> `.gitignore` covers `.env`, `.mcp.json`, `.cursor/mcp.json`, `week2/.mcp.json`
> and `token.json`. The token cache additionally lives under `$HOME`, not in
> the tree, so `git add -A` cannot reach it. `week2/.mcp.json.example` carries
> no `env` block for the secrets at all; the server loads `.env` itself, which
> removes the temptation to paste a client secret into an editor config.

**Token dies mid-session**: what the agent sees:
> The server never opens a browser during a tool call — that is the whole
> reason `login` is a separate command. When the token is gone, expired beyond
> refresh, or revoked, `get_valid_token()` raises `AuthRequired`, which
> [github_client.py:134-138](github_mcp/github_client.py#L134) converts into
> the same structured error shape as everything else:
>
> ```json
> {
>   "error": "GitHub rejected the access token: Bad credentials",
>   "kind": "auth_required",
>   "retryable": false,
>   "hint": "The cached token was revoked or is invalid. Run: python -m week2.github_mcp.auth login"
> }
> ```
>
> `retryable: false` stops the agent from looping, and the hint names the exact
> command for the human to run. Three tests cover the three ways this happens:
> no cached token, a live 401 from GitHub, and a refresh token GitHub rejects.


## Part IV: Integration

**Registration config** (`.mcp.json.example`) and the client you used:
> Cursor, via a project-local `.cursor/mcp.json` (gitignored). The committed
> template is [week2/.mcp.json.example](.mcp.json.example):
>
> ```json
> {
>   "mcpServers": {
>     "github-issues": {
>       "command": "/ABSOLUTE/PATH/TO/python",
>       "args": ["-m", "week2.github_mcp.server"],
>       "env": { "PYTHONPATH": "/ABSOLUTE/PATH/TO/modern-software-dev-assignments" }
>     }
>   }
> }
> ```
>
> `PYTHONPATH` is the only environment entry, because the client has no business
> holding credentials; the server reads `.env` at import time.

**End-to-end transcript**: the prompt, the tools that fired with their arguments, the result:
```
PROMPT (Cursor chat, github-issues server enabled):
  "My GitHub repo for this class is named cs146s-assignment. Find it, check
   whether there's already an open issue tracking the week 2 MCP server work,
   and if there isn't, file one titled 'Week 2: GitHub MCP server' with a short
   body listing the five tools the server exposes. Show me the preview before
   you create anything."

-> search_repos(query="cs146s-assignment user:xuanzhuoliu", limit=5)
<- {"total_count":0,"results":[],"note":"No matches. GitHub's search index only
    covers public repositories, so a private repo will not appear here even
    though you can read it. If you already know the 'owner/name', pass it
    straight to list_issues."}

   The repo is private, so search genuinely cannot see it. Without the note this
   reads as "no such repo" and the chain dies here; with it, the agent builds
   the slug from the owner it already knows and keeps going.

-> list_issues(repo="xuanzhuoliu/cs146s-assignment", state="all", limit=10)
<- {"repo":"xuanzhuoliu/cs146s-assignment","state":"all","issues":[]}

   Confirms the repo is reachable (resolving the ambiguity the empty search
   left) and that no tracking issue exists, so the "file one" branch applies.

-> create_issue(repo="xuanzhuoliu/cs146s-assignment",
                title="Week 2: GitHub MCP server",
                body="Tracking the week 2 assignment: an MCP server over stdio
                      exposing GitHub issues.\n\nTools exposed:\n\n- `whoami`
                      (read) ... - `create_issue` (write) - files an issue;
                      previews unless `dry_run=false`\n\nAuth is a GitHub App
                      authorization-code flow with a cached, silently refreshed
                      user token.")
   [dry_run not passed, so it defaults to true]
<- {"dry_run":true,"created":false,
    "would_create":{"repo":"xuanzhuoliu/cs146s-assignment",
                    "title":"Week 2: GitHub MCP server","body":"..."},
    "next_step":"Repeat this call with dry_run=false to actually create the issue."}

   Nothing created. Preview shown to the user; approval given.

-> create_issue(repo="xuanzhuoliu/cs146s-assignment",
                title="Week 2: GitHub MCP server", body="...", dry_run=false)
<- {"dry_run":false,"created":true,
    "issue":{"number":1,"title":"Week 2: GitHub MCP server","state":"open",
             "author":"xuanzhuoliu","labels":[],"comments":0,
             "created_at":"2026-10-05T03:58:50Z",
             "updated_at":"2026-10-05T03:58:50Z",
             "url":"https://github.com/xuanzhuoliu/cs146s-assignment/issues/1",
             "repo":"xuanzhuoliu/cs146s-assignment"}}

-> get_issue(repo="xuanzhuoliu/cs146s-assignment", issue_number=1)
<- {"number":1,"title":"Week 2: GitHub MCP server","state":"open",
    "author":"xuanzhuoliu","labels":[],"comments":0,
    "created_at":"2026-10-05T03:58:50Z","updated_at":"2026-10-05T03:58:50Z",
    "url":"https://github.com/xuanzhuoliu/cs146s-assignment/issues/1",
    "repo":"xuanzhuoliu/cs146s-assignment",
    "body":"Tracking the week 2 assignment: ...","body_truncated":false}

RESULT: Issue #1 "Week 2: GitHub MCP server" now exists at
https://github.com/xuanzhuoliu/cs146s-assignment/issues/1. Four distinct tools
fired, and three of the four consumed an identifier produced by an earlier
step: the `owner/name` slug threaded from the search stage into `list_issues`
and both `create_issue` calls, and `number: 1` came out of the write and went
straight back into `get_issue`.
```

**A failure, handled**: what you provoked, what the agent saw, what it did next:
```
FAILURE 1 - an issue number that does not exist (provoked)

-> get_issue(repo="xuanzhuoliu/cs146s-assignment", issue_number=99999)
<- {"error":"not found: Not Found","kind":"not_found","retryable":false,
    "hint":"Check the identifier. Repos come from search_repos; issue numbers
            come from list_issues."}

AGENT NEXT STEP: did not retry. `retryable: false` says the argument is wrong,
not the moment, so repeating the call unchanged can only fail again. The hint
names where a valid number comes from, so the recovery is `list_issues` on the
same repo and picking a real number — which is a different call, not a retry.
Note `is_error` is false at the protocol level: this arrived as a result the
agent could read and reason about, not an exception that would have ended the
turn.


FAILURE 2 - owner prefix omitted (provoked; never reaches GitHub)

-> list_issues(repo="cs146s-assignment")
<- 1 validation error for call[list_issues]
   repo
     String should match pattern '^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$'
     [type=string_pattern_mismatch, input_value='cs146s-assignment',
      input_type=str]

AGENT NEXT STEP: fixed the argument and called
list_issues(repo="xuanzhuoliu/cs146s-assignment"). The error names the rejected
value and the exact shape required, which is enough to repair without guessing.
This is the payoff from putting the constraint in the schema: no HTTP request
was made, no rate-limit budget spent, and the agent was not left interpreting a
generic 404 from GitHub.


FAILURE 3 - not provoked; this one actually happened

-> create_issue(repo="xuanzhuoliu/cs146s-assignment", title="Week 2: GitHub MCP
                server", body="...", dry_run=false)
<- {"error":"unexpected GitHub response (HTTP 410): Issues has been disabled in
             this repository.","kind":"upstream","retryable":true}

AGENT NEXT STEP: this is the response that exposed the bug described in Part II.
The message was accurate but the metadata was a lie - 410 is permanent, and
`retryable: true` invited an unbounded retry loop. I stopped, enabled Issues on
the repository, and changed the mapping. The same call against the fixed server
now returns:

   {"error":"this repository does not accept the request: Issues has been
             disabled in this repository.","kind":"unavailable",
    "retryable":false,
    "hint":"Issues are turned off for this repository. Enable them in the
            repository's Settings -> Features, or use a different repository."}

which an agent can act on: stop, and tell the human which switch to flip.
```

**Protocol-level test**: what it covers and how to run it:
> [week2/tests/test_protocol.py](tests/test_protocol.py) — 18 tests, run with:
>
> ```
> python -m pytest week2/tests -q
> ```
>
> Every test drives the server through `fastmcp.Client`, i.e. real MCP
> `tools/list` and `tools/call` traffic against the server object, so tool
> registration, JSON-Schema validation, annotation serialisation and result
> encoding are all exercised. Calling the Python functions directly would skip
> exactly the layer that breaks. GitHub is mocked with `respx`, so the suite
> needs no network and no credentials. Coverage:
>
> - **Catalog**: the advertised schemas really do carry the `state` enum, the
>   `owner/name` pattern, `limit`'s bounds, and `dry_run: true` as the default;
>   `readOnlyHint` is true on the four readers and false on `create_issue`.
> - **Chaining**: `search_repos -> list_issues -> get_issue` where each call's
>   arguments come from the previous call's output, asserting PRs are filtered
>   and bodies truncate at 4000 characters.
> - **The brake**: a default `create_issue` call issues zero POSTs; the same
>   call with `dry_run=false` issues exactly one.
> - **Errors as data**: 404 yields `kind="not_found"`/`retryable=false` with
>   `is_error` false at the protocol level; a 403 with `X-RateLimit-Remaining: 0`
>   yields `retryable=true` and a computed `retry_after`.
> - **Regressions from live integration**: 410 (issues disabled) is
>   `unavailable`/non-retryable; an unrecognised status defaults to
>   non-retryable; a 301 from a renamed repository is followed; an unexpected
>   payload shape becomes an error rather than a crash; an empty search carries
>   its explanatory `note`.
> - **Schema enforcement**: `repo="not-a-slug"` is rejected by validation, never
>   reaching GitHub.
> - **OAuth**: an expired access token is refreshed silently mid-call, the
>   request carries the *new* bearer token, and the rotated refresh token is
>   persisted; a rejected refresh becomes an `auth_required` error naming the
>   login command; the cache file is mode 0600.


## Submission
1. `Command (⌘) + F` for `TODO`. No results means you're done.
2. Confirm no tokens, client secrets, cached token file, or real `.mcp.json` are committed.
3. Push all changes to your remote repository and submit via Gradescope.
4. Clean up (optional): remove the server from your agent config, delete your cached token, and revoke the OAuth app's access.
