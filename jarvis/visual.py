"""
Terminal visual layer + web UI bridge.
Animates the terminal and pushes state to the browser orb via web_ui.
"""

import sys
import threading
import time
import itertools

CYAN   = "\033[96m"
BLUE   = "\033[94m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
WHITE  = "\033[97m"
DIM    = "\033[2m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
CLEAR  = "\033[2K\r"

HEADER = f"""
{CYAN}{BOLD}
  ╔══════════════════════════════════╗
  ║    J · A · R · V · I · S        ║
  ║    InsureTechABQ  /  ABQ Growth  ║
  ╚══════════════════════════════════╝
{RESET}"""

_anim_stop = threading.Event()
_anim_thread = None


def _web(fn_name: str, *args):
    try:
        import web_ui
        getattr(web_ui, fn_name)(*args)
    except Exception:
        pass


def _stop_anim():
    global _anim_thread
    _anim_stop.set()
    if _anim_thread and _anim_thread.is_alive():
        _anim_thread.join(timeout=0.5)
    _anim_stop.clear()
    sys.stdout.write(CLEAR)
    sys.stdout.flush()


def _run_anim(frames, color, delay=0.12):
    for frame in itertools.cycle(frames):
        if _anim_stop.is_set():
            break
        sys.stdout.write(f"{CLEAR}{color}{BOLD}{frame}{RESET}")
        sys.stdout.flush()
        time.sleep(delay)


def _start_anim(frames, color, delay=0.12):
    global _anim_thread
    _stop_anim()
    _anim_thread = threading.Thread(
        target=_run_anim, args=(frames, color, delay), daemon=True
    )
    _anim_thread.start()


def print_header():
    print(HEADER, flush=True)


def stop():
    _stop_anim()
    _web("set_status", "idle")


def show_listening():
    frames = [
        "  ○  Hold SPACE to speak   ",
        "  ◌  Hold SPACE to speak   ",
        "  ●  Hold SPACE to speak   ",
        "  ◌  Hold SPACE to speak   ",
    ]
    _start_anim(frames, DIM, delay=0.5)
    _web("set_status", "listening")


def show_recording():
    frames = [
        "  ◉  Recording  ▁          ",
        "  ◉  Recording  ▁▃         ",
        "  ◉  Recording  ▁▃▅        ",
        "  ◉  Recording  ▁▃▅▇       ",
        "  ◉  Recording  ▁▃▅▇▅      ",
        "  ◉  Recording  ▁▃▅▇▅▃     ",
        "  ◉  Recording  ▁▃▅▇▅▃▁    ",
    ]
    _start_anim(frames, GREEN, delay=0.1)
    _web("set_status", "recording")


def show_thinking():
    frames = [
        "  ⠋  Thinking              ",
        "  ⠙  Thinking .            ",
        "  ⠹  Thinking ..           ",
        "  ⠸  Thinking ...          ",
        "  ⠼  Thinking              ",
        "  ⠴  Thinking .            ",
        "  ⠦  Thinking ..           ",
        "  ⠧  Thinking ...          ",
    ]
    _start_anim(frames, CYAN, delay=0.1)
    _web("set_status", "thinking")


def show_speaking():
    frames = [
        "  ♪  Jarvis  ▁▂▃▄▃▂▁      ",
        "  ♪  Jarvis  ▂▃▄▅▄▃▂      ",
        "  ♪  Jarvis  ▃▄▅▆▅▄▃      ",
        "  ♪  Jarvis  ▄▅▆▇▆▅▄      ",
        "  ♪  Jarvis  ▃▄▅▆▅▄▃      ",
        "  ♪  Jarvis  ▂▃▄▅▄▃▂      ",
        "  ♪  Jarvis  ▁▂▃▄▃▂▁      ",
    ]
    _start_anim(frames, BLUE, delay=0.1)
    _web("set_status", "speaking")


def show_transcribing():
    frames = [
        "  ◌  Transcribing          ",
        "  ◎  Transcribing .        ",
        "  ●  Transcribing ..       ",
        "  ◎  Transcribing ...      ",
    ]
    _start_anim(frames, YELLOW, delay=0.15)
    _web("set_status", "thinking")


def print_you(text: str):
    _stop_anim()
    print(f"\n  {GREEN}{BOLD}You:{RESET}  {WHITE}{text}{RESET}", flush=True)
    _web("set_you_text", text)


def print_jarvis_start():
    _stop_anim()
    print(f"\n  {CYAN}{BOLD}Jarvis:{RESET} ", end="", flush=True)
    _web("set_jarvis_text", "")


def print_jarvis_chunk(text: str):
    print(f"{CYAN}{text}{RESET}", end="", flush=True)
    _web("append_jarvis_chunk", text)


def print_jarvis_end():
    print(flush=True)
