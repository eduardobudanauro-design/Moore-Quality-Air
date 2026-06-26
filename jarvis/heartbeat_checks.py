"""
Heartbeat checks — the things Jarvis watches for you.

Each check is a function decorated with @check. It runs on its interval,
returns a string if something is worth surfacing, or None if there's nothing
to report. Add new checks here without touching heartbeat.py.

Current checks:
  daily_reminder_scan  — surface notes/reminders that are overdue or due today
  revenue_nudge        — periodic nudge toward the $8K/month goal
  stale_notes_alert    — flag notes that have been open for too long

All intervals and thresholds are pulled from config.yaml where possible.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from heartbeat import check

NOTES_FILE = Path(__file__).parent / "memory" / "notes.json"
FACTS_FILE = Path(__file__).parent / "memory" / "facts.json"


def _load_notes() -> list[dict]:
    if not NOTES_FILE.exists():
        return []
    with open(NOTES_FILE) as f:
        return json.load(f)


def _load_facts() -> list[dict]:
    if not FACTS_FILE.exists():
        return []
    with open(FACTS_FILE) as f:
        return json.load(f)


# ─── Check: daily reminder scan ──────────────────────────────────────────────

@check(
    name="daily_reminder_scan",
    description="Surfaces open reminders and follow-ups from your notes.",
    interval_seconds=3600,  # every hour; overrideable in config.yaml
    urgent=False,
)
def daily_reminder_scan() -> str | None:
    notes = _load_notes()
    reminders = [
        n for n in notes
        if not n.get("done")
        and n.get("category") in ("reminder", "follow-up", "follow_up")
    ]
    if not reminders:
        return None

    # Only surface if there are reminders at least 6 hours old (avoid noise)
    cutoff = datetime.now() - timedelta(hours=6)
    due = []
    for n in reminders:
        created_str = n.get("created", "")
        try:
            created = datetime.fromisoformat(created_str)
            if created < cutoff:
                due.append(n)
        except ValueError:
            due.append(n)

    if not due:
        return None

    lines = [f"• #{n['id']} {n['content']}" for n in due[:5]]  # cap at 5
    count = len(due)
    tail = f" (+{count - 5} more)" if count > 5 else ""
    return f"You've got {count} open reminder{'s' if count != 1 else ''}{tail}:\n" + "\n".join(lines)


# ─── Check: revenue nudge ─────────────────────────────────────────────────────

@check(
    name="revenue_nudge",
    description="Periodic nudge toward the $8K/month revenue goal.",
    interval_seconds=86400,  # once a day
    urgent=False,
)
def revenue_nudge() -> str | None:
    facts = _load_facts()

    # Only nudge if we have a revenue goal stored
    goal_facts = [f for f in facts if f.get("category") == "goal"]
    if not goal_facts:
        return None

    notes = _load_notes()
    open_notes = [n for n in notes if not n.get("done")]
    project_notes = [n for n in open_notes if n.get("category") == "project"]
    business_notes = [n for n in open_notes if n.get("category") == "business"]

    total_open = len(open_notes)
    if total_open == 0:
        return (
            "Revenue check-in: no open tasks on the board. "
            "What's the next move toward $8K/month?"
        )

    return (
        f"Daily check-in: {total_open} open item{'s' if total_open != 1 else ''} "
        f"({len(project_notes)} project, {len(business_notes)} business). "
        "Anything blocking the $8K goal?"
    )


# ─── Check: stale notes alert ─────────────────────────────────────────────────

@check(
    name="stale_notes_alert",
    description="Flags notes that have been open for more than 7 days.",
    interval_seconds=43200,  # twice a day
    urgent=False,
)
def stale_notes_alert() -> str | None:
    notes = _load_notes()
    cutoff = datetime.now() - timedelta(days=7)
    stale = []
    for n in notes:
        if n.get("done"):
            continue
        try:
            created = datetime.fromisoformat(n.get("created", ""))
            if created < cutoff:
                stale.append(n)
        except ValueError:
            pass

    if not stale:
        return None

    lines = [f"• #{n['id']} [{n.get('category','?')}] {n['content'][:60]}…"
             if len(n['content']) > 60 else f"• #{n['id']} [{n.get('category','?')}] {n['content']}"
             for n in stale[:4]]
    count = len(stale)
    tail = f" (+{count - 4} more)" if count > 4 else ""
    return (
        f"{count} note{'s' if count != 1 else ''} open for 7+ days{tail}. "
        "Worth a review:\n" + "\n".join(lines)
    )
