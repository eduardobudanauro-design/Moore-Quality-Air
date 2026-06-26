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
- **Provider seam:** one thin function (`ask_brain`) — rest of code never imports the SDK directly
- **Streaming:** replies stream token-by-token from Tier 1 onward
- **Secrets:** all keys in `.env` (git-ignored), never in source

## Voice plan
- Tier 1–2: text only (terminal)
- Tier 3: push-to-talk via held key; Deepgram STT, ElevenLabs TTS — both behind seams
- Wake-word: post-baseline

## Runtime
- Laptop-first
- Heartbeat loop designed to relocate to always-on server without rewrite

## Hard limits — NEVER without explicit confirmation
- Send any message (email, SMS, DM, post)
- Spend money or trigger a charge
- Delete any data or file
- Change a setting, config, or credential
- Any action that is hard to reverse

## Proactive behavior
- Yes — Jarvis can reach out first
- Quiet by default: most checks produce nothing; only genuine urgency earns an interruption
- Notices held for Eduardo if interface is closed — never dropped
- Quiet hours respected (configurable)

## Project context
- Business: InsureTechABQ, DBA ABQ Growth Partners
- Revenue target: $8K/month
- Active projects tracked in notes; Jarvis helps create and ship them

## File layout (filled in as tiers complete)
```
jarvis/
  main.py          # entry point / conversation loop
  brain.py         # provider seam (ask_brain)
  tools/           # tool registry + individual tools
  memory/          # durable fact store
  heartbeat.py     # background scheduled-check loop
  config.yaml      # all tunable values (no hardcoded literals)
  .env             # secrets — git-ignored
```

## Tier status
- [ ] Tier 0 — Interview + spec (this file)
- [ ] Tier 1 — Text conversation loop
- [ ] Tier 2 — Tool registry + first real tools
- [ ] Tier 3 — Push-to-talk voice (Deepgram + ElevenLabs)
- [ ] Tier 4 — Memory across restarts
- [ ] Tier 5 — Heartbeat / proactive loop
- [ ] Tier 6 — Safety rails, confirmation gate, config, audit log
