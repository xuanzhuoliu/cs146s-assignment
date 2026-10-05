"""Thin async wrapper over the GitHub REST API.

The only job beyond "make the request" is translating every way GitHub can say
no into a `GitHubError` carrying an `ErrorKind`. Tools then render that as data
instead of letting an exception escape as a traceback.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from . import auth, config
from .auth import AuthRequired
from .errors import ErrorKind

_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "cs146s-week2-github-mcp",
}


class GitHubError(Exception):
    def __init__(
        self,
        kind: ErrorKind,
        message: str,
        *,
        hint: str | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message)
        self.kind: ErrorKind = kind
        self.message = message
        self.hint = hint
        self.retry_after = retry_after


def _retry_after_seconds(response: httpx.Response) -> int | None:
    raw = response.headers.get("retry-after")
    if raw and raw.isdigit():
        return int(raw)
    reset = response.headers.get("x-ratelimit-reset")
    if reset and reset.isdigit():
        return max(0, int(int(reset) - time.time()))
    return None


def _api_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text[:200] or f"HTTP {response.status_code}"
    if isinstance(body, dict):
        message = body.get("message") or f"HTTP {response.status_code}"
        errors = body.get("errors")
        if errors:
            details = "; ".join(
                e.get("message") or f"{e.get('field')}: {e.get('code')}"
                for e in errors
                if isinstance(e, dict)
            )
            if details:
                return f"{message} ({details})"
        return str(message)
    return f"HTTP {response.status_code}"


def _raise_for_response(response: httpx.Response) -> None:
    if response.status_code < 400:
        return

    status = response.status_code
    message = _api_message(response)

    if status == 401:
        raise GitHubError(
            "auth_required",
            f"GitHub rejected the access token: {message}",
            hint="The cached token was revoked or is invalid. Run: python -m week2.github_mcp.auth login",
        )
    if status in (403, 429):
        remaining = response.headers.get("x-ratelimit-remaining")
        retry_after = _retry_after_seconds(response)
        if status == 429 or remaining == "0":
            raise GitHubError(
                "rate_limited",
                f"rate limited by GitHub: {message}",
                hint=(
                    f"Wait {retry_after}s before retrying."
                    if retry_after is not None
                    else "Wait before retrying."
                ),
                retry_after=retry_after,
            )
        raise GitHubError(
            "forbidden",
            f"GitHub refused the request: {message}",
            hint="The GitHub App is probably not installed on this repository, or lacks the required permission.",
        )
    if status == 404:
        raise GitHubError(
            "not_found",
            f"not found: {message}",
            hint="Check the identifier. Repos come from search_repos; issue numbers come from list_issues.",
        )
    if status == 410:
        # Repositories can disable the Issues feature entirely. Permanent, so
        # the agent must change target rather than retry.
        raise GitHubError(
            "unavailable",
            f"this repository does not accept the request: {message}",
            hint="Issues are turned off for this repository. Enable them in the repository's Settings -> Features, or use a different repository.",
        )
    if status in (400, 422):
        raise GitHubError(
            "validation",
            f"GitHub rejected the arguments: {message}",
            hint="Fix the arguments named in the message and call again.",
        )
    if status >= 500:
        raise GitHubError(
            "upstream",
            f"GitHub server error (HTTP {status}): {message}",
            hint="Transient on GitHub's side; retry shortly.",
            retry_after=5,
        )
    # Any other 4xx is a client-side problem we haven't named. Defaulting an
    # unrecognised status to retryable invites an infinite loop, so don't.
    raise GitHubError(
        "unavailable",
        f"unexpected GitHub response (HTTP {status}): {message}",
        hint="Not a recognised transient failure; do not retry unchanged.",
    )


async def request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> Any:
    """Call the GitHub API with a valid token, or raise `GitHubError`."""
    try:
        token = await asyncio.to_thread(auth.get_valid_token)
    except AuthRequired as exc:
        raise GitHubError("auth_required", exc.message, hint=exc.hint) from exc

    headers = {**_HEADERS, "Authorization": f"Bearer {token}"}
    try:
        # GitHub answers 301 for repositories that have been renamed or whose
        # owner renamed their account. Without following it, the redirect body
        # comes back looking like a successful (but wrongly shaped) response.
        async with httpx.AsyncClient(
            base_url=config.GITHUB_API_BASE, timeout=20.0, follow_redirects=True
        ) as client:
            response = await client.request(method, path, params=params, json=json, headers=headers)
    except httpx.HTTPError as exc:
        raise GitHubError(
            "network",
            f"could not reach GitHub: {exc}",
            hint="Transient transport failure; retry.",
        ) from exc

    _raise_for_response(response)
    if response.status_code == 204 or not response.content:
        return None
    return response.json()
