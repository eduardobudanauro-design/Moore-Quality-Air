"""
Voice output — the mouth.
Calls ElevenLabs API directly via httpx, requests PCM audio, plays with pyaudio.
No ElevenLabs SDK needed — works with any Python version.
"""

import os
import io
import threading
import httpx
import pyaudio

is_speaking = threading.Event()
interrupt_flag = threading.Event()

DEFAULT_VOICE_ID = "onwK4e9ZLuTAKqWW03F9"  # Daniel (British, deep)


def speak(text: str, voice_id: str = "") -> None:
    if not text or not text.strip():
        return

    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        print("\n  [TTS error: ELEVENLABS_API_KEY not set]", flush=True)
        return

    resolved_voice = (
        voice_id
        or os.environ.get("ELEVENLABS_VOICE_ID", "")
        or DEFAULT_VOICE_ID
    )

    interrupt_flag.clear()
    is_speaking.set()

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{resolved_voice}/stream"
    headers = {
        "xi-api-key": key,
        "Content-Type": "application/json",
        "Accept": "audio/pcm; sample_rate=22050",
    }
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
        "output_format": "pcm_22050",
    }

    try:
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=22050,
            output=True,
            frames_per_buffer=2048,
        )

        try:
            with httpx.stream("POST", url, headers=headers, json=payload, timeout=30) as response:
                if response.status_code != 200:
                    body = response.read()
                    print(f"\n  [TTS error: HTTP {response.status_code} — {body[:200]}]", flush=True)
                    return
                for chunk in response.iter_bytes(chunk_size=4096):
                    if interrupt_flag.is_set():
                        break
                    if chunk:
                        stream.write(chunk)
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

    except Exception as e:
        print(f"\n  [TTS error: {e}]", flush=True)
    finally:
        is_speaking.clear()


def interrupt_speech() -> None:
    interrupt_flag.set()
