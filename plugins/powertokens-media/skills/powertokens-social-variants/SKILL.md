---
name: powertokens-social-variants
description: Turn one PowerTokens video or campaign into platform variants and A/B tests — 9:16, 1:1, 16:9 crops or native regenerations, alternative hooks, caption and CTA variants, length cut-downs (6 s, 15 s, 30 s) — with cost estimates before any regeneration. Use when the user wants versions for TikTok, Reels, Shorts, YouTube, Instagram feed, X/LinkedIn, ad A/B testing, or "make this square/landscape".
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.2"
---

# Social variants and A/B hooks

Reference: `references/platforms.md` (ratios, safe zones, variant matrix).

## Choose the cheapest path per variant
1. **Reformat (free)** — `python3 scripts/pipeline.py reformat final.mp4 --ratio 1:1 --mode crop` (or `pad` to keep everything in frame). Good when the subject is centered.
2. **Regenerate natively (paid)** — copy the shot list, change `defaults.ratio`, re-run only shots where the crop loses the subject. Keyframes must be regenerated at the new ratio.
3. **Hook A/B (paid, small)** — duplicate the shot list with a different first shot + caption; other shots reuse finished clips (copy their `state.json` entries and clips) so only the hook is paid.
4. **Cut-downs (free)** — drop shots from the shot list and `assemble` again, still with captions burned in. Pass `--no-captions` only when the user explicitly asked for no burn-in or softsubs only. Confirm `captions_burned: true` before sharing the cut.

Always `plan` and get approval for any paid regeneration. Name outputs `<project>-<ratio>-<hook>.mp4` and give the user a table of variants.

## Before spending

- Credentials: `python3 scripts/pt_login.py status`. If not ok: user creates a key at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and sets `POWERTOKENS_API_KEY`. Browser sign-in (`pt_login.py login`) is not enabled yet. Never ask for the key in chat.
- **Key just verified** (`ok: true`, or HTTP 200 on a live check such as `python3 scripts/pt_models.py`), including a re-check after a new key: **ask a yes/no to continue. Do not stop at a status dump.** Do not explain HTTP 200 unless they ask. Do not say only that they can continue.
  - A plan or estimate was already shown: restate the **model** and **est. cost**, ask whether to continue that generation, and wait for an explicit yes before `run` or any other spend. A yes from before the key wall does not replace this question.
  - No plan yet: ask whether to proceed with **a free reformat vs a paid regen, then `plan` for anything paid**. That yes only starts the unpaid step. Do not spend until they later approve the estimate.
  - Ask in the user's language. If they already said yes to this question for this plan, do not ask again. Canonical wording: repo `docs/auth-after-verify.md`.
- Always `pipeline.py validate` → `plan` → show the estimate table → wait for an explicit yes → `run --approve-estimate <total>`.
- `INSUFFICIENT_CREDITS` → stop and tell the user. Timeouts → run the same command again (resumes, no double charge).

When regenerating at a new ratio, remake Seedream keyframes at that ratio. Seedance first-frame i2v must not send `ratio`.
