---
name: powertokens-bilingual-voiceover
description: Create English and Chinese (Mandarin/Cantonese) voiceovers and dubbed versions of a video with MiniMax speech through PowerTokens — translate and adapt the script for timing, pick matching voices, generate per-line audio, swap captions, and assemble EN and ZH cuts of the same visuals. Use when the user wants bilingual, Chinese, English, localized or dubbed voiceover, 中文配音, 英文配音, or the same ad in two languages.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.2"
---

# Bilingual EN/ZH voiceover

Reference: `references/adaptation.md` (timing, voice pairs, caption rules). Example: `examples/bilingual-vo.json`.

## Workflow
1. Start from the finished shot list (or a script). Keep visuals identical; only VO and captions change.
2. **Adapt, don't translate literally** — match each line's duration: EN ≈ 2.5 words/s, ZH ≈ 4–5 characters/s. Show EN and ZH side by side for approval.
3. **Pick a voice pair** (see reference). Test one line per voice first (`speech.py`, cheap) before the whole script.
4. Make a language copy of the shot list: `<project>-zh.json` with `project` renamed, `voiceover.lines` and each shot's `caption` in Chinese. Copy the finished clips and the shots part of `state.json` into the new workdir so no video is regenerated.
5. `pipeline.py run --approve-estimate 0` (video estimate is 0 when all clips exist; only VO is generated — tell the user VO is billed per character) → `assemble` with captions burned in. Pass `--no-captions` only when the user explicitly asked for softsubs only.
6. Deliver both MP4s with captions burned in (`captions_burned: true` on each). Each `captions.srt` is a sidecar, not a substitute for burn-in.

## Before spending

- Credentials: `python3 scripts/pt_login.py status`. If not ok: user creates a key at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and sets `POWERTOKENS_API_KEY`. Browser sign-in (`pt_login.py login`) is not enabled yet. Never ask for the key in chat.
- **Key just verified** (`ok: true`, or HTTP 200 on a live check such as `python3 scripts/pt_models.py`), including a re-check after a new key: **ask a yes/no to continue. Do not stop at a status dump.** Do not explain HTTP 200 unless they ask. Do not say only that they can continue.
  - A plan or estimate was already shown: restate the **model** and **est. cost**, ask whether to continue that generation, and wait for an explicit yes before `run` or any other spend. A yes from before the key wall does not replace this question.
  - No plan yet: ask whether to proceed with **the EN/ZH line pair for approval, then `plan`**. That yes only starts the unpaid step. Do not spend until they later approve the estimate.
  - Ask in the user's language. If they already said yes to this question for this plan, do not ask again. Canonical wording: repo `docs/auth-after-verify.md`.
- Always `pipeline.py validate` → `plan` → show the estimate table → wait for an explicit yes → `run --approve-estimate <total>`.
- `INSUFFICIENT_CREDITS` → stop and tell the user. Timeouts → run the same command again (resumes, no double charge).

Captions in Chinese need a CJK font on the machine for burning (e.g. Noto Sans CJK); set `assembly.caption_style` FontName accordingly. If that font is missing, say so and only then use `--no-captions` (SRT only) as a fallback, and say burn-in was skipped. For product-ad, UGC, and short-drama cuts, the normal delivery is still an MP4 with captions burned in.

Do not invent product claims when adapting EN↔ZH; keep meaning and length, not marketing upgrades.
