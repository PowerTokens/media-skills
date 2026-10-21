---
name: powertokens-short-drama
description: Write and produce AI short dramas and multi-shot story videos (vertical micro-drama episodes, cliffhangers, narrative shorts, animated stories) with consistent characters across shots and episodes — beat sheet, shot list with 1-3 s cuts, character reference sheets reused in every shot, Seedance/Wan clips with dialogue, captions and assembly via PowerTokens. Use when the user wants a short drama, micro-drama, web series episode, story video, storyboard to video, or recurring characters.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.2"
---

# Short drama (multi-shot, consistent characters)

References: `references/workflow.md` (beat sheet, episode template, continuity),
`references/consistency.md` (character bible + reference image rules), `references/checklist.md`.
Example: `examples/short-drama.json`.

## Workflow
1. **Logline + episode goal** — one sentence; each episode ends on a hook/cliffhanger.
2. **Character bible** — per character: name, age, 3 fixed visual traits, outfit, optional `forbid` / refs. Set `"kind": "short-drama"` and either inline `characters` (description required) or `"character_bible": "character-bible.json"` (see `examples/character-bible.ning.json`). `pipeline validate` enforces the schema. This text is pasted into every shot via `characters`.
3. **Reference sheets** — Seedream: plain background, front view + close-up per character (user approves). Save under `refs/`.
4. **Beat sheet → shots** — 60–90 s episode ≈ 8–15 generated clips; timeline beats of 1–3 s inside 4–8 s Seedance clips (see powertokens-prompting timing-and-shots).
5. **Route** — drafts `seedance-fast` 720p; dialogue-heavy finals `seedance-2.5`; budget episodes `wan3.0-video` with reference mode.
6. Shot list → `validate` → `plan` → approval → `run` → review continuity → re-take single shots → `assemble` with dialogue captions.
7. For the next episode, reuse the same `characters` block and refs unchanged.

## Before spending

- Credentials: `python3 scripts/pt_login.py status`. If not ok: `python3 scripts/pt_login.py login` (browser sign-in; if it says `LOGIN_UNAVAILABLE`, the user sets `POWERTOKENS_API_KEY` from https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills). Never ask for the key in chat.
- Always `pipeline.py validate` → `plan` → show the estimate table → wait for an explicit yes → `run --approve-estimate <total>`.
- `INSUFFICIENT_CREDITS` → stop and tell the user. Timeouts → run the same command again (resumes, no double charge).
