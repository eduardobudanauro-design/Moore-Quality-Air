"""
Voice output — the mouth.

Streams ElevenLabs TTS and plays audio as it arrives, so Jarvis starts
speaking before the full sentence is synthesized. This is what makes the
response feel fast rather than laggy.

The only public function is speak(text, voice_id).
Everything else — the ElevenLabs SDK, the audio playback — is hidden here.
Changing providers or voices means editing this file only.

External dependencies:
  elevenlabs    — official ElevenLabs SDK; key in ELEVENLABS_API_KEY env var
  pyaudio       — audio playback
"""

import os
import threading
import pyaudio

from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

# Global flag — set True while Jarvis is speaking so PTT ignores mic input
is_speaking = threading.Event()

# Global flag — set True to interrupt playback mid-sentence
interrupt_flag = threading.Event()

_client: ElevenLabs | None = None

# Default voice: "Daniel" — deep, authoritative British male.
# Override with ELEVENLABS_VOICE_ID in .env or voice.tts_voice_id in config.yaml.
DEFAULT_VOICE_ID = "onwK4e9ZLuTAKqWW03F9"  # Daniel (British, deep)


def _get_client() -> ElevenLabs:
    global _client
    if _client is None:
        key = os.environ.get("ELEVENLABS_API_KEY")
        if not key:
            raise EnvironmentError("ELEVENLABS_API_KEY is not set. Add it to jarvis/.env")
        _client = ElevenLabs(api_key=key)
    return _client


def speak(text: str, voice_id: str = "") -> None:
    """
    Convert text to speech and play it.
    Streams audio from ElevenLabs and plays chunk-by-chunk so output starts fast.
    Returns only after playback finishes (or is interrupted).
    """
    if not text or not text.strip():
        return

    resolved_voice = (
        voice_id
        or os.environ.get("ELEVENLABS_VOICE_ID", "")
        or DEFAULT_VOICE_ID
    )

    client = _get_client()
    interrupt_flag.clear()
    is_speaking.set()

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=22050,
        output=True,
        frames_per_buffer=2048,
    )

    try:
        audio_stream = client.text_to_speech.convert(
            voice_id=resolved_voice,
            text=text,
            model_id="eleven_turbo_v2",  # fastest model, lowest latency
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
            ),
            output_format="pcm_22050",  # raw PCM so we can stream directly
        )
        for chunk in audio_stream:
            if interrupt_flag.is_set():
                break
            if chunk:
                stream.write(chunk)
    except Exception as e:
        print(f"\n  [TTS error: {e}]", flush=True)
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        is_speaking.clear()


def interrupt_speech() -> None:
    """Call this to cut off Jarvis mid-sentence."""
    interrupt_flag.set()
