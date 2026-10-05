"""OAuth 2.0 authorization-code flow for a GitHub App's user-to-server tokens.

Two halves, deliberately separated:

* `login()` runs from a terminal. It opens a browser, catches the redirect on
  127.0.0.1, exchanges the code, and writes the token cache.
* `get_valid_token()` runs inside the MCP server. It only ever reads the cache
  and refreshes silently. It never opens a browser, because a long-running
  stdio server has no business hijacking the user's screen mid tool call. When
  it can't produce a token it raises `AuthRequired`, which tools turn into a
  structured error telling the human which command to run.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import threading
import time
import urllib.parse
import webbrowser
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx

from . import config


class AuthRequired(Exception):
    """Raised when no usable token can be produced without human interaction."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint or "Run: python -m week2.github_mcp.auth login"


@dataclass
class TokenBundle:
    access_token: str
    # None means the GitHub App was configured without expiring user tokens.
    expires_at: float | None = None
    refresh_token: str | None = None
    refresh_token_expires_at: float | None = None

    @property
    def needs_refresh(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at - config.REFRESH_SKEW_SECONDS

    @property
    def refresh_token_expired(self) -> bool:
        if self.refresh_token_expires_at is None:
            return False
        return time.time() >= self.refresh_token_expires_at


def _bundle_from_response(payload: dict) -> TokenBundle:
    now = time.time()
    expires_in = payload.get("expires_in")
    refresh_expires_in = payload.get("refresh_token_expires_in")
    return TokenBundle(
        access_token=payload["access_token"],
        expires_at=now + float(expires_in) if expires_in else None,
        refresh_token=payload.get("refresh_token"),
        refresh_token_expires_at=now + float(refresh_expires_in) if refresh_expires_in else None,
    )


def load_tokens() -> TokenBundle | None:
    path = config.token_path()
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text())
        return TokenBundle(**raw)
    except (json.JSONDecodeError, TypeError, KeyError):
        return None


def save_tokens(bundle: TokenBundle) -> None:
    path = config.token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Create with 0600 before writing so the token is never briefly world-readable.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        json.dump(asdict(bundle), fh)


def clear_tokens() -> bool:
    path = config.token_path()
    if path.exists():
        path.unlink()
        return True
    return False


def _require_app_credentials() -> tuple[str, str]:
    cid, secret = config.client_id(), config.client_secret()
    if not cid or not secret:
        raise AuthRequired(
            "GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET are not set",
            hint="Copy week2/.env.example to .env at the repo root and fill in your GitHub App credentials.",
        )
    return cid, secret


def _post_token_endpoint(data: dict[str, str]) -> dict:
    """POST to GitHub's token endpoint and normalise its two failure styles."""
    try:
        response = httpx.post(
            config.GITHUB_OAUTH_TOKEN_URL,
            data=data,
            headers={"Accept": "application/json"},
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        raise AuthRequired(
            f"could not reach GitHub's token endpoint: {exc}",
            hint="Check network connectivity, then retry.",
        ) from exc

    if response.status_code >= 400:
        raise AuthRequired(f"token endpoint returned HTTP {response.status_code}")

    payload = response.json()
    # GitHub reports OAuth failures with HTTP 200 and an `error` key.
    if "error" in payload:
        raise AuthRequired(
            f"{payload['error']}: {payload.get('error_description', 'no description')}"
        )
    if "access_token" not in payload:
        raise AuthRequired("token endpoint response contained no access_token")
    return payload


def refresh(bundle: TokenBundle) -> TokenBundle:
    """Trade a refresh token for a fresh access token and persist the result."""
    if not bundle.refresh_token:
        raise AuthRequired(
            "access token expired and the app issued no refresh token",
            hint="Enable expiring user tokens on the GitHub App, then run the login command again.",
        )
    if bundle.refresh_token_expired:
        raise AuthRequired("refresh token itself has expired")

    cid, secret = _require_app_credentials()
    payload = _post_token_endpoint(
        {
            "client_id": cid,
            "client_secret": secret,
            "grant_type": "refresh_token",
            "refresh_token": bundle.refresh_token,
        }
    )
    refreshed = _bundle_from_response(payload)
    save_tokens(refreshed)
    return refreshed


def get_valid_token() -> str:
    """Return a usable access token, refreshing silently if needed.

    Raises `AuthRequired` rather than prompting; the caller is a server.
    """
    bundle = load_tokens()
    if bundle is None:
        raise AuthRequired("no cached GitHub token")
    if bundle.needs_refresh:
        bundle = refresh(bundle)
    return bundle.access_token


class _CallbackHandler(BaseHTTPRequestHandler):
    """Single-shot handler that records the OAuth redirect's query string."""

    result: dict[str, str] = {}

    def do_GET(self) -> None:  # noqa: N802 - name fixed by BaseHTTPRequestHandler
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        query = {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}
        _CallbackHandler.result = query
        body = (
            b"<html><body><h2>GitHub authorization received.</h2>"
            b"<p>You can close this tab and return to your terminal.</p></body></html>"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:
        pass


def login(timeout_seconds: int = 180) -> TokenBundle:
    """Run the interactive authorization-code flow and cache the result."""
    cid, secret = _require_app_credentials()
    state = secrets.token_urlsafe(24)

    _CallbackHandler.result = {}
    server = HTTPServer(("127.0.0.1", config.callback_port()), _CallbackHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    authorize_url = (
        config.GITHUB_OAUTH_AUTHORIZE_URL
        + "?"
        + urllib.parse.urlencode(
            {"client_id": cid, "redirect_uri": config.callback_url(), "state": state}
        )
    )
    print(f"Opening browser for GitHub authorization:\n  {authorize_url}\n")
    webbrowser.open(authorize_url)

    deadline = time.time() + timeout_seconds
    try:
        while not _CallbackHandler.result and time.time() < deadline:
            time.sleep(0.2)
    finally:
        server.shutdown()
        server.server_close()

    query = _CallbackHandler.result
    if not query:
        raise AuthRequired(f"no OAuth callback received within {timeout_seconds}s")
    if "error" in query:
        raise AuthRequired(f"{query['error']}: {query.get('error_description', '')}")
    # Guards against a third party tricking the local listener into exchanging
    # a code the user never authorized.
    if query.get("state") != state:
        raise AuthRequired("OAuth state mismatch; aborting the code exchange")
    if "code" not in query:
        raise AuthRequired("OAuth callback contained no authorization code")

    payload = _post_token_endpoint(
        {
            "client_id": cid,
            "client_secret": secret,
            "code": query["code"],
            "redirect_uri": config.callback_url(),
        }
    )
    bundle = _bundle_from_response(payload)
    save_tokens(bundle)
    return bundle


def _describe(bundle: TokenBundle | None) -> str:
    if bundle is None:
        return "no cached token"
    if bundle.expires_at is None:
        return "token cached (non-expiring)"
    remaining = int(bundle.expires_at - time.time())
    state = f"expires in {remaining}s" if remaining > 0 else f"expired {-remaining}s ago"
    refreshable = "yes" if bundle.refresh_token else "no"
    return f"token cached, {state}, refreshable: {refreshable}"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    command = argv[0] if argv else "status"

    if command == "login":
        bundle = login()
        print(f"Authorized. {_describe(bundle)}")
        print(f"Cached at {config.token_path()}")
        return 0
    if command == "logout":
        print("Deleted cached token." if clear_tokens() else "Nothing to delete.")
        return 0
    if command == "status":
        print(_describe(load_tokens()))
        print(f"Cache path: {config.token_path()}")
        return 0
    if command == "refresh":
        bundle = load_tokens()
        if bundle is None:
            raise AuthRequired("no cached GitHub token")
        print(f"Refreshed. {_describe(refresh(bundle))}")
        return 0

    print("usage: python -m week2.github_mcp.auth [login|logout|status|refresh]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuthRequired as exc:
        print(f"error: {exc.message}\nhint: {exc.hint}", file=sys.stderr)
        raise SystemExit(1) from exc
