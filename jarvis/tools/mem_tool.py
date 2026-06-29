"""
Mem.ai tools — read and save notes in Eduardo's Mem workspace.
"""

import os
import httpx
from tools import tool

BASE = "https://api.mem.ai/v0"


def _headers() -> dict:
    key = os.environ.get("MEM_API_KEY")
    if not key:
        raise EnvironmentError("MEM_API_KEY not set in jarvis/.env")
    return {"Authorization": f"ApiAccessToken {key}", "Content-Type": "application/json"}


@tool(
    name="search_mem",
    description=(
        "Search Eduardo's Mem notes and return matching content. "
        "Use this when Eduardo asks questions about his notes, ideas, or anything he's saved in Mem."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "What to search for in Mem",
            },
        },
        "required": ["query"],
    },
)
def search_mem(query: str) -> str:
    r = httpx.post(
        f"{BASE}/mems/search",
        headers=_headers(),
        json={"query": query},
        timeout=20,
    )
    if r.status_code != 200:
        return f"Mem search error {r.status_code}: {r.text[:200]}"

    results = r.json().get("mems", [])
    if not results:
        return "No matching notes found in Mem."

    lines = []
    for m in results[:5]:
        content = m.get("content", "").strip()[:300]
        lines.append(f"---\n{content}")
    return "\n".join(lines)


@tool(
    name="save_to_mem",
    description=(
        "Save a new note to Eduardo's Mem workspace. "
        "Use this when Eduardo wants to capture an idea, thought, or piece of information in Mem."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The note content to save",
            },
        },
        "required": ["content"],
    },
)
def save_to_mem(content: str) -> str:
    r = httpx.post(
        f"{BASE}/mems",
        headers=_headers(),
        json={"content": content},
        timeout=20,
    )
    if r.status_code in (200, 201):
        return "Saved to Mem."
    return f"Mem save error {r.status_code}: {r.text[:200]}"


@tool(
    name="list_mem_notes",
    description="List Eduardo's most recent notes from Mem.",
    input_schema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "How many recent notes to return (default 10)",
            },
        },
        "required": [],
    },
)
def list_mem_notes(limit: int = 10) -> str:
    r = httpx.get(
        f"{BASE}/mems",
        headers=_headers(),
        params={"limit": limit},
        timeout=20,
    )
    if r.status_code != 200:
        return f"Mem error {r.status_code}: {r.text[:200]}"

    mems = r.json().get("mems", [])
    if not mems:
        return "No notes found in Mem."

    lines = []
    for m in mems:
        snippet = m.get("content", "").strip().split("\n")[0][:120]
        lines.append(f"• {snippet}")
    return "\n".join(lines)
