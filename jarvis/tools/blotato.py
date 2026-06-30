"""
Blotato social media tools.
Lets Jarvis post to LinkedIn, Instagram, Facebook, Twitter/X, etc.
"""

import os
import httpx
from tools import tool

BASE = "https://backend.blotato.com/v2"


def _headers() -> dict:
    key = os.environ.get("BLOTATO_API_KEY")
    if not key:
        raise EnvironmentError("BLOTATO_API_KEY not set in jarvis/.env")
    return {"blotato-api-key": key, "Content-Type": "application/json"}


def _get_accounts() -> list[dict]:
    r = httpx.get(f"{BASE}/accounts", headers=_headers(), timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"Blotato error {r.status_code}: {r.text[:200]}")
    return r.json()


@tool(
    name="post_to_social",
    description=(
        "Post content to Eduardo's social media accounts via Blotato. "
        "Specify which platforms (linkedin, instagram, facebook, twitter) or use 'all'. "
        "Optionally schedule with a datetime string like '2024-12-01T10:00:00'."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The post content",
            },
            "platforms": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Platforms: linkedin, instagram, facebook, twitter. Use ['all'] for all connected.",
            },
            "scheduled_time": {
                "type": "string",
                "description": "Optional ISO 8601 datetime to schedule. Leave blank to post immediately.",
            },
            "media_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional public image or video URLs to attach.",
            },
        },
        "required": ["text", "platforms"],
    },
)
def post_to_social(
    text: str,
    platforms: list,
    scheduled_time: str = "",
    media_urls: list = None,
) -> str:
    accounts = _get_accounts()
    if not accounts:
        return "No social media accounts connected in Blotato."

    post_all = "all" in [p.lower() for p in platforms]
    target_platforms = (
        {a["platform"].lower() for a in accounts}
        if post_all
        else {p.lower() for p in platforms}
    )

    results = []
    for account in accounts:
        platform = account["platform"].lower()
        if platform not in target_platforms:
            continue

        payload = {
            "accountId": account["id"],
            "platform": platform,
            "text": text,
            "mediaUrls": media_urls or [],
        }
        if scheduled_time:
            payload["scheduledTime"] = scheduled_time
        if platform == "facebook" and account.get("subaccounts"):
            payload["pageId"] = account["subaccounts"][0]["id"]
        if platform == "linkedin" and account.get("subaccounts"):
            payload["pageId"] = account["subaccounts"][0]["id"]

        r = httpx.post(f"{BASE}/posts", headers=_headers(), json=payload, timeout=30)
        if r.status_code in (200, 201):
            results.append(f"✓ {platform.capitalize()}: posted")
        else:
            results.append(f"✗ {platform.capitalize()}: {r.text[:100]}")

    if not results:
        return f"No matching accounts found for: {platforms}"
    return "\n".join(results)


@tool(
    name="list_social_accounts",
    description="List all social media accounts connected to Blotato.",
    input_schema={"type": "object", "properties": {}, "required": []},
)
def list_social_accounts() -> str:
    accounts = _get_accounts()
    if not accounts:
        return "No accounts connected in Blotato."
    lines = []
    for a in accounts:
        name = a.get("displayName") or a.get("username") or a["id"]
        lines.append(f"• {a['platform'].capitalize()}: {name}")
    return "\n".join(lines)
