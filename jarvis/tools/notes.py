"""
Notes tool — save, list, search, and delete notes.
Covers capabilities: reminders/follow-ups and notes Q&A.
Notes are stored as plain JSON so Eduardo can read and edit them directly.
"""

import json
import os
from datetime import datetime
from tools import tool

NOTES_FILE = os.path.join(os.path.dirname(__file__), "..", "memory", "notes.json")


def _load() -> list[dict]:
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE) as f:
        return json.load(f)


def _save(notes: list[dict]) -> None:
    os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)


@tool(
    name="save_note",
    description=(
        "Save a note, reminder, or follow-up for Eduardo. "
        "Use this any time he asks you to remember something, note something down, "
        "or follow up on something. Optionally tag it with a category like "
        "'reminder', 'project', 'idea', 'follow-up', etc."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The note text — write it as a clear, standalone statement.",
            },
            "category": {
                "type": "string",
                "description": "Optional tag: reminder, project, idea, follow-up, business, personal, etc.",
            },
        },
        "required": ["content"],
    },
)
def save_note(content: str, category: str = "general") -> str:
    notes = _load()
    note = {
        "id": len(notes) + 1,
        "content": content,
        "category": category,
        "created": datetime.now().isoformat(timespec="seconds"),
        "done": False,
    }
    notes.append(note)
    _save(notes)
    return f"Saved note #{note['id']}: {content}"


@tool(
    name="list_notes",
    description=(
        "List Eduardo's saved notes. Can filter by category or show only open "
        "(not-done) items. Use this to surface reminders, review follow-ups, "
        "or answer 'what do I have going on?'"
    ),
    input_schema={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Filter by category (e.g. 'reminder'). Omit to show all.",
            },
            "open_only": {
                "type": "boolean",
                "description": "If true, only show notes not yet marked done. Default true.",
            },
        },
        "required": [],
    },
)
def list_notes(category: str = None, open_only: bool = True) -> str:
    notes = _load()
    filtered = [
        n for n in notes
        if (not open_only or not n.get("done"))
        and (category is None or n.get("category") == category)
    ]
    if not filtered:
        return "No notes found matching those filters."
    lines = []
    for n in filtered:
        status = "✓" if n.get("done") else "•"
        cat = f"[{n['category']}] " if n.get("category") else ""
        lines.append(f"{status} #{n['id']} {cat}{n['content']}  ({n['created'][:10]})")
    return "\n".join(lines)


@tool(
    name="search_notes",
    description=(
        "Search Eduardo's notes for a keyword or phrase. Use this when he asks "
        "'do I have anything about X?' or 'what did I note about Y?'"
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Keyword or phrase to search for in note content.",
            },
        },
        "required": ["query"],
    },
)
def search_notes(query: str) -> str:
    notes = _load()
    q = query.lower()
    matches = [n for n in notes if q in n["content"].lower()]
    if not matches:
        return f"No notes found containing '{query}'."
    lines = []
    for n in matches:
        status = "✓" if n.get("done") else "•"
        lines.append(f"{status} #{n['id']} [{n['category']}] {n['content']}")
    return "\n".join(lines)


@tool(
    name="mark_note_done",
    description=(
        "Mark a note or reminder as done/complete. Use when Eduardo says something "
        "is finished, handled, or no longer needed."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "note_id": {
                "type": "integer",
                "description": "The ID number of the note to mark done.",
            },
        },
        "required": ["note_id"],
    },
)
def mark_note_done(note_id: int) -> str:
    notes = _load()
    for n in notes:
        if n["id"] == note_id:
            n["done"] = True
            _save(notes)
            return f"Note #{note_id} marked done: {n['content']}"
    return f"No note found with ID {note_id}."
