"""
Voice output — the mouth.
Streams ElevenLabs TTS and plays audio as it arrives.
"""

import os
import threading
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

    try:
        # Support both old and new ElevenLabs SDK versions
        try:
            from elevenlabs.client import ElevenLabs
            client = ElevenLabs(api_key=key)
            audio_stream = client.text_to_speech.convert(
                voice_id=resolved_voice,
                text=text,
                model_id="eleven_turbo_v2",
                output_format="pcm_22050",
            )
        except Exception:
            # Fallback for older SDK versions
            from elevenlabs import generate, stream as el_stream, set_api_key
            set_api_key(key)
            audio_stream = generate(
                text=text,
                voice=resolved_voice,
                model="eleven_turbo_v2",
                stream=True,
            )

        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=22050,
            output=True,
            frames_per_buffer=2048,
        )

        try:
            for chunk in audio_stream:
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
