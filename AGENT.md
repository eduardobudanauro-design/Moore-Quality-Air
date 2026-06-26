# Jarvis — Agent Spec

## Identity
- **Name:** Jarvis
- **Mission:** Help Eduardo hit $8K/month through InsureTechABQ (DBA ABQ Growth Partners)
- **Personality:** Warm, casual, direct — like a sharp friend who's also your business partner

## Who it's for
Just Eduardo. Single-user. Per-user state design not required yet.

## First Three Capabilities (become first tools + test cases)
1. **Reminders & follow-ups** — log a thing to remember, surface it at the right time
2. **Notes Q&A** — store notes and answer questions about them in plain English
3. **Project creation assist** — help draft, build, and iterate on websites, apps, books, and any other project Eduardo is working on under InsureTechABQ / ABQ Growth Partners

## Stack
- **Language:** Python 3.11+
- **AI Provider:** Anthropic SDK — latest capable Claude model (claude-sonnet-4-6 or newer)
- **Provider seam:** one thin function (`ask_brain_stream`) — rest of code never imports the SDK directly
- **Streaming:** replies stream token-by-token from Tier 1 onward
- **Secrets:** all keys in `.env` (git-ignored), never in source

## Voice plan
- Tier 1–2: text only (terminal)
- Tier 3: push-to-talk (hold spacebar) + open-mic wake word ("Hey Jarvis") in same tier
  - STT: Deepgram (fast, streaming, behind a seam)
  - TTS: ElevenLabs (natural voice, streaming, behind a seam)
  - Both text path and voice path remain alive forever
- Wake word: built in Tier 3 using `pvporcupine` (offline, no network latency)

## Runtime
- Primary: iMac (desktop) + MacBook (laptop) — both macOS
- Same codebase runs on both; no machine-specific code
- Heartbeat loop designed to relocate to always-on server without rewrite

## Hard limits — NEVER without explicit confirmation
- Spend money or trigger any charge
- Delete any data or file
- Change a setting, config, or credential
- Any action that is hard to reverse

## What Jarvis CAN do freely (no confirmation needed)
- Send messages, emails, DMs, posts on Eduardo's behalf
- Read/search/retrieve any data
- Create or save new content (notes, drafts, files)

## Proactive behavior
- Yes — Jarvis can reach out first
- Quiet by default: most checks produce nothing; only genuine urgency earns an interruption
- Notices held for Eduardo if interface is closed — never dropped
- Quiet hours respected (configurable in config.yaml)

## Project context
- Business: InsureTechABQ, DBA ABQ Growth Partners
- Revenue target: $8K/month
- Active projects tracked in notes; Jarvis helps create and ship them

## File layout
```
jarvis/
  main.py          # entry point / conversation loop (text + voice)
  brain.py         # provider seam (ask_brain_stream)
  voice/
    input.py       # push-to-talk + wake word → text
    output.py      # text → speech (ElevenLabs)
  tools/           # tool registry + individual tools
    __init__.py    # @tool decorator, registry, run_tool()
    notes.py       # save_note, list_notes, search_notes, mark_note_done
  memory/          # durable fact store (plain JSON, human-editable)
  heartbeat.py     # background scheduled-check loop
  config.yaml      # all tunable values (no hardcoded literals)
  .env             # secrets — git-ignored
  jarvis.log       # audit trail — git-ignored
```

## Tier status
- [x] Tier 0 — Interview + spec (this file)
- [x] Tier 1 — Text conversation loop (streaming, error-safe, history)
- [x] Tier 2 — Tool registry + notes tools (save, list, search, mark done)
- [x] Tier 3 — Push-to-talk (spacebar) + wake word "Jarvis" (Deepgram STT + ElevenLabs TTS — Daniel voice)
- [x] Tier 4 — Memory across restarts (durable fact store, auto-loaded into system prompt)
- [x] Tier 5 — Heartbeat / proactive loop (scheduled checks, durable inbox, kill switch)
- [ ] Tier 6 — Safety rails, confirmation gate, config, audit log
