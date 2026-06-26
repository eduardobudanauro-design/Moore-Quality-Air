"""
Voice input — the ears.

Two modes (set in config.yaml voice.mode):
  push_to_talk  — hold spacebar, speak, release → returns transcript
  wake_word     — always listening for "Hey Jarvis", then records until silence

Both return a plain string (the transcript) to main.py, which feeds it into
the same process_turn() used by typed input. The brain never knows the difference.

External dependencies (install in requirements.txt):
  pyaudio          — cross-platform audio capture (needs portaudio on macOS: brew install portaudio)
  deepgram-sdk     — Deepgram STT; key in DEEPGRAM_API_KEY env var
  pvporcupine      — offline wake-word detection; key in PICOVOICE_API_KEY env var
  pynput           — keyboard listener for push-to-talk (no root required on macOS)
"""

import os
import io
import time
import wave
import threading
from typing import Callable

import pyaudio
from deepgram import DeepgramClient
try:
    from deepgram import PrerecordedOptions
except ImportError:
    PrerecordedOptions = None


# Audio capture settings
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK = 1024
FORMAT = pyaudio.paInt16


# ─── Deepgram STT seam ───────────────────────────────────────────────────────

def transcribe(audio_bytes: bytes) -> str:
    """
    Send raw PCM audio bytes to Deepgram and return the transcript.
    This is the only function that touches the Deepgram SDK.
    """
    key = os.environ.get("DEEPGRAM_API_KEY")
    if not key:
        raise EnvironmentError("DEEPGRAM_API_KEY is not set. Add it to jarvis/.env")

    client = DeepgramClient(key)

    # Wrap raw PCM in a WAV container so Deepgram knows the format
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_bytes)
    wav_buffer.seek(0)

    options = {"model": "nova-2", "smart_format": True, "language": "en-US"}
    if PrerecordedOptions is not None:
        options = PrerecordedOptions(**options)

    response = client.listen.prerecorded.v("1").transcribe_file(
        {"buffer": wav_buffer, "mimetype": "audio/wav"},
        options,
    )
    try:
        transcript = response.results.channels[0].alternatives[0].transcript
        return transcript.strip()
    except (AttributeError, IndexError):
        return ""


# ─── Audio capture helpers ───────────────────────────────────────────────────

def _record_until_released(stop_event: threading.Event) -> bytes:
    """Record audio until stop_event is set (push-to-talk release)."""
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )
    frames = []
    try:
        while not stop_event.is_set():
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
    return b"".join(frames)


def _record_until_silence(
    silence_threshold: int = 500,
    silence_seconds: float = 1.5,
    max_seconds: float = 30.0,
) -> bytes:
    """Record audio until silence_seconds of quiet, or max_seconds total."""
    import audioop
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )
    frames = []
    silent_chunks = 0
    silence_limit = int(SAMPLE_RATE / CHUNK * silence_seconds)
    max_chunks = int(SAMPLE_RATE / CHUNK * max_seconds)

    try:
        for _ in range(max_chunks):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            rms = audioop.rms(data, 2)
            if rms < silence_threshold:
                silent_chunks += 1
                if silent_chunks >= silence_limit:
                    break
            else:
                silent_chunks = 0
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
    return b"".join(frames)


# ─── Push-to-talk ─────────────────────────────────────────────────────────────

def listen_push_to_talk(on_listening: Callable = None) -> str:
    """
    Block until user holds spacebar, record while held, return transcript on release.
    on_listening: optional callback called the moment recording starts.
    """
    from pynput import keyboard

    stop_event = threading.Event()
    start_event = threading.Event()

    def on_press(key):
        if key == keyboard.Key.space and not start_event.is_set():
            start_event.set()

    def on_release(key):
        if key == keyboard.Key.space:
            stop_event.set()
            return False  # stop listener

    print("  [Hold SPACE to speak]", flush=True)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    start_event.wait()

    if on_listening:
        on_listening()
    print("  [Listening…]", flush=True)

    audio = _record_until_released(stop_event)
    listener.join()

    print("  [Transcribing…]", flush=True)
    transcript = transcribe(audio)
    return transcript


# ─── Wake word ────────────────────────────────────────────────────────────────

def listen_wake_word(
    sensitivity: float = 0.5,
    on_detected: Callable = None,
) -> str:
    """
    Block until wake word is detected, then record until silence, return transcript.
    Uses Porcupine (offline, runs on CPU) — requires PICOVOICE_API_KEY in .env.

    The built-in keyword is "jarvis" (available free in Porcupine's keyword library).
    """
    import pvporcupine
    import struct

    key = os.environ.get("PICOVOICE_API_KEY")
    if not key:
        raise EnvironmentError("PICOVOICE_API_KEY is not set. Add it to jarvis/.env")

    porcupine = pvporcupine.create(
        access_key=key,
        keywords=["jarvis"],
        sensitivities=[sensitivity],
    )

    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length,
    )

    print("  [Listening for 'Jarvis'…]", flush=True)

    try:
        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm_unpacked = struct.unpack_from("h" * porcupine.frame_length, pcm)
            result = porcupine.process(pcm_unpacked)
            if result >= 0:
                break
    finally:
        stream.stop_stream()
        stream.close()
        porcupine.delete()
        pa.terminate()

    if on_detected:
        on_detected()
    print("  [Wake word detected — listening…]", flush=True)

    audio = _record_until_silence()
    print("  [Transcribing…]", flush=True)
    return transcribe(audio)
