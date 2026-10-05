"""Protocol-level tests.

Everything here goes through an in-memory MCP client talking to the real
server object, so tool registration, JSON-schema validation, annotations and
result serialisation are all exercised. Calling the Python functions directly
would skip exactly the layer that breaks in practice.

GitHub itself is mocked with respx; no network, no credentials.
"""

from __future__ import annotations

import json
import time

import httpx
import pytest
import respx
from fastmcp import Client
from fastmcp.exceptions import ToolError

from week2.github_mcp import auth, config
from week2.github_mcp.server import mcp

API = config.GITHUB_API_BASE


@pytest.fixture
def token_file(tmp_path, monkeypatch):
    """A cached, still-valid token so tools get past the auth gate."""
    path = tmp_path / "token.json"
    monkeypatch.setenv("GITHUB_MCP_TOKEN_PATH", str(path))
    auth.save_tokens(
        auth.TokenBundle(
            access_token="ghu_test_access",
            expires_at=time.time() + 3600,
            refresh_token="ghr_test_refresh",
            refresh_token_expires_at=time.time() + 86400,
        )
    )
    return path


@pytest.fixture
def no_token(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_MCP_TOKEN_PATH", str(tmp_path / "missing.json"))


def repo_payload(full_name: str) -> dict:
    owner, name = full_name.split("/")
    return {
        "full_name": full_name,
        "name": name,
        "owner": {"login": owner},
        "description": "a repo",
        "stargazers_count": 42,
        "language": "Python",
        "open_issues_count": 3,
        "pushed_at": "2026-09-01T00:00:00Z",
        "html_url": f"https://github.com/{full_name}",
        "id": 1,
        "node_id": "ignored",
    }


def issue_payload(number: int, *, body: str = "details", pull_request: bool = False) -> dict:
    raw = {
        "number": number,
        "title": f"issue {number}",
        "state": "open",
        "user": {"login": "octocat"},
        "labels": [{"name": "bug"}],
        "comments": 2,
        "created_at": "2026-09-01T00:00:00Z",
        "updated_at": "2026-09-02T00:00:00Z",
        "html_url": f"https://github.com/octo/widget/issues/{number}",
        "body": body,
    }
    if pull_request:
        raw["pull_request"] = {"url": "..."}
    return raw


async def test_tool_catalog_exposes_constraints_and_annotations():
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    assert {"whoami", "search_repos", "list_issues", "get_issue", "create_issue"} <= set(tools)

    for name in ("whoami", "search_repos", "list_issues", "get_issue"):
        assert tools[name].annotations.read_only_hint is True, name
    assert tools["create_issue"].annotations.read_only_hint is False

    # Legal values are in the schema, so a bad value fails validation rather
    # than reaching GitHub.
    assert tools["list_issues"].input_schema["properties"]["state"]["enum"] == [
        "open",
        "closed",
        "all",
    ]
    assert "pattern" in tools["list_issues"].input_schema["properties"]["repo"]
    assert tools["search_repos"].input_schema["properties"]["limit"]["maximum"] == 20

    # The write tool is safe by default.
    assert tools["create_issue"].input_schema["properties"]["dry_run"]["default"] is True


async def test_server_instructions_describe_the_chain():
    async with Client(mcp) as client:
        await client.list_tools()  # forces protocol negotiation
        instructions = client.instructions
    assert "search_repos" in instructions
    assert "dry_run=false" in instructions


@respx.mock
async def test_chained_search_then_list_then_get(token_file):
    respx.get(f"{API}/search/repositories").mock(
        return_value=httpx.Response(
            200, json={"total_count": 1, "items": [repo_payload("octo/widget")]}
        )
    )
    respx.get(f"{API}/repos/octo/widget/issues").mock(
        return_value=httpx.Response(
            200,
            json=[issue_payload(7), issue_payload(8, pull_request=True)],
        )
    )
    respx.get(f"{API}/repos/octo/widget/issues/7").mock(
        return_value=httpx.Response(200, json=issue_payload(7, body="x" * 5000))
    )

    async with Client(mcp) as client:
        found = (await client.call_tool("search_repos", {"query": "widget"})).data
        repo = found["results"][0]["full_name"]

        listed = (await client.call_tool("list_issues", {"repo": repo})).data
        numbers = [issue["number"] for issue in listed["issues"]]

        detail = (
            await client.call_tool("get_issue", {"repo": repo, "issue_number": numbers[0]})
        ).data

    assert repo == "octo/widget"
    # Pull requests are filtered out of list_issues.
    assert numbers == [7]
    assert detail["number"] == 7
    assert detail["body_truncated"] is True
    assert len(detail["body"]) == 4000
    # Output is shaped, not passed through.
    assert "node_id" not in found["results"][0]


@respx.mock
async def test_create_issue_previews_before_it_writes(token_file):
    route = respx.post(f"{API}/repos/octo/widget/issues").mock(
        return_value=httpx.Response(201, json=issue_payload(9))
    )

    async with Client(mcp) as client:
        preview = (
            await client.call_tool(
                "create_issue", {"repo": "octo/widget", "title": "Flaky test", "body": "steps"}
            )
        ).data
        assert preview["created"] is False
        assert route.call_count == 0

        committed = (
            await client.call_tool(
                "create_issue",
                {
                    "repo": "octo/widget",
                    "title": "Flaky test",
                    "body": "steps",
                    "dry_run": False,
                },
            )
        ).data

    assert route.call_count == 1
    assert committed["created"] is True
    assert committed["issue"]["number"] == 9
    assert json.loads(route.calls[0].request.content)["title"] == "Flaky test"


@respx.mock
async def test_renamed_repo_redirect_is_followed(token_file):
    """GitHub 301s renamed repos; the redirect body is not an issue list."""
    respx.get(f"{API}/repos/olduser/widget/issues").mock(
        return_value=httpx.Response(
            301, headers={"Location": f"{API}/repositories/1/issues"}, json={"message": "Moved"}
        )
    )
    respx.get(f"{API}/repositories/1/issues").mock(
        return_value=httpx.Response(200, json=[issue_payload(7)])
    )

    async with Client(mcp) as client:
        result = (await client.call_tool("list_issues", {"repo": "olduser/widget"})).data

    assert [issue["number"] for issue in result["issues"]] == [7]


@respx.mock
async def test_unexpected_payload_shape_is_an_error_not_a_crash(token_file):
    respx.get(f"{API}/repos/octo/widget/issues").mock(
        return_value=httpx.Response(200, json={"message": "not a list"})
    )
    async with Client(mcp) as client:
        result = await client.call_tool("list_issues", {"repo": "octo/widget"})

    assert result.is_error is False
    assert result.data["kind"] == "upstream"


async def test_bad_repo_slug_is_rejected_by_the_schema(token_file):
    async with Client(mcp) as client:
        result = await client.call_tool("list_issues", {"repo": "not-a-slug"}, raise_on_error=False)
    assert result.is_error
    assert "pattern" in str(result.content[0].text).lower()


@respx.mock
async def test_not_found_is_data_and_not_retryable(token_file):
    respx.get(f"{API}/repos/octo/widget/issues/404").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_issue", {"repo": "octo/widget", "issue_number": 404})
    assert result.is_error is False  # an error the agent can read, not a crash
    assert result.data["kind"] == "not_found"
    assert result.data["retryable"] is False
    assert "list_issues" in result.data["hint"]


@respx.mock
async def test_rate_limit_tells_the_agent_when_to_retry(token_file):
    reset_at = int(time.time()) + 42
    respx.get(f"{API}/search/repositories").mock(
        return_value=httpx.Response(
            403,
            json={"message": "API rate limit exceeded"},
            headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(reset_at)},
        )
    )
    async with Client(mcp) as client:
        result = (await client.call_tool("search_repos", {"query": "widget"})).data

    assert result["kind"] == "rate_limited"
    assert result["retryable"] is True
    assert 35 <= result["retry_after"] <= 42


@respx.mock
async def test_disabled_issues_is_permanent_not_retryable(token_file):
    """A repo with the Issues feature turned off answers 410, forever."""
    respx.post(f"{API}/repos/octo/widget/issues").mock(
        return_value=httpx.Response(
            410, json={"message": "Issues has been disabled in this repository."}
        )
    )
    async with Client(mcp) as client:
        result = (
            await client.call_tool(
                "create_issue",
                {"repo": "octo/widget", "title": "x", "dry_run": False},
            )
        ).data

    assert result["kind"] == "unavailable"
    assert result["retryable"] is False
    assert "Settings" in result["hint"]


@respx.mock
async def test_unrecognised_status_defaults_to_not_retryable(token_file):
    respx.get(f"{API}/user").mock(return_value=httpx.Response(418, json={"message": "teapot"}))
    async with Client(mcp) as client:
        result = (await client.call_tool("whoami", {})).data
    assert result["retryable"] is False


@respx.mock
async def test_empty_search_explains_itself(token_file):
    respx.get(f"{API}/search/repositories").mock(
        return_value=httpx.Response(200, json={"total_count": 0, "items": []})
    )
    async with Client(mcp) as client:
        result = (await client.call_tool("search_repos", {"query": "nothing"})).data

    assert result["results"] == []
    # Without this, an agent reads "no results" as "no such repository".
    assert "private" in result["note"]
    assert "list_issues" in result["note"]


@respx.mock
async def test_revoked_token_mid_session_asks_the_human(token_file):
    respx.get(f"{API}/user").mock(
        return_value=httpx.Response(401, json={"message": "Bad credentials"})
    )
    async with Client(mcp) as client:
        result = (await client.call_tool("whoami", {})).data

    assert result["kind"] == "auth_required"
    assert result["retryable"] is False
    assert "auth login" in result["hint"]


async def test_missing_token_never_opens_a_browser(no_token):
    async with Client(mcp) as client:
        result = (await client.call_tool("whoami", {})).data
    assert result["kind"] == "auth_required"
    assert "no cached GitHub token" in result["error"]


@respx.mock
async def test_expired_access_token_is_refreshed_silently(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_MCP_TOKEN_PATH", str(tmp_path / "token.json"))
    monkeypatch.setenv("GITHUB_CLIENT_ID", "Iv1.test")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test-secret")
    auth.save_tokens(
        auth.TokenBundle(
            access_token="ghu_expired",
            expires_at=time.time() - 10,
            refresh_token="ghr_test_refresh",
            refresh_token_expires_at=time.time() + 86400,
        )
    )

    token_route = respx.post(config.GITHUB_OAUTH_TOKEN_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "ghu_fresh",
                "expires_in": 28800,
                "refresh_token": "ghr_next",
                "refresh_token_expires_in": 15897600,
            },
        )
    )
    user_route = respx.get(f"{API}/user").mock(
        return_value=httpx.Response(200, json={"login": "octocat", "name": "Octo"})
    )

    async with Client(mcp) as client:
        result = (await client.call_tool("whoami", {})).data

    assert result["login"] == "octocat"
    assert token_route.call_count == 1
    assert user_route.calls[0].request.headers["authorization"] == "Bearer ghu_fresh"
    # The rotated refresh token was persisted, so the next expiry also recovers.
    assert auth.load_tokens().refresh_token == "ghr_next"


@respx.mock
async def test_dead_refresh_token_becomes_an_actionable_error(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_MCP_TOKEN_PATH", str(tmp_path / "token.json"))
    monkeypatch.setenv("GITHUB_CLIENT_ID", "Iv1.test")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test-secret")
    auth.save_tokens(
        auth.TokenBundle(
            access_token="ghu_expired",
            expires_at=time.time() - 10,
            refresh_token="ghr_revoked",
            refresh_token_expires_at=time.time() + 86400,
        )
    )
    # GitHub reports this with HTTP 200 and an `error` key, not a 4xx.
    respx.post(config.GITHUB_OAUTH_TOKEN_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "error": "bad_refresh_token",
                "error_description": "The refresh token is incorrect",
            },
        )
    )

    async with Client(mcp) as client:
        result = (await client.call_tool("whoami", {})).data

    assert result["kind"] == "auth_required"
    assert result["retryable"] is False
    assert "python -m week2.github_mcp.auth login" in result["hint"]


def test_token_cache_is_not_world_readable(tmp_path, monkeypatch):
    path = tmp_path / "token.json"
    monkeypatch.setenv("GITHUB_MCP_TOKEN_PATH", str(path))
    auth.save_tokens(auth.TokenBundle(access_token="ghu_secret"))
    assert path.stat().st_mode & 0o077 == 0


def test_tool_error_import_is_available():
    # Guards the import used above if fastmcp reshuffles its exception module.
    assert issubclass(ToolError, Exception)
