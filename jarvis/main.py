#!/usr/bin/env python3
"""
Jarvis — entry point.

Run:
  python main.py              # text mode (default)
  python main.py --voice ptt  # push-to-talk
  python main.py --voice wake # open-mic wake word ("Jarvis")
  python main.py --voice      # uses mode from config.yaml

The brain (brain.py) and tools (tools/) are identical in all modes.
Voice is a wrapper around the same process_turn() — not a fork.
"""

import argparse
import json
import os
import sys
import threading
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import brain
import tools as tool_registry
from tools import ToolError
import memory
import heartbeat


def load_config() -> dict:
    cfg_path = Path(__file__).parent / "config.yaml"
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def build_system_prompt(cfg: dict) -> str:
    identity = cfg["identity"]
    personality = cfg["personality"].strip()
    tool_names = [t["name"] for t in tool_registry.get_schema_list()]
    tools_str = ", ".join(tool_names) if tool_names else "none yet"

    memory_block = memory.facts_as_prompt_block()
    memory_section = f"\n\n{memory_block}" if memory_block else ""

    return (
        f"{personality}\n\n"
        f"Owner: {identity['owner']}\n"
        f"Business: {identity['business']}\n"
        f"Mission: {identity['mission']}"
        f"{memory_section}\n\n"
        f"Available tools: {tools_str}\n"
        "Use tools whenever they'd give a better answer than guessing. "
        "Always tell Eduardo what you found or did, not just that you called a tool.\n"
        "When Eduardo tells you something worth keeping across sessions — a preference, "
        "a decision, a key fact — use remember_fact to store it without being asked."
    )


def build_greeting(cfg: dict) -> str:
    """
    Generate a short opening line for each new session.
    If memory has facts, Jarvis references them to feel like it knows Eduardo.
    Returns None if we want a silent start.
    """
    facts = memory.load_facts()
    name = cfg["identity"]["name"]

    if not facts:
        return f"{name} online. What are we working on?"

    # Pull out any goal/business facts for a context-aware opener
    business_facts = [f["content"] for f in facts if f.get("category") in ("goal", "business")]
    if business_facts:
        return f"Hey Eduardo. {name} here — picking up where we left off. What do you need?"
    return f"Welcome back, Eduardo. {name} ready. What's on the agenda?"


def run_tool_call(block, cfg: dict) -> str:
    name = block.name
    inputs = block.input

    if tool_registry.needs_confirmation(name):
        print(f"\n⚠  Jarvis wants to run '{name}' with: {json.dumps(inputs, indent=2)}")
        answer = input("Allow? (yes/no): ").strip().lower()
        if answer not in ("yes", "y"):
            return f"Action '{name}' was cancelled by Eduardo."

    if cfg.get("logging", {}).get("show_tool_calls"):
        print(f"\n  [tool: {name}({json.dumps(inputs)})]", flush=True)

    try:
        result = tool_registry.run_tool(name, inputs)
        return str(result)
    except ToolError as e:
        return f"Tool error: {e}"


def _surface_inbox() -> str | None:
    """
    If the inbox has unseen notices, return a formatted string to prepend to
    the next Jarvis reply. Returns None if inbox is empty.
    """
    count = heartbeat.get_inbox_count()
    if count == 0:
        return None
    word = "notice" if count == 1 else "notices"
    return f"📬 {count} new {word} in your inbox — say 'check inbox' to see them."


def process_turn(user_text: str, history: list[dict], system: str, cfg: dict) -> str:
    """
    One full turn: user text → (tool rounds) → final reply.
    Streams text to stdout. Returns the full reply string.
    Voice callers use the returned string; text callers rely on the streaming print.
    """
    # Surface inbox count so Eduardo knows something came in
    inbox_hint = _surface_inbox()
    if inbox_hint:
        print(f"\n{inbox_hint}", flush=True)

    brain_cfg = cfg["brain"]
    history.append({"role": "user", "content": user_text})
    reply_text = ""

    while True:
        tool_calls = []
        text_chunks = []
        final_message = None

        print(f"\nJarvis: ", end="", flush=True)

        for event_type, data in brain.ask_brain_stream(
            messages=history,
            system=system,
            tools=tool_registry.get_schema_list() or None,
            model=brain_cfg["model"],
            max_tokens=brain_cfg["max_tokens"],
        ):
            if event_type == "text":
                print(data, end="", flush=True)
                text_chunks.append(data)
            elif event_type == "tool_use":
                tool_calls.append(data)
            elif event_type == "message_stop":
                final_message = data
            elif event_type == "error":
                print(f"\n[Error] {data}", flush=True)
                return str(data)

        reply_text = "".join(text_chunks)

        if not tool_calls:
            print()
            break

        history.append({"role": "assistant", "content": final_message.content})

        tool_results = []
        for block in tool_calls:
            result_str = run_tool_call(block, cfg)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_str,
            })

        history.append({"role": "user", "content": tool_results})

    if reply_text:
        history.append({"role": "assistant", "content": reply_text})

    max_turns = brain_cfg.get("max_history_turns", 40)
    if len(history) > max_turns * 2:
        history[:] = history[-(max_turns * 2):]

    return reply_text


# ─── Text loop ────────────────────────────────────────────────────────────────

def run_text_loop(cfg: dict, system: str) -> None:
    history: list[dict] = []
    name = cfg["identity"]["name"]

    print(f"\n{'='*50}")
    print(f"  {name} — {cfg['identity']['business']}")
    print(f"  Type your message. Ctrl+C or 'quit' to exit.")
    print(f"{'='*50}")

    greeting = build_greeting(cfg)
    print(f"\nJarvis: {greeting}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{name}: Catch you later, Eduardo. Go get that 8K.")
            sys.exit(0)

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print(f"\n{name}: Later, Eduardo.")
            sys.exit(0)

        process_turn(user_input, history, system, cfg)


# ─── Push-to-talk loop ────────────────────────────────────────────────────────

def run_ptt_loop(cfg: dict, system: str) -> None:
    from voice.input import listen_push_to_talk
    from voice.output import speak, interrupt_speech, is_speaking

    history: list[dict] = []
    name = cfg["identity"]["name"]
    voice_cfg = cfg.get("voice", {})
    voice_id = voice_cfg.get("tts_voice_id", "")
    show_transcript = voice_cfg.get("show_transcript", True)

    print(f"\n{'='*50}")
    print(f"  {name} — Push-to-talk mode")
    print(f"  Hold SPACE to speak. Ctrl+C to exit.")
    print(f"{'='*50}")

    greeting = build_greeting(cfg)
    print(f"\nJarvis: {greeting}\n")
    if greeting:
        tts_thread = threading.Thread(target=speak, args=(greeting, voice_id), daemon=True)
        tts_thread.start()
        tts_thread.join()

    while True:
        try:
            # If Jarvis is still speaking when we start a new cycle, interrupt it
            if is_speaking.is_set():
                interrupt_speech()
                is_speaking.wait(timeout=0.5)

            transcript = listen_push_to_talk(
                on_listening=lambda: print("  [Recording…]", flush=True)
            )

            if not transcript:
                print("  (didn't catch that — try again)\n")
                continue

            if show_transcript:
                print(f"\nYou said: {transcript}")

            # Start TTS in a thread so we can interrupt it if needed
            reply = process_turn(transcript, history, system, cfg)

            if reply:
                tts_thread = threading.Thread(
                    target=speak, args=(reply, voice_id), daemon=True
                )
                tts_thread.start()

        except KeyboardInterrupt:
            interrupt_speech()
            print(f"\n\n{name}: Catch you later, Eduardo.")
            sys.exit(0)


# ─── Wake-word loop ───────────────────────────────────────────────────────────

def run_wake_word_loop(cfg: dict, system: str) -> None:
    from voice.input import listen_wake_word
    from voice.output import speak, interrupt_speech, is_speaking

    history: list[dict] = []
    name = cfg["identity"]["name"]
    voice_cfg = cfg.get("voice", {})
    voice_id = voice_cfg.get("tts_voice_id", "")
    sensitivity = voice_cfg.get("wake_word_sensitivity", 0.5)
    show_transcript = voice_cfg.get("show_transcript", True)

    print(f"\n{'='*50}")
    print(f"  {name} — Wake-word mode")
    print(f"  Say 'Jarvis' to activate. Ctrl+C to exit.")
    print(f"{'='*50}")

    greeting = build_greeting(cfg)
    print(f"\nJarvis: {greeting}\n")
    if greeting:
        tts_thread = threading.Thread(target=speak, args=(greeting, voice_id), daemon=True)
        tts_thread.start()
        tts_thread.join()

    while True:
        try:
            if is_speaking.is_set():
                interrupt_speech()
                is_speaking.wait(timeout=0.5)

            transcript = listen_wake_word(
                sensitivity=sensitivity,
                on_detected=lambda: print("  [Activated — speak now…]", flush=True),
            )

            if not transcript:
                print("  (didn't catch that — say 'Jarvis' to try again)\n")
                continue

            if show_transcript:
                print(f"\nYou said: {transcript}")

            reply = process_turn(transcript, history, system, cfg)

            if reply:
                tts_thread = threading.Thread(
                    target=speak, args=(reply, voice_id), daemon=True
                )
                tts_thread.start()
                # Don't start the next wake-word listen until TTS finishes
                # (prevents Jarvis from hearing itself)
                tts_thread.join()

        except KeyboardInterrupt:
            interrupt_speech()
            print(f"\n\n{name}: Catch you later, Eduardo.")
            sys.exit(0)


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Jarvis assistant")
    parser.add_argument(
        "--voice",
        nargs="?",
        const="config",  # --voice with no arg → use config.yaml setting
        choices=["ptt", "wake", "config"],
        help="Voice mode: ptt (push-to-talk), wake (wake word), or use config",
    )
    args = parser.parse_args()

    cfg = load_config()
    system = build_system_prompt(cfg)

    # Start heartbeat background loop if enabled in config
    if cfg.get("heartbeat", {}).get("enabled", False):
        heartbeat.start()

    # Determine mode
    if args.voice is None:
        mode = "text"
    elif args.voice == "config":
        mode = cfg.get("voice", {}).get("mode", "push_to_talk")
    else:
        mode_map = {"ptt": "push_to_talk", "wake": "wake_word"}
        mode = mode_map.get(args.voice, "push_to_talk")

    if mode == "text":
        run_text_loop(cfg, system)
    elif mode == "push_to_talk":
        run_ptt_loop(cfg, system)
    elif mode == "wake_word":
        run_wake_word_loop(cfg, system)
    else:
        print(f"Unknown mode '{mode}', falling back to text.")
        run_text_loop(cfg, system)


if __name__ == "__main__":
    main()
