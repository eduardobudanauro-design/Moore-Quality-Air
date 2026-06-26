"""
Safety layer — the rails that make Jarvis trustworthy enough to leave running.

Three responsibilities:
  1. Confirmation gate  — stops consequential actions before they run,
                          states exactly what it's about to do, waits for yes
  2. Prompt injection   — detects content that looks like instructions and
                          flags it to Eduardo instead of obeying
  3. Audit log          — every tool call, every notice, every confirmation
                          written to jarvis.log in plain, searchable text

Rules:
  - Confirmation is per-action; one yes never pre-authorizes the next
  - The gate covers typed turns, voice turns, and heartbeat-initiated actions
  - Injection detection treats all external content as data, never commands
  - The audit log is append-only — nothing is ever edited or deleted from it
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

import yaml

CONFIG_FILE = Path(__file__).parent / "config.yaml"
LOG_FILE = Path(__file__).parent / "jarvis.log"

# ─── Audit logger ─────────────────────────────────────────────────────────────

def _get_audit_logger() -> logging.Logger:
    logger = logging.getLogger("jarvis.audit")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)
    # Also mirror to stdout at DEBUG level so costs/tools are visible in terminal
    stream = logging.StreamHandler()
    stream.setLevel(logging.WARNING)  # only warnings+ to terminal; full detail in log
    stream.setFormatter(logging.Formatter("  [%(levelname)s] %(message)s"))
    logger.addHandler(stream)
    return logger


_audit = _get_audit_logger()


def log_tool_call(name: str, inputs: dict, result: str, source: str = "conversation") -> None:
    _audit.info(f"TOOL  source={source}  tool={name}  inputs={json.dumps(inputs)}  result={result[:120]!r}")


def log_confirmation(name: str, inputs: dict, approved: bool) -> None:
    verdict = "APPROVED" if approved else "DENIED"
    _audit.warning(f"GATE  {verdict}  tool={name}  inputs={json.dumps(inputs)}")


def log_notice(check_name: str, message: str, urgent: bool) -> None:
    _audit.info(f"NOTICE  check={check_name}  urgent={urgent}  message={message[:120]!r}")


def log_injection_flag(content_source: str, snippet: str) -> None:
    _audit.warning(f"INJECTION_FLAG  source={content_source!r}  snippet={snippet[:200]!r}")


def log_session_start(mode: str) -> None:
    _audit.info(f"SESSION_START  mode={mode}")


def log_session_end() -> None:
    _audit.info("SESSION_END")


def log_cost(input_tokens: int, output_tokens: int, model: str) -> None:
    _audit.info(f"COST  model={model}  input_tokens={input_tokens}  output_tokens={output_tokens}")


# ─── Confirmation gate ────────────────────────────────────────────────────────

def _load_confirmation_list() -> list[str]:
    try:
        with open(CONFIG_FILE) as f:
            cfg = yaml.safe_load(f)
        return cfg.get("confirmation_required", [])
    except Exception:
        # Fail safe: if config unreadable, require confirmation for everything
        return ["spend_money", "delete_data", "change_setting", "any_irreversible_action"]


def requires_confirmation(tool_name: str) -> bool:
    """True if this tool name matches the confirmation list in config.yaml."""
    blocked = _load_confirmation_list()
    name_lower = tool_name.lower()
    for pattern in blocked:
        if pattern.lower() in name_lower or name_lower in pattern.lower():
            return True
    return False


def confirm_action(
    tool_name: str,
    inputs: dict,
    speak_fn=None,
) -> bool:
    """
    Present the action to Eduardo and wait for explicit yes/no.
    speak_fn: optional TTS callable for voice mode confirmation.
    Returns True (approved) or False (denied).
    This is called for EVERY matching action — one yes never carries forward.
    """
    summary = _describe_action(tool_name, inputs)

    prompt_text = (
        f"\n⚠  Jarvis wants to: {summary}\n"
        f"   Tool: {tool_name}\n"
        f"   Inputs: {json.dumps(inputs, indent=4)}\n"
        f"   Allow this? (yes / no): "
    )
    print(prompt_text, end="", flush=True)

    if speak_fn:
        try:
            speak_fn(f"I want to {summary}. Should I go ahead?")
        except Exception:
            pass

    try:
        answer = input("").strip().lower()
    except (KeyboardInterrupt, EOFError):
        answer = "no"

    approved = answer in ("yes", "y")
    log_confirmation(tool_name, inputs, approved)

    if not approved:
        print(f"   Cancelled.\n", flush=True)
    return approved


def _describe_action(tool_name: str, inputs: dict) -> str:
    """Turn a tool name + inputs into a plain-English one-liner."""
    descriptions = {
        "spend_money": "spend money",
        "delete_data": lambda i: f"delete: {i.get('target', 'data')}",
        "change_setting": lambda i: f"change setting '{i.get('key', '?')}' to '{i.get('value', '?')}'",
        "send_email": lambda i: f"send email to {i.get('to', '?')} — subject: {i.get('subject', '?')}",
        "delete_file": lambda i: f"permanently delete file: {i.get('path', '?')}",
        "delete_note": lambda i: f"permanently delete note #{i.get('note_id', '?')}",
    }
    handler = descriptions.get(tool_name)
    if callable(handler):
        return handler(inputs)
    if isinstance(handler, str):
        return handler
    # Generic fallback
    input_summary = ", ".join(f"{k}={v!r}" for k, v in list(inputs.items())[:3])
    return f"run '{tool_name}' with {input_summary}"


# ─── Prompt injection detection ───────────────────────────────────────────────

# Patterns that suggest injected instructions in external content
_INJECTION_PATTERNS = [
    r"ignore (?:\w+ ){0,3}(?:rules?|instructions?|constraints?|guidelines?|prompt|directive)",
    r"disregard (?:\w+ ){0,3}(?:rules?|instructions?|constraints?|guidelines?|prompt|directive)",
    r"you are now",
    r"new (instructions?|directive|rules?|persona|role):",
    r"from now on (you (must|should|will|are))",
    r"system prompt",
    r"override (your|all) (instructions?|rules?|safety)",
    r"act as (if you are|a different|an unrestricted)",
    r"pretend (you (have no|are not|don't have))",
    r"forget (everything|your|all) (you know|instructions?|training|rules?)",
    r"(do|execute|run) (the following|this) (command|instruction|code)",
    r"<\s*(system|assistant|human|user)\s*>",  # role-injection tags
]

_INJECTION_RE = re.compile(
    "|".join(_INJECTION_PATTERNS),
    re.IGNORECASE,
)


def scan_for_injection(content: str, source: str = "external content") -> str | None:
    """
    Scan a string of external content for injection attempts.
    Returns a warning message to surface to Eduardo, or None if clean.
    The warning includes the suspicious snippet so Eduardo can judge it.
    """
    match = _INJECTION_RE.search(content)
    if not match:
        return None

    snippet = content[max(0, match.start() - 40): match.end() + 40].strip()
    log_injection_flag(source, snippet)
    return (
        f"⚠  Possible prompt injection detected in {source}.\n"
        f"   Suspicious text: \"{snippet}\"\n"
        f"   I'm not acting on it — showing it to you instead. "
        f"Let me know if you want me to proceed anyway."
    )
