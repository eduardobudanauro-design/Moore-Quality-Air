"""
Jarvis Web UI — a browser-based visual that opens on the desktop.
Serves a single HTML page with a glowing orb and live conversation.
Uses Server-Sent Events (SSE) to push state/text from Jarvis to the browser.
No extra dependencies — stdlib http.server only.
"""

import json
import queue
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 7474
_clients: list[queue.Queue] = []
_clients_lock = threading.Lock()
_last_state = {"status": "idle", "text": "", "you": ""}


def _broadcast(event: str, data: dict) -> None:
    msg = f"event: {event}\ndata: {json.dumps(data)}\n\n".encode()
    with _clients_lock:
        dead = []
        for q in _clients:
            try:
                q.put_nowait(msg)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _clients.remove(q)


def set_status(status: str) -> None:
    """status: idle | listening | recording | thinking | speaking"""
    _last_state["status"] = status
    _broadcast("status", {"status": status})


def set_jarvis_text(text: str) -> None:
    _last_state["text"] = text
    _broadcast("jarvis", {"text": text})


def append_jarvis_chunk(chunk: str) -> None:
    _last_state["text"] = _last_state.get("text", "") + chunk
    _broadcast("chunk", {"chunk": chunk})


def set_you_text(text: str) -> None:
    _last_state["you"] = text
    _last_state["text"] = ""
    _broadcast("you", {"text": text})


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Jarvis</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #030712;
    color: #e2e8f0;
    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
    height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  /* Header */
  .header {
    position: fixed;
    top: 24px;
    letter-spacing: 0.4em;
    font-size: 11px;
    color: #38bdf8;
    opacity: 0.6;
    text-transform: uppercase;
  }

  /* Orb container */
  .orb-wrap {
    position: relative;
    width: 220px;
    height: 220px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 40px;
  }

  /* Outer glow rings */
  .ring {
    position: absolute;
    border-radius: 50%;
    border: 1px solid rgba(56, 189, 248, 0.15);
    animation: ringPulse 3s ease-in-out infinite;
  }
  .ring:nth-child(1) { width: 220px; height: 220px; animation-delay: 0s; }
  .ring:nth-child(2) { width: 180px; height: 180px; animation-delay: 0.4s; }
  .ring:nth-child(3) { width: 140px; height: 140px; animation-delay: 0.8s; }

  @keyframes ringPulse {
    0%, 100% { opacity: 0.15; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(1.04); }
  }

  /* Core orb */
  .orb {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 35%, #7dd3fc, #0ea5e9 40%, #0369a1 70%, #0c1a2e);
    box-shadow:
      0 0 30px rgba(14, 165, 233, 0.6),
      0 0 60px rgba(14, 165, 233, 0.3),
      0 0 100px rgba(14, 165, 233, 0.15);
    animation: orbIdle 3s ease-in-out infinite;
    transition: all 0.4s ease;
    position: relative;
    z-index: 2;
  }

  /* Orb shine */
  .orb::before {
    content: '';
    position: absolute;
    top: 18%;
    left: 22%;
    width: 28%;
    height: 20%;
    background: rgba(255,255,255,0.35);
    border-radius: 50%;
    filter: blur(4px);
  }

  @keyframes orbIdle {
    0%, 100% { transform: scale(1); box-shadow: 0 0 30px rgba(14,165,233,0.6), 0 0 60px rgba(14,165,233,0.3), 0 0 100px rgba(14,165,233,0.15); }
    50% { transform: scale(1.03); box-shadow: 0 0 40px rgba(14,165,233,0.7), 0 0 80px rgba(14,165,233,0.4), 0 0 120px rgba(14,165,233,0.2); }
  }

  /* States */
  body.listening .orb {
    background: radial-gradient(circle at 35% 35%, #a5f3fc, #06b6d4 40%, #0e7490 70%, #0c1a2e);
    animation: orbListening 1.5s ease-in-out infinite;
    box-shadow: 0 0 40px rgba(6,182,212,0.7), 0 0 80px rgba(6,182,212,0.4), 0 0 120px rgba(6,182,212,0.2);
  }
  @keyframes orbListening {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.06); }
  }

  body.recording .orb {
    background: radial-gradient(circle at 35% 35%, #bbf7d0, #22c55e 40%, #15803d 70%, #0c1a2e);
    animation: orbRecording 0.5s ease-in-out infinite;
    box-shadow: 0 0 40px rgba(34,197,94,0.8), 0 0 80px rgba(34,197,94,0.4);
  }
  @keyframes orbRecording {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
  }

  body.thinking .orb {
    background: radial-gradient(circle at 35% 35%, #e9d5ff, #a855f7 40%, #7e22ce 70%, #0c1a2e);
    animation: orbSpin 1s linear infinite;
    box-shadow: 0 0 40px rgba(168,85,247,0.7), 0 0 80px rgba(168,85,247,0.4);
  }
  @keyframes orbSpin {
    0% { filter: hue-rotate(0deg) brightness(1); }
    50% { filter: hue-rotate(30deg) brightness(1.2); }
    100% { filter: hue-rotate(0deg) brightness(1); }
  }

  body.speaking .orb {
    background: radial-gradient(circle at 35% 35%, #fef3c7, #f59e0b 40%, #b45309 70%, #0c1a2e);
    animation: orbSpeaking 0.3s ease-in-out infinite alternate;
    box-shadow: 0 0 50px rgba(245,158,11,0.8), 0 0 100px rgba(245,158,11,0.4);
  }
  @keyframes orbSpeaking {
    from { transform: scale(1); }
    to { transform: scale(1.12); }
  }

  /* Status label */
  .status-label {
    font-size: 11px;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #38bdf8;
    opacity: 0.7;
    margin-bottom: 32px;
    height: 16px;
    transition: opacity 0.3s;
  }

  /* Conversation */
  .convo {
    width: min(680px, 90vw);
    max-height: 35vh;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 0 4px;
  }
  .convo::-webkit-scrollbar { width: 3px; }
  .convo::-webkit-scrollbar-thumb { background: rgba(56,189,248,0.3); border-radius: 2px; }

  .bubble {
    padding: 12px 18px;
    border-radius: 16px;
    font-size: 15px;
    line-height: 1.55;
    max-width: 90%;
    animation: fadeUp 0.3s ease;
  }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .bubble.you {
    background: rgba(56, 189, 248, 0.08);
    border: 1px solid rgba(56, 189, 248, 0.15);
    color: #7dd3fc;
    align-self: flex-end;
  }
  .bubble.jarvis {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    color: #e2e8f0;
    align-self: flex-start;
  }
  .bubble .label {
    font-size: 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    opacity: 0.45;
    margin-bottom: 4px;
  }

  /* Waveform bars (speaking) */
  .bars {
    display: none;
    gap: 3px;
    align-items: flex-end;
    height: 24px;
    margin-top: 6px;
  }
  body.speaking .bars { display: flex; }
  .bar {
    width: 4px;
    background: #f59e0b;
    border-radius: 2px;
    animation: barBounce 0.6s ease-in-out infinite alternate;
  }
  .bar:nth-child(1) { animation-delay: 0.0s; }
  .bar:nth-child(2) { animation-delay: 0.1s; }
  .bar:nth-child(3) { animation-delay: 0.2s; }
  .bar:nth-child(4) { animation-delay: 0.3s; }
  .bar:nth-child(5) { animation-delay: 0.2s; }
  .bar:nth-child(6) { animation-delay: 0.1s; }
  .bar:nth-child(7) { animation-delay: 0.0s; }
  @keyframes barBounce {
    from { height: 4px; opacity: 0.5; }
    to { height: 22px; opacity: 1; }
  }
</style>
</head>
<body class="idle">

<div class="header">J · A · R · V · I S &nbsp;&nbsp;|&nbsp;&nbsp; InsureTechABQ</div>

<div class="orb-wrap">
  <div class="ring"></div>
  <div class="ring"></div>
  <div class="ring"></div>
  <div class="orb"></div>
</div>

<div class="bars">
  <div class="bar"></div><div class="bar"></div><div class="bar"></div>
  <div class="bar"></div><div class="bar"></div><div class="bar"></div>
  <div class="bar"></div>
</div>

<div class="status-label" id="statusLabel">Ready</div>

<div class="convo" id="convo"></div>

<script>
const body = document.body;
const label = document.getElementById('statusLabel');
const convo = document.getElementById('convo');
let jarvisBubble = null;

const statusText = {
  idle: 'Ready',
  listening: 'Hold Space to Speak',
  recording: 'Recording',
  thinking: 'Thinking',
  speaking: 'Speaking',
};

function setStatus(s) {
  body.className = s;
  label.textContent = statusText[s] || s;
}

function addBubble(role, text) {
  const el = document.createElement('div');
  el.className = `bubble ${role}`;
  el.innerHTML = `<div class="label">${role === 'you' ? 'You' : 'Jarvis'}</div><div class="text"></div>`;
  el.querySelector('.text').textContent = text;
  convo.appendChild(el);
  convo.scrollTop = convo.scrollHeight;
  return el;
}

const es = new EventSource('/events');

es.addEventListener('status', e => {
  const d = JSON.parse(e.data);
  setStatus(d.status);
});

es.addEventListener('you', e => {
  const d = JSON.parse(e.data);
  jarvisBubble = null;
  addBubble('you', d.text);
});

es.addEventListener('jarvis', e => {
  const d = JSON.parse(e.data);
  jarvisBubble = addBubble('jarvis', d.text);
});

es.addEventListener('chunk', e => {
  const d = JSON.parse(e.data);
  if (!jarvisBubble) {
    jarvisBubble = addBubble('jarvis', '');
  }
  jarvisBubble.querySelector('.text').textContent += d.chunk;
  convo.scrollTop = convo.scrollHeight;
});
</script>
</body>
</html>"""


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silence request logs

    def do_GET(self):
        if self.path == "/":
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif self.path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            q: queue.Queue = queue.Queue(maxsize=50)
            with _clients_lock:
                _clients.append(q)

            # Send current state immediately on connect
            init = json.dumps(_last_state)
            try:
                self.wfile.write(f"event: status\ndata: {{\"status\": \"{_last_state['status']}\"}}\n\n".encode())
                self.wfile.flush()
            except Exception:
                pass

            try:
                while True:
                    try:
                        msg = q.get(timeout=15)
                        self.wfile.write(msg)
                        self.wfile.flush()
                    except queue.Empty:
                        # Keepalive
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
            except Exception:
                pass
            finally:
                with _clients_lock:
                    if q in _clients:
                        _clients.remove(q)
        else:
            self.send_response(404)
            self.end_headers()


def start(open_browser: bool = True) -> None:
    server = HTTPServer(("127.0.0.1", PORT), _Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    if open_browser:
        time.sleep(0.4)
        webbrowser.open(f"http://127.0.0.1:{PORT}")
