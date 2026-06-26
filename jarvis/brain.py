"""
Provider seam — the only file that imports the Anthropic SDK.
Everything else calls ask_brain() or ask_brain_stream().
"""

import os
import anthropic
from typing import Generator

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise EnvironmentError("ANTHROPIC_API_KEY is not set. Add it to jarvis/.env")
        _client = anthropic.Anthropic(api_key=key)
    return _client


def ask_brain_stream(
    messages: list[dict],
    system: str,
    tools: list[dict] | None,
    model: str,
    max_tokens: int,
) -> Generator[tuple[str, object], None, None]:
    """
    Yields (event_type, data) tuples:
      ("text", str)              — streamed text delta
      ("tool_use", block)        — model wants to call a tool
      ("message_stop", message)  — final assembled message object
      ("error", Exception)       — something went wrong
    """
    client = _get_client()
    kwargs: dict = dict(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    if tools:
        kwargs["tools"] = tools

    try:
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield ("text", text)
            final = stream.get_final_message()
            # surface any tool_use blocks
            for block in final.content:
                if block.type == "tool_use":
                    yield ("tool_use", block)
            yield ("message_stop", final)
    except anthropic.APIConnectionError as e:
        yield ("error", ConnectionError(f"Can't reach Anthropic — check your internet. ({e})"))
    except anthropic.AuthenticationError:
        yield ("error", PermissionError("Bad API key — check ANTHROPIC_API_KEY in your .env file."))
    except anthropic.RateLimitError:
        yield ("error", RuntimeError("Rate limited by Anthropic. Wait a moment and try again."))
    except anthropic.APIStatusError as e:
        yield ("error", RuntimeError(f"Anthropic error {e.status_code}: {e.message}"))
