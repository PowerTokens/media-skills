---
name: powertokens-bilingual-voiceover
description: Create English and Chinese (Mandarin/Cantonese) voiceovers and dubbed versions of a video with MiniMax speech through PowerTokens — translate and adapt the script for timing, pick matching voices, generate per-line audio, swap captions, and assemble EN and ZH cuts of the same visuals. Use when the user wants bilingual, Chinese, English, localized or dubbed voiceover, 中文配音, 英文配音, or the same ad in two languages.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.1"
---

# Bilingual EN/ZH voiceover

Reference: `references/adaptation.md` (timing, voice pairs, caption rules). Example: `examples/bilingual-vo.json`.

## Workflow
1. Start from the finished shot list (or a script). Keep visuals identical; only VO and captions change.
2. **Adapt, don't translate literally** — match each line's duration: EN ≈ 2.5 words/s, ZH ≈ 4–5 characters/s. Show EN and ZH side by side for approval.
3. **Pick a voice pair** (see reference). Test one line per voice first (`speech.py`, cheap) before the whole script.
4. Make a language copy of the shot list: `<project>-zh.json` with `project` renamed, `voiceover.lines` and each shot's `caption` in Chinese. Copy the finished clips and the shots part of `state.json` into the new workdir so no video is regenerated.
5. `pipeline.py run --approve-estimate 0` (video estimate is 0 when all clips exist; only VO is generated — tell the user VO is billed per character) → `assemble`.
6. Deliver both files and both SRTs.

## Before spending

- Credentials: `python3 scripts/pt_login.py status`. If not ok: `python3 scripts/pt_login.py login` (browser sign-in; if it says `LOGIN_UNAVAILABLE`, the user sets `POWERTOKENS_API_KEY` from https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills). Never ask for the key in chat.
- Always `pipeline.py validate` → `plan` → show the estimate table → wait for an explicit yes → `run --approve-estimate <total>`.
- `INSUFFICIENT_CREDITS` → stop and tell the user. Timeouts → run the same command again (resumes, no double charge).

Captions in Chinese need a CJK font on the machine for burning (e.g. Noto Sans CJK); set `assembly.caption_style` FontName accordingly, or deliver the SRT unburned (`--no-captions`).

Do not invent product claims when adapting EN↔ZH; keep meaning and length, not marketing upgrades.
