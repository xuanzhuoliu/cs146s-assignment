# github-issues MCP server

An MCP server over stdio that lets a coding agent search repositories, read
issues, and file new ones, authenticated as *you* through a GitHub App's
OAuth authorization-code flow.

## Setup

### 1. Create a GitHub App

<https://github.com/settings/apps/new>

| Field | Value |
|---|---|
| GitHub App name | anything unique, e.g. `cs146s-<yourname>-issues` |
| Homepage URL | your repo URL (unused) |
| Callback URL | `http://127.0.0.1:8765/callback` |
| Expire user authorization tokens | **checked** (this is what gives you refresh tokens) |
| Request user authorization (OAuth) during installation | checked |
| Webhook -> Active | **unchecked** |

Repository permissions, and nothing else:

| Permission | Level | Why |
|---|---|---|
| Metadata | Read-only | mandatory for any repo access; backs `search_repos` |
| Issues | Read and write | `list_issues` / `get_issue` read, `create_issue` writes |

Then **Install App** on your own account and limit it to the one or two
repositories you want the agent to touch. Generate a client secret on the
app's settings page.

### 2. Configure credentials

```bash
cp week2/.env.example .env     # from the repo root; .env is gitignored
$EDITOR .env                   # paste the client ID and client secret
```

### 3. Install dependencies

```bash
conda activate cs146s
poetry install --no-interaction
```

### 4. Authorize once

```bash
python -m week2.github_mcp.auth login
```

This opens a browser, catches the redirect on `127.0.0.1:8765`, exchanges the
code, and writes `~/.config/cs146s-github-mcp/token.json` with mode 0600.
`status`, `refresh`, and `logout` are the other subcommands.

### 5. Run the server

```bash
python -m week2.github_mcp.server
```

That is the whole command; it speaks MCP over stdio and exits when its client
does. For Cursor, copy `week2/.mcp.json.example` to `.cursor/mcp.json`
(gitignored) and replace both absolute paths — the `command` with
`$(conda run -n cs146s which python)` and `PYTHONPATH` with the repo root.

## Tools

| Tool | Kind | Takes | Gives |
|---|---|---|---|
| `whoami` | read | – | the authenticated login |
| `search_repos` | read | query, sort, limit | `full_name` values |
| `list_issues` | read | `repo` from `search_repos` | issue `number` values |
| `get_issue` | read | `repo` + `number` from `list_issues` | body and metadata |
| `create_issue` | **write** | `repo`, title, body, labels, `dry_run` | preview, or the created issue |

`create_issue` defaults to `dry_run=true`: it returns what it *would* file and
touches nothing. Only an explicit `dry_run=false` creates the issue.

## Tests

```bash
python -m pytest week2/tests -q
```

They drive the server through an in-memory MCP client (`fastmcp.Client`), so
schemas, annotations, and protocol-level error handling are all covered.
GitHub is mocked with `respx`; no network and no credentials needed.
