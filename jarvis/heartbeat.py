"""
Heartbeat — the background loop that lets Jarvis act without being spoken to.

Architecture:
  - A single background thread wakes on a short tick (default 60s)
  - Each tick it checks which scheduled checks are due and runs them
  - A check returns a Notice (worth surfacing) or None (nothing to report)
  - Notices are queued in an inbox; the conversation loop drains it on each turn
  - The schedule (next_run per check) is persisted to disk so restarts don't
    reset timers or fire everything at once

Checks live in heartbeat_checks.py — one function per check, registered with
@check. Adding a new scheduled behavior = write one function, register it.

Design rules enforced here:
  - Quiet by default: only genuine worth-your-attention items become Notices
  - Held for you: notices survive restart (persisted), never silently dropped
  - Quiet hours: non-urgent notices are held until waking hours
  - No overlapping runs: a check that's still running skips its next tick
  - No blocking forever: checks have a timeout; hung checks fail safe
  - Kill switch: heartbeat.pause() / heartbeat.resume() without teardown
"""

import json
import logging
import threading
import time
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Callable, Optional
from dataclasses import dataclass, field, asdict

import yaml

logger = logging.getLogger("jarvis.heartbeat")

STATE_FILE = Path(__file__).parent / "memory" / "heartbeat_state.json"
INBOX_FILE = Path(__file__).parent / "memory" / "inbox.json"
CONFIG_FILE = Path(__file__).parent / "config.yaml"

# ─── Data structures ──────────────────────────────────────────────────────────

@dataclass
class Notice:
    check_name: str
    message: str
    urgent: bool = False
    created: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    seen: bool = False
    id: int = 0


@dataclass
class CheckEntry:
    name: str
    description: str
    interval_seconds: int
    urgent: bool          # True → surfaces even during quiet hours
    fn: Callable
    running: bool = False # guard against overlapping runs


# ─── Registry ─────────────────────────────────────────────────────────────────

_checks: dict[str, CheckEntry] = {}


def check(
    name: str,
    description: str,
    interval_seconds: int,
    urgent: bool = False,
):
    """
    Decorator to register a scheduled check.

    The decorated function must return either:
      - A string  → Jarvis surfaces it as a Notice
      - None      → nothing to report this cycle (the common case)
    """
    def decorator(fn: Callable) -> Callable:
        _checks[name] = CheckEntry(
            name=name,
            description=description,
            interval_seconds=interval_seconds,
            urgent=urgent,
            fn=fn,
        )
        return fn
    return decorator


# ─── Persistent state ─────────────────────────────────────────────────────────

def _load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _load_inbox() -> list[dict]:
    if INBOX_FILE.exists():
        with open(INBOX_FILE) as f:
            return json.load(f)
    return []


def _save_inbox(inbox: list[dict]) -> None:
    INBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INBOX_FILE, "w") as f:
        json.dump(inbox, f, indent=2)


# ─── Inbox (notice queue) ─────────────────────────────────────────────────────

def post_notice(notice: Notice) -> None:
    inbox = _load_inbox()
    notice.id = max((n.get("id", 0) for n in inbox), default=0) + 1
    inbox.append(asdict(notice))
    _save_inbox(inbox)
    logger.info(f"Notice posted: [{notice.check_name}] {notice.message}")


def drain_inbox() -> list[Notice]:
    """Return all unseen notices and mark them seen."""
    inbox = _load_inbox()
    unseen = [Notice(**n) for n in inbox if not n.get("seen")]
    for n in inbox:
        n["seen"] = True
    _save_inbox(inbox)
    return unseen


def dismiss_notice(notice_id: int) -> bool:
    inbox = _load_inbox()
    for n in inbox:
        if n.get("id") == notice_id:
            n["seen"] = True
            _save_inbox(inbox)
            return True
    return False


def get_inbox_count() -> int:
    return sum(1 for n in _load_inbox() if not n.get("seen"))


# ─── Quiet hours ──────────────────────────────────────────────────────────────

def _in_quiet_hours(cfg: dict) -> bool:
    hb = cfg.get("heartbeat", {})
    start_str = hb.get("quiet_hours_start", "22:00")
    end_str = hb.get("quiet_hours_end", "07:00")
    try:
        start = dt_time(*map(int, start_str.split(":")))
        end = dt_time(*map(int, end_str.split(":")))
    except (ValueError, AttributeError):
        return False
    now = datetime.now().time()
    if start > end:  # spans midnight
        return now >= start or now < end
    return start <= now < end


# ─── Heartbeat engine ─────────────────────────────────────────────────────────

class Heartbeat:
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._paused = threading.Event()
        self._paused.set()  # start unpaused (set = not paused)
        self._check_timeout = 30  # seconds before a hung check is abandoned

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, name="jarvis-heartbeat", daemon=True
        )
        self._thread.start()
        logger.info("Heartbeat started.")

    def stop(self) -> None:
        self._stop_event.set()
        logger.info("Heartbeat stopped.")

    def pause(self) -> None:
        self._paused.clear()
        logger.info("Heartbeat paused (kill switch).")

    def resume(self) -> None:
        self._paused.set()
        logger.info("Heartbeat resumed.")

    @property
    def is_paused(self) -> bool:
        return not self._paused.is_set()

    def _loop(self) -> None:
        with open(CONFIG_FILE) as f:
            cfg = yaml.safe_load(f)
        tick = cfg.get("heartbeat", {}).get("tick_seconds", 60)

        state = _load_state()

        while not self._stop_event.is_set():
            # Respect kill switch
            self._paused.wait()

            now = datetime.now()
            now_ts = now.timestamp()

            # Reload config each tick so changes take effect without restart
            try:
                with open(CONFIG_FILE) as f:
                    cfg = yaml.safe_load(f)
            except Exception:
                pass

            quiet = _in_quiet_hours(cfg)

            for name, entry in _checks.items():
                if entry.running:
                    continue  # skip overlapping run

                next_run = state.get(name, {}).get("next_run", 0)
                if now_ts < next_run:
                    continue  # not due yet

                # Schedule next run before we start (so a crash doesn't reset the clock)
                state.setdefault(name, {})["next_run"] = now_ts + entry.interval_seconds
                _save_state(state)

                entry.running = True
                threading.Thread(
                    target=self._run_check,
                    args=(entry, quiet),
                    daemon=True,
                ).start()

            self._stop_event.wait(timeout=tick)

    def _run_check(self, entry: CheckEntry, quiet: bool) -> None:
        result = None
        try:
            result_holder = [None]
            exc_holder = [None]

            def target():
                try:
                    result_holder[0] = entry.fn()
                except Exception as e:
                    exc_holder[0] = e

            t = threading.Thread(target=target, daemon=True)
            t.start()
            t.join(timeout=self._check_timeout)

            if t.is_alive():
                logger.warning(f"Check '{entry.name}' timed out after {self._check_timeout}s — skipping.")
                return

            if exc_holder[0]:
                logger.warning(f"Check '{entry.name}' raised: {exc_holder[0]}")
                return

            result = result_holder[0]

        finally:
            entry.running = False

        if result is None:
            return  # nothing to surface

        notice = Notice(
            check_name=entry.name,
            message=str(result),
            urgent=entry.urgent,
        )

        # Non-urgent notices are held during quiet hours
        if quiet and not entry.urgent:
            logger.info(f"Quiet hours — holding notice from '{entry.name}'")
            # Still post it — it'll be there when Eduardo opens the interface

        post_notice(notice)

        # Mirror to audit log
        try:
            import safety
            safety.log_notice(entry.name, str(result), entry.urgent)
        except Exception:
            pass


# Singleton
_heartbeat = Heartbeat()


def start() -> None:
    _heartbeat.start()


def stop() -> None:
    _heartbeat.stop()


def pause() -> None:
    _heartbeat.pause()


def resume() -> None:
    _heartbeat.resume()


def is_paused() -> bool:
    return _heartbeat.is_paused


# Import checks so their @check decorators fire
import heartbeat_checks  # noqa: E402, F401
