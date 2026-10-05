"""Environment and filesystem configuration.

Everything secret is read from the environment. Nothing in this module may ever
hold a literal credential.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(REPO_ROOT / ".env")

GITHUB_API_BASE = "https://api.github.com"
GITHUB_OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"

# Tokens are cached outside the repository so a stray `git add .` can't leak them.
DEFAULT_TOKEN_PATH = Path.home() / ".config" / "cs146s-github-mcp" / "token.json"

# Refresh this many seconds before the access token actually expires, so a tool
# call that starts just under the wire doesn't fail mid-flight.
REFRESH_SKEW_SECONDS = 300


def client_id() -> str | None:
    return os.environ.get("GITHUB_CLIENT_ID") or None


def client_secret() -> str | None:
    return os.environ.get("GITHUB_CLIENT_SECRET") or None


def token_path() -> Path:
    override = os.environ.get("GITHUB_MCP_TOKEN_PATH")
    return Path(override).expanduser() if override else DEFAULT_TOKEN_PATH


def callback_port() -> int:
    return int(os.environ.get("GITHUB_MCP_CALLBACK_PORT", "8765"))


def callback_url() -> str:
    return f"http://127.0.0.1:{callback_port()}/callback"
