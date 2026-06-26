"""
Tool registry — the single place where tools are registered.
Adding a new capability: write a function, decorate it with @tool, done.
"""

import functools
from typing import Any, Callable

_registry: dict[str, dict] = {}


def tool(name: str, description: str, input_schema: dict):
    """Decorator to register a function as a Jarvis tool."""
    def decorator(fn: Callable) -> Callable:
        _registry[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "fn": fn,
            # Mark tools that require confirmation (set by individual tools)
            "requires_confirmation": getattr(fn, "_requires_confirmation", False),
        }
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def requires_confirmation(fn: Callable) -> Callable:
    """Decorator to flag a tool as requiring user confirmation before running."""
    fn._requires_confirmation = True
    return fn


def get_schema_list() -> list[dict]:
    """Return tool schemas in the format the Anthropic API expects."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
        }
        for t in _registry.values()
    ]


def run_tool(name: str, inputs: dict) -> Any:
    """
    Look up and run a tool by name.
    Returns the result, or raises ToolError on bad name or execution failure.
    """
    entry = _registry.get(name)
    if not entry:
        raise ToolError(f"No tool named '{name}'. Available: {list(_registry.keys())}")
    try:
        return entry["fn"](**inputs)
    except TypeError as e:
        raise ToolError(f"Wrong inputs for '{name}': {e}")
    except Exception as e:
        raise ToolError(f"Tool '{name}' failed: {e}")


def needs_confirmation(name: str) -> bool:
    entry = _registry.get(name)
    return bool(entry and entry.get("requires_confirmation"))


class ToolError(Exception):
    pass


# Import all tool modules so their @tool decorators fire
from tools import notes             # noqa: E402, F401
from tools import memory_tools      # noqa: E402, F401
from tools import heartbeat_tools   # noqa: E402, F401
