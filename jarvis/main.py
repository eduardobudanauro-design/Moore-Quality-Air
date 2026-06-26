#!/usr/bin/env python3
"""
Jarvis — entry point.
Run: python main.py
"""

import json
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Load secrets before anything else
load_dotenv(Path(__file__).parent / ".env")

import brain
import tools as tool_registry
from tools import ToolError


def load_config() -> dict:
    cfg_path = Path(__file__).parent / "config.yaml"
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def build_system_prompt(cfg: dict) -> str:
    identity = cfg["identity"]
    personality = cfg["personality"].strip()
    tool_names = [t["name"] for t in tool_registry.get_schema_list()]
    tools_str = ", ".join(tool_names) if tool_names else "none yet"
    return (
        f"{personality}\n\n"
        f"Owner: {identity['owner']}\n"
        f"Business: {identity['business']}\n"
        f"Mission: {identity['mission']}\n\n"
        f"Available tools: {tools_str}\n"
        "Use tools whenever they'd give a better answer than guessing. "
        "Always tell Eduardo what you found or did, not just that you called a tool."
    )


def run_tool_call(block, cfg: dict) -> str:
    """Run one tool call block and return the result string."""
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


def process_turn(user_text: str, history: list[dict], system: str, cfg: dict) -> str:
    """
    Run one full turn: user text → (possibly multiple tool rounds) → final reply.
    Streams output to stdout as it arrives.
    Returns the final assistant reply text.
    """
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

        # No tool calls — we're done
        if not tool_calls:
            print()  # newline after streamed reply
            break

        # Append the assistant message (with tool_use blocks) to history
        history.append({"role": "assistant", "content": final_message.content})

        # Run each tool and build the tool_result message
        tool_results = []
        for block in tool_calls:
            result_str = run_tool_call(block, cfg)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_str,
            })

        history.append({"role": "user", "content": tool_results})
        # Loop back — let the model react to the tool results

    # Append final assistant reply to history
    if reply_text:
        history.append({"role": "assistant", "content": reply_text})

    # Trim history if it grows too long (keep system + last N turns)
    max_turns = brain_cfg.get("max_history_turns", 40)
    if len(history) > max_turns * 2:
        history[:] = history[-(max_turns * 2):]

    return reply_text


def main():
    cfg = load_config()
    system = build_system_prompt(cfg)
    history: list[dict] = []
    name = cfg["identity"]["name"]

    print(f"\n{'='*50}")
    print(f"  {name} — {cfg['identity']['business']}")
    print(f"  Type your message. Ctrl+C or 'quit' to exit.")
    print(f"{'='*50}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{name}: Catch you later, Eduardo. Go get that 8K. 💪")
            sys.exit(0)

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print(f"\n{name}: Later, Eduardo. 🤝")
            sys.exit(0)

        process_turn(user_input, history, system, cfg)


if __name__ == "__main__":
    main()
