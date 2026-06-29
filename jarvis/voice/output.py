"""
Voice output — the mouth.
Fetches MP3 from ElevenLabs, decodes to raw PCM via ffmpeg subprocess,
plays with pyaudio. No pydub or audioop needed.
"""

import os
import subprocess
import threading
import httpx
import pyaudio

is_speaking = threading.Event()
interrupt_flag = threading.Event()

DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam (American, deep)


def _mp3_to_pcm(mp3_bytes: bytes) -> bytes:
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", "pipe:0", "-f", "s16le", "-ar", "44100", "-ac", "1", "pipe:1"],
        input=mp3_bytes,
        capture_output=True,
    )
    return result.stdout


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

    try:
        response = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{resolved_voice}",
            headers={
                "xi-api-key": key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_turbo_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            },
            timeout=30,
        )

        if response.status_code != 200:
            print(f"\n  [TTS error: HTTP {response.status_code}]", flush=True)
            return

        pcm_data = _mp3_to_pcm(response.content)
        if not pcm_data:
            print("\n  [TTS error: ffmpeg produced no audio]", flush=True)
            return

        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            output=True,
            frames_per_buffer=4096,
        )
        try:
            chunk_size = 4096
            for i in range(0, len(pcm_data), chunk_size):
                if interrupt_flag.is_set():
                    break
                stream.write(pcm_data[i:i + chunk_size])
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
