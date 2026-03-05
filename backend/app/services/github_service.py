"""GitHub API interactions — OAuth flow, user info, repo listing."""

import httpx
import logging
from typing import Optional
from app.config import get_settings
from app.utils.audit import log_auth_event

settings = get_settings()
logger = logging.getLogger("codelens.github")

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"


def get_authorization_url(state: Optional[str] = None) -> str:
    """Build the GitHub OAuth authorization URL."""
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "read:user user:email repo",
    }
    if state:
        params["state"] = state
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GITHUB_AUTH_URL}?{query}"


async def exchange_code_for_token(code: str) -> str:
    """Exchange OAuth authorization code for an access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GITHUB_TOKEN_URL,
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            log_auth_event("github_token_error", details=data)
            raise ValueError(f"GitHub OAuth error: {data.get('error_description', data['error'])}")

        return data["access_token"]


async def get_user_info(access_token: str) -> dict:
    """Fetch authenticated user's profile from GitHub."""
    async with httpx.AsyncClient() as client:
        # Get profile
        response = await client.get(
            f"{GITHUB_API_URL}/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        profile = response.json()

        # Get primary email
        email_response = await client.get(
            f"{GITHUB_API_URL}/user/emails",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        emails = email_response.json() if email_response.status_code == 200 else []
        primary_email = next(
            (e["email"] for e in emails if e.get("primary") and e.get("verified")),
            profile.get("email"),
        )

        return {
            "github_id": str(profile["id"]),
            "username": profile["login"],
            "email": primary_email,
            "avatar_url": profile.get("avatar_url"),
            "name": profile.get("name"),
        }


async def list_user_repos(access_token: str, page: int = 1, per_page: int = 30) -> list[dict]:
    """List authenticated user's repositories from GitHub."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_URL}/user/repos",
            params={
                "sort": "updated",
                "direction": "desc",
                "page": page,
                "per_page": per_page,
                "type": "owner",
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        repos = response.json()

        return [
            {
                "name": r["name"],
                "full_name": r["full_name"],
                "url": r["html_url"],
                "description": r.get("description") or "",
                "language": r.get("language") or "",
                "stars": r.get("stargazers_count", 0),
            }
            for r in repos
        ]


async def get_repo_info(owner: str, repo: str, access_token: Optional[str] = None) -> dict:
    """Get info about a specific repository."""
    logger.info("🔍 Fetching repository info: %s/%s", owner, repo)
    headers = {"Accept": "application/vnd.github+json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        logger.info("✓ Repository info fetched: %s (language: %s, stars: %d)", 
                   data["full_name"], data.get("language", "unknown"), data.get("stargazers_count", 0))
        return {
            "name": data["name"],
            "full_name": data["full_name"],
            "description": data.get("description") or "",
            "language": data.get("language") or "",
            "star_count": data.get("stargazers_count", 0),
            "default_branch": data.get("default_branch", "main"),
        }


async def download_repo_tarball(owner: str, repo: str, branch: str = "main", access_token: Optional[str] = None) -> bytes:
    """Download repository as tarball."""
    logger.info("⬇️  Downloading tarball: %s/%s@%s", owner, repo, branch)
    headers = {"Accept": "application/vnd.github+json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/tarball/{branch}",
            headers=headers,
        )
        response.raise_for_status()
        tarball_size = len(response.content)
        logger.info("✓ Tarball downloaded: %.2f MB", tarball_size / (1024 * 1024))
        return response.content
