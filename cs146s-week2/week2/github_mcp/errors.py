"""Structured errors.

Every failure an agent can see is a plain dict with a stable shape. The agent
needs to answer one question from it: should I retry, fix my arguments, or stop
and tell the human? `kind` and `retryable` answer that without parsing prose.
"""

from __future__ import annotations

from typing import Any, Literal

ErrorKind = Literal[
    "auth_required",  # human must re-run the login command; do not retry
    "forbidden",  # token is valid but lacks permission on this resource
    "not_found",  # bad id/repo; fix the argument, do not retry as-is
    "validation",  # arguments rejected by GitHub; fix and retry
    "unavailable",  # permanently impossible here (e.g. issues disabled); change target
    "rate_limited",  # retry after `retry_after` seconds
    "network",  # transient transport failure; retry
    "upstream",  # GitHub 5xx; retry
]

_RETRYABLE: dict[str, bool] = {
    "auth_required": False,
    "forbidden": False,
    "not_found": False,
    "validation": False,
    "unavailable": False,
    "rate_limited": True,
    "network": True,
    "upstream": True,
}


def error(
    kind: ErrorKind,
    message: str,
    *,
    hint: str | None = None,
    retry_after: int | None = None,
) -> dict[str, Any]:
    """Build the error payload that tools return in place of a result."""
    payload: dict[str, Any] = {
        "error": message,
        "kind": kind,
        "retryable": _RETRYABLE[kind],
    }
    if retry_after is not None:
        payload["retry_after"] = retry_after
    if hint:
        payload["hint"] = hint
    return payload
