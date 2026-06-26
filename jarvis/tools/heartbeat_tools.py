"""
Heartbeat tools — let Eduardo manage the proactive inbox from conversation.

  check_inbox       — see what Jarvis has been wanting to tell you
  dismiss_notice    — clear a specific notice
  pause_heartbeat   — kill switch: stop all proactive checks
  resume_heartbeat  — turn the heartbeat back on
"""

from tools import tool
import heartbeat


@tool(
    name="check_inbox",
    description=(
        "Check what Jarvis has noticed while you were away or between turns. "
        "Use when Eduardo asks 'anything I should know?', 'any updates?', "
        "'what did you catch?', or similar. Returns unseen notices."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def check_inbox() -> str:
    notices = heartbeat.drain_inbox()
    if not notices:
        return "Nothing in the inbox — all clear."
    lines = []
    for n in notices:
        urgency = " [URGENT]" if n.urgent else ""
        lines.append(f"#{n.id}{urgency} [{n.check_name}] {n.message}\n  — {n.created[:16]}")
    return f"{len(notices)} notice{'s' if len(notices) != 1 else ''}:\n\n" + "\n\n".join(lines)


@tool(
    name="dismiss_notice",
    description=(
        "Dismiss (clear) a specific notice from the inbox by its ID. "
        "Use when Eduardo says 'got it', 'clear that', 'dismiss #X', or similar."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "notice_id": {
                "type": "integer",
                "description": "The ID number of the notice to dismiss.",
            },
        },
        "required": ["notice_id"],
    },
)
def dismiss_notice(notice_id: int) -> str:
    success = heartbeat.dismiss_notice(notice_id)
    if success:
        return f"Notice #{notice_id} dismissed."
    return f"No notice found with ID {notice_id}."


@tool(
    name="pause_heartbeat",
    description=(
        "Pause all of Jarvis's background checks — the kill switch. "
        "Use when Eduardo says 'stop the background stuff', 'pause proactive mode', "
        "or 'quiet mode'. Jarvis can still be talked to normally; it just stops watching."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def pause_heartbeat() -> str:
    heartbeat.pause()
    return "Heartbeat paused. I'll stop background checks until you say resume."


@tool(
    name="resume_heartbeat",
    description=(
        "Resume Jarvis's background checks after a pause. "
        "Use when Eduardo says 'resume', 'turn proactive back on', or similar."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def resume_heartbeat() -> str:
    heartbeat.resume()
    return "Heartbeat resumed. Back to watching in the background."
