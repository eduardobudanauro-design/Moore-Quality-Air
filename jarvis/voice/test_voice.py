"""Quick voice diagnostic — run with: python jarvis/voice/test_voice.py"""
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')
import httpx
import pyaudio

key = os.environ.get("ELEVENLABS_API_KEY")
print(f"ElevenLabs key found: {'YES' if key else 'NO'}")
if not key:
    raise SystemExit("Add ELEVENLABS_API_KEY to jarvis/.env and try again.")

voice_id = "onwK4e9ZLuTAKqWW03F9"

print("Calling ElevenLabs API...")
response = httpx.post(
    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
    headers={"xi-api-key": key, "Content-Type": "application/json"},
    json={"text": "Hello Eduardo, Jarvis is online.", "model_id": "eleven_turbo_v2"},
    timeout=30,
)

print(f"HTTP status: {response.status_code}")
print(f"Content-Type: {response.headers.get('content-type')}")
print(f"Audio bytes received: {len(response.content)}")

if response.status_code != 200:
    raise SystemExit(f"Error: {response.text[:300]}")

print("Decoding MP3 via ffmpeg...")
result = subprocess.run(
    ["ffmpeg", "-y", "-i", "pipe:0", "-f", "s16le", "-ar", "44100", "-ac", "1", "pipe:1"],
    input=response.content,
    capture_output=True,
)
pcm = result.stdout
print(f"PCM bytes: {len(pcm)}")
if not pcm:
    raise SystemExit(f"ffmpeg error: {result.stderr.decode()[-300:]}")

print("Playing audio...")
pa = pyaudio.PyAudio()
stream = pa.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True)
stream.write(pcm)
stream.stop_stream()
stream.close()
pa.terminate()
print("Done.")
