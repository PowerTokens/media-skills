---
name: powertokens-short-drama
description: Write and produce AI short dramas and multi-shot story videos (vertical micro-drama episodes, cliffhangers, narrative shorts, animated stories) with consistent characters across shots and episodes — beat sheet, shot list with 1-3 s cuts, character reference sheets reused in every shot, Seedance/Wan clips with dialogue, captions and assembly via PowerTokens. Use when the user wants a short drama, micro-drama, web series episode, story video, storyboard to video, or recurring characters.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.4"
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
5. **Route** — default drafts `seedance-mini` 720p (4–15 s, max 720p, ~$0.031/s); step up to `seedance-fast` for a closer Seedance look; dialogue-heavy finals `seedance-2.5`. Use `wan3.0-video` only when you need 2–30 s, 1080p, or Wan reference mode.
6. Shot list → `validate` → `plan` → approval → `run` → review continuity → re-take single shots → `assemble` with dialogue captions burned in. Pass `--no-captions` only when the user explicitly asked for no burn-in or softsubs only. Before sharing the MP4, confirm JSON `captions_burned: true` and that each shot has `caption` text. If assemble warns that caption text is missing, fix the shot list and re-assemble. `captions.srt` is a sidecar, not the delivery.
7. For the next episode, reuse the same `characters` block and refs unchanged.

## Before spending

- Credentials: `python3 scripts/pt_login.py status`. If not ok: user creates a key at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and sets `POWERTOKENS_API_KEY`. Browser sign-in (`pt_login.py login`) is not enabled yet. Never ask for the key in chat.
- **Key just verified** (`ok: true`, or HTTP 200 on a live check such as `python3 scripts/pt_models.py`), including a re-check after a new key: **ask a yes/no to continue. Do not stop at a status dump.** Do not explain HTTP 200 unless they ask. Do not say only that they can continue.
  - A plan or estimate was already shown: restate the **model** and **est. cost**, ask whether to continue that generation, and wait for an explicit yes before `run` or any other spend. A yes from before the key wall does not replace this question.
  - No plan yet: ask whether to proceed with **the logline, character bible, or beat sheet, then `plan`**. That yes only starts the unpaid step. Do not spend until they later approve the estimate.
  - Ask in the user's language. If they already said yes to this question for this plan, do not ask again. Canonical wording: repo `docs/auth-after-verify.md`.
- Always `pipeline.py validate` → `plan` → show the estimate table → wait for an explicit yes → `run --approve-estimate <total>`.
- `INSUFFICIENT_CREDITS` → stop and tell the user. Timeouts → run the same command again (resumes, no double charge).
