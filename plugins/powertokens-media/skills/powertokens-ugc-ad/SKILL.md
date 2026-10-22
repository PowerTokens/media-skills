---
name: powertokens-ugc-ad
description: Make UGC-style and talking-head ads — selfie-style creator testimonials, unboxings, "I tried this" reviews, POV demos — with consistent on-camera characters, spoken lines with native audio (Seedance 2.5) or voiceover over b-roll, captions and A/B hooks, through PowerTokens. Use when the user asks for UGC, creator-style, testimonial, talking head, influencer-style, unboxing, or "TikTok ad that looks native".
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.2"
---

# UGC / talking-head ad

References: `references/workflow.md` (formats, scripts, two production routes),
`references/checklist.md`. Example: `examples/ugc-ad.json`.

## Workflow
1. **Brief** — product, real benefits, audience, persona (age/look/vibe), setting, CTA, length (15–30 s).
2. **Pick a format** — testimonial, unboxing, problem/solution, POV demo, "3 reasons".
3. **Script** — spoken, casual, short lines (≤ 10 words each), one line per shot.
4. **Persona** — make a character sheet with Seedream (neutral face + half body) and reuse it as `ref_image` in every shot. The persona must be fictional; do not imitate real people or claim it is a real customer.
5. **Choose route:**
   - *Native speech:* `dreamina-seedance-2-5-260628` with lines in double quotes, `audio: true`. Best feel; lip-sync quality is not verified here — review each take.
   - *VO over b-roll:* silent POV/hands/product shots on `seedance-mini` (cheapest, 4–15 s, max 720p, ~$0.031/s) + MiniMax voiceover. Use Wan when you need 1080p or a length outside 4–15 s.
6. Shot list → `validate` → `plan` → approval → `run` → `assemble` with captions (UGC lives on captions).
7. Offer 2–3 hook variants (re-generate only the hook shot).

## Before spending

- Credentials: `python3 scripts/pt_login.py status`. If not ok: user creates a key at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and sets `POWERTOKENS_API_KEY`. Browser sign-in (`pt_login.py login`) is not enabled yet. Never ask for the key in chat.
- **Key just verified** (`ok: true`, or HTTP 200 on a live check such as `python3 scripts/pt_models.py`), including a re-check after a new key: **ask a yes/no to continue. Do not stop at a status dump.** Do not explain HTTP 200 unless they ask. Do not say only that they can continue.
  - A plan or estimate was already shown: restate the **model** and **est. cost**, ask whether to continue that generation, and wait for an explicit yes before `run` or any other spend. A yes from before the key wall does not replace this question.
  - No plan yet: ask whether to proceed with **the brief, script, or shot list, then `plan`**. That yes only starts the unpaid step. Do not spend until they later approve the estimate.
  - Ask in the user's language. If they already said yes to this question for this plan, do not ask again. Canonical wording: repo `docs/auth-after-verify.md`.
- Always `pipeline.py validate` → `plan` → show the estimate table → wait for an explicit yes → `run --approve-estimate <total>`.
- `INSUFFICIENT_CREDITS` → stop and tell the user. Timeouts → run the same command again (resumes, no double charge).

Disclose AI-generated personas where the platform or law requires it; never fake reviews or results.

When the product pack is visible and must stay accurate, also follow `powertokens-product-qc` (or set `product_bible` on the shot list).
