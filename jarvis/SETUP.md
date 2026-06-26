# Jarvis — Setup Guide (macOS iMac / MacBook)

## 1. Prerequisites

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# PortAudio is required by PyAudio for mic/speaker access
brew install portaudio
```

## 2. Python environment

```bash
cd jarvis
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. API keys

Copy the example and fill in your real keys:
```bash
cp .env.example .env
```

Edit `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
DEEPGRAM_API_KEY=...          # get free key at deepgram.com
ELEVENLABS_API_KEY=...        # get key at elevenlabs.io
PICOVOICE_API_KEY=...         # get free key at picovoice.ai (for wake word)
```

## 4. macOS permissions

The first time you run voice mode, macOS will ask for:
- **Microphone access** — allow it for Terminal (or your terminal app)
- **Accessibility access** — allow it for push-to-talk keyboard listening (System Settings → Privacy & Security → Accessibility)

## 5. Run Jarvis

```bash
# Text mode (no API keys needed except Anthropic)
python main.py

# Push-to-talk voice mode
python main.py --voice ptt

# Wake-word mode (say "Jarvis" to activate)
python main.py --voice wake
```

## 6. Voice details

- **Push-to-talk key:** SPACEBAR — hold while speaking, release when done
- **Wake word:** "Jarvis" — detected offline by Porcupine (no audio sent anywhere)
- **Voice:** Daniel — deep British male (ElevenLabs)
  - To change: update `voice.tts_voice_id` in `config.yaml` with any ElevenLabs voice ID
- **Transcript:** printed next to each reply so you can see what Jarvis heard

## 7. Running on both iMac and MacBook

Same setup on both machines. The only thing that differs per machine:
- The `.env` file (each machine keeps its own — never commit this)
- The `memory/` folder (notes and facts are local; future Tier 4/5 work can sync these)

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `ANTHROPIC_API_KEY is not set` | Check `.env` exists in `jarvis/` and the key is correct |
| `PyAudio` install fails | Run `brew install portaudio` first |
| Keyboard listener blocked | Grant Accessibility permission in System Settings |
| Wake word never fires | Try increasing `wake_word_sensitivity` in `config.yaml` (toward 1.0) |
| Jarvis sounds robotic | Confirm `ELEVENLABS_API_KEY` is set; free tier has character limits |
