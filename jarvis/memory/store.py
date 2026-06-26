"""
Durable fact store — long-term memory that survives restarts.

Facts are plain JSON, one entry per line of reasoning, human-readable and
directly editable. Eduardo can open memory/facts.json, fix a wrong fact,
delete a stale one, or add one by hand — and Jarvis respects it on the next run.

Facts are loaded into the system prompt at the start of every conversation so
the model walks in already knowing them. They are treated as background
knowledge, never as commands.
"""

import json
import os
from datetime import datetime
from pathlib import Path

FACTS_FILE = Path(__file__).parent / "facts.json"


def _load() -> list[dict]:
    if not FACTS_FILE.exists():
        return []
    with open(FACTS_FILE) as f:
        return json.load(f)


def _save(facts: list[dict]) -> None:
    FACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FACTS_FILE, "w") as f:
        json.dump(facts, f, indent=2)


def load_facts() -> list[dict]:
    return _load()


def facts_as_prompt_block() -> str:
    """
    Return a compact string to inject into the system prompt.
    Empty string if there are no facts yet.
    """
    facts = _load()
    if not facts:
        return ""
    lines = [f"- [{f.get('category', 'general')}] {f['content']}" for f in facts]
    return "What Jarvis knows about Eduardo:\n" + "\n".join(lines)


def add_fact(content: str, category: str = "general") -> dict:
    facts = _load()
    # Replace an existing fact in the same category with the same key subject
    # (simple dedup: if content starts the same way, update instead of duplicate)
    for f in facts:
        if f.get("category") == category and _same_subject(f["content"], content):
            f["content"] = content
            f["updated"] = datetime.now().isoformat(timespec="seconds")
            _save(facts)
            return f

    fact = {
        "id": _next_id(facts),
        "content": content,
        "category": category,
        "created": datetime.now().isoformat(timespec="seconds"),
    }
    facts.append(fact)
    _save(facts)
    return fact


def update_fact(fact_id: int, new_content: str) -> dict | None:
    facts = _load()
    for f in facts:
        if f["id"] == fact_id:
            f["content"] = new_content
            f["updated"] = datetime.now().isoformat(timespec="seconds")
            _save(facts)
            return f
    return None


def delete_fact(fact_id: int) -> bool:
    facts = _load()
    new_facts = [f for f in facts if f["id"] != fact_id]
    if len(new_facts) == len(facts):
        return False
    _save(new_facts)
    return True


def search_facts(query: str) -> list[dict]:
    q = query.lower()
    return [f for f in _load() if q in f["content"].lower()]


def _next_id(facts: list[dict]) -> int:
    return max((f["id"] for f in facts), default=0) + 1


def _same_subject(existing: str, new: str) -> bool:
    # Rough heuristic: first 4 words match → same subject, update in place
    def first_words(s: str, n: int = 4) -> str:
        return " ".join(s.lower().split()[:n])
    return first_words(existing) == first_words(new)
