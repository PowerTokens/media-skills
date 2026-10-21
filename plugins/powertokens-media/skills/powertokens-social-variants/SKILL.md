---
name: powertokens-social-variants
description: Turn one PowerTokens video or campaign into platform variants and A/B tests — 9:16, 1:1, 16:9 crops or native regenerations, alternative hooks, caption and CTA variants, length cut-downs (6 s, 15 s, 30 s) — with cost estimates before any regeneration. Use when the user wants versions for TikTok, Reels, Shorts, YouTube, Instagram feed, X/LinkedIn, ad A/B testing, or "make this square/landscape".
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.1"
---

# Social variants and A/B hooks

Reference: `references/platforms.md` (ratios, safe zones, variant matrix).

## Choose the cheapest path per variant
1. **Reformat (free)** — `python3 scripts/pipeline.py reformat final.mp4 --ratio 1:1 --mode crop` (or `pad` to keep everything in frame). Good when the subject is centered.
2. **Regenerate natively (paid)** — copy the shot list, change `defaults.ratio`, re-run only shots where the crop loses the subject. Keyframes must be regenerated at the new ratio.
3. **Hook A/B (paid, small)** — duplicate the shot list with a different first shot + caption; other shots reuse finished clips (copy their `state.json` entries and clips) so only the hook is paid.
4. **Cut-downs (free)** — drop shots from the shot list and `assemble` again.

Always `plan` and get approval for any paid regeneration. Name outputs `<project>-<ratio>-<hook>.mp4` and give the user a table of variants.

## Before spending

- Credentials: `python3 scripts/pt_login.py status`. If not ok: `python3 scripts/pt_login.py login` (browser sign-in; if it says `LOGIN_UNAVAILABLE`, the user sets `POWERTOKENS_API_KEY` from https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills). Never ask for the key in chat.
- Always `pipeline.py validate` → `plan` → show the estimate table → wait for an explicit yes → `run --approve-estimate <total>`.
- `INSUFFICIENT_CREDITS` → stop and tell the user. Timeouts → run the same command again (resumes, no double charge).

When regenerating at a new ratio, remake Seedream keyframes at that ratio. Seedance first-frame i2v must not send `ratio`.
