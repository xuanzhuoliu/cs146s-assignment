"""MCP server exposing a composable slice of GitHub issues.

Design notes for the reader (the agent only ever sees the schemas below):

* Argument domains live in the type annotations, not in prose, so an illegal
  value fails at validation with a message naming the legal set.
* Responses are hand-shaped. GitHub's issue payload is ~40 fields of URLs and
  mirror ids; almost none of it helps an agent decide what to do next.
* Failures return a dict from `errors.error(...)`, never an exception.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from . import errors
from .github_client import GitHubError, request

INSTRUCTIONS = """\
Read-and-write access to GitHub issues for repositories where the user has
installed this app.

Typical workflow:
  1. `search_repos` to turn a description into an `owner/name` string.
  2. `list_issues` on that repo to get issue numbers and titles.
  3. `get_issue` for the full body of a specific number.
  4. `create_issue` to file a new one. It previews by default; you must call it
     a second time with dry_run=false to actually create the issue, and you
     should show the preview to the user before you do.

Every tool returns either its documented result or an object with `error`,
`kind`, and `retryable`. When `retryable` is false, change the arguments or
stop and tell the user; do not call the same tool again unchanged. When `kind`
is "auth_required", the user must run the login command themselves; you cannot
fix it from here.
"""

mcp = FastMCP(name="github-issues", instructions=INSTRUCTIONS)

_READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=True)
_WRITE = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=False,
    open_world_hint=True,
)

RepoName = Annotated[
    str,
    Field(
        pattern=r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$",
        description="Repository as 'owner/name', e.g. 'pallets/flask'. Use the full_name returned by search_repos.",
    ),
]

BODY_PREVIEW_CHARS = 4000


def _as_error(exc: GitHubError) -> dict[str, Any]:
    return errors.error(exc.kind, exc.message, hint=exc.hint, retry_after=exc.retry_after)


def _shape_repo(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "full_name": raw["full_name"],
        "description": raw.get("description"),
        "stars": raw.get("stargazers_count"),
        "language": raw.get("language"),
        "open_issues": raw.get("open_issues_count"),
        "pushed_at": raw.get("pushed_at"),
        "url": raw.get("html_url"),
    }


def _shape_issue(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": raw["number"],
        "title": raw.get("title"),
        "state": raw.get("state"),
        "author": (raw.get("user") or {}).get("login"),
        "labels": [label["name"] for label in raw.get("labels", []) if isinstance(label, dict)],
        "comments": raw.get("comments"),
        "created_at": raw.get("created_at"),
        "updated_at": raw.get("updated_at"),
        "url": raw.get("html_url"),
    }


@mcp.tool(annotations=_READ_ONLY)
async def whoami() -> dict[str, Any]:
    """Return the GitHub account this server is authenticated as.

    Cheap way to confirm the cached token still works before a write. If this
    returns kind="auth_required", every other tool will fail the same way until
    the user re-authorizes.
    """
    try:
        user = await request("GET", "/user")
    except GitHubError as exc:
        return _as_error(exc)
    return {
        "login": user["login"],
        "name": user.get("name"),
        "account_url": user.get("html_url"),
    }


@mcp.tool(annotations=_READ_ONLY)
async def search_repos(
    query: Annotated[
        str,
        Field(
            min_length=1,
            description="GitHub search syntax, e.g. 'http client language:python' or 'user:octocat'.",
        ),
    ],
    sort: Literal["best-match", "stars", "forks", "updated"] = "best-match",
    limit: Annotated[int, Field(ge=1, le=20)] = 5,
) -> dict[str, Any]:
    """Find repositories matching a query.

    Returns `results`, each with a `full_name` ('owner/name') that `list_issues`
    and `create_issue` take as their `repo` argument. Start here when the user
    names a project in prose rather than as owner/name.

    Only public repositories are indexed. An empty `results` does not mean the
    repository is missing; if you can construct the `owner/name` yourself, pass
    it to `list_issues` directly rather than concluding it does not exist.
    """
    params: dict[str, Any] = {"q": query, "per_page": limit}
    if sort != "best-match":
        params["sort"] = sort
    try:
        payload = await request("GET", "/search/repositories", params=params)
    except GitHubError as exc:
        return _as_error(exc)

    items = payload.get("items", [])[:limit]
    result: dict[str, Any] = {
        "total_count": payload.get("total_count", 0),
        "results": [_shape_repo(item) for item in items],
    }
    if not items:
        # An empty list alone reads as "no such repository", which is wrong
        # often enough to mislead: GitHub's search index only covers public
        # repositories, so private ones the caller can read never appear here.
        result["note"] = (
            "No matches. GitHub's search index only covers public repositories, "
            "so a private repo will not appear here even though you can read it. "
            "If you already know the 'owner/name', pass it straight to list_issues."
        )
    return result


@mcp.tool(annotations=_READ_ONLY)
async def list_issues(
    repo: RepoName,
    state: Literal["open", "closed", "all"] = "open",
    sort: Literal["created", "updated", "comments"] = "created",
    direction: Literal["asc", "desc"] = "desc",
    labels: Annotated[
        list[str] | None,
        Field(description="Only issues carrying all of these labels."),
    ] = None,
    limit: Annotated[int, Field(ge=1, le=50)] = 10,
) -> dict[str, Any]:
    """List issues in a repository, newest first by default.

    `repo` is the `full_name` from `search_repos`. Each result's `number` is what
    `get_issue` and any follow-up work take as `issue_number`. Pull requests are
    filtered out, so counts here can be lower than `limit` even when more pages
    exist. Bodies are omitted; use `get_issue` for one.
    """
    params: dict[str, Any] = {
        "state": state,
        "sort": sort,
        "direction": direction,
        "per_page": limit,
    }
    if labels:
        params["labels"] = ",".join(labels)
    try:
        payload = await request("GET", f"/repos/{repo}/issues", params=params)
    except GitHubError as exc:
        return _as_error(exc)

    if not isinstance(payload, list):
        return errors.error(
            "upstream",
            "GitHub returned a non-list payload for the issues listing",
            hint="Confirm `repo` names a real repository; verify it with search_repos.",
        )

    # The issues endpoint returns PRs as well; they are never what the caller meant.
    issues = [item for item in payload if "pull_request" not in item][:limit]
    return {"repo": repo, "state": state, "issues": [_shape_issue(item) for item in issues]}


@mcp.tool(annotations=_READ_ONLY)
async def get_issue(
    repo: RepoName,
    issue_number: Annotated[
        int,
        Field(ge=1, description="The `number` field from a list_issues result."),
    ],
) -> dict[str, Any]:
    """Fetch one issue including its body.

    `issue_number` is the `number` from `list_issues` for the same `repo`, not a
    GitHub internal id and not a position in the list. Long bodies are cut at
    4000 characters with `body_truncated` set to true.
    """
    try:
        raw = await request("GET", f"/repos/{repo}/issues/{issue_number}")
    except GitHubError as exc:
        return _as_error(exc)

    body = raw.get("body") or ""
    shaped = _shape_issue(raw)
    shaped["repo"] = repo
    shaped["body"] = body[:BODY_PREVIEW_CHARS]
    shaped["body_truncated"] = len(body) > BODY_PREVIEW_CHARS
    return shaped


@mcp.tool(annotations=_WRITE)
async def create_issue(
    repo: RepoName,
    title: Annotated[str, Field(min_length=1, max_length=256)],
    body: Annotated[str, Field(max_length=60000)] = "",
    labels: Annotated[
        list[str] | None,
        Field(description="Labels must already exist in the repository."),
    ] = None,
    dry_run: Annotated[
        bool,
        Field(
            description="True (the default) returns a preview and creates nothing. Pass false only after the user has seen the preview and approved it."
        ),
    ] = True,
) -> dict[str, Any]:
    """Create an issue. Previews by default; creating requires a second call.

    This is the only tool here that changes real state, and the change is public
    and notifies watchers. With `dry_run=true` it returns `{"dry_run": true, ...}`
    describing exactly what would be filed and creates nothing. Show that to the
    user, get an explicit go-ahead, then repeat the identical call with
    `dry_run=false`; the response then carries `number` and `url`.

    `repo` is a `full_name` from `search_repos`. Check `list_issues` for a
    duplicate before filing.
    """
    payload: dict[str, Any] = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels

    if dry_run:
        return {
            "dry_run": True,
            "created": False,
            "would_create": {"repo": repo, **payload},
            "next_step": "Repeat this call with dry_run=false to actually create the issue.",
        }

    try:
        raw = await request("POST", f"/repos/{repo}/issues", json=payload)
    except GitHubError as exc:
        return _as_error(exc)

    shaped = _shape_issue(raw)
    shaped["repo"] = repo
    return {"dry_run": False, "created": True, "issue": shaped}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
