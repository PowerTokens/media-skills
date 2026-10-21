---
name: powertokens-product-ad
description: Produce a short vertical product ad (TikTok, Reels, Shorts, paid social, 9:16, 10-30 s) from a product photo and a few selling points — hook and script, storyboard, Seedream keyframes that keep the real product, image-to-video clips, voiceover, captions and an assembled MP4, through PowerTokens. Use when the user wants a product ad, promo video, e-commerce or Amazon/Shopify video, launch teaser, or "turn this product photo into a video ad".
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.0"
---

# Product ad (image → vertical ad)

Scripts: `scripts/pipeline.py` (+ video/image/speech). References:
`references/workflow.md` (detailed steps, hook formulas, storyboard template),
`references/checklist.md` (QA before delivery). Example: `examples/product-ad.json`.

## Workflow
1. **Brief** — product photo(s), name, 1–3 true selling points, audience, platform, CTA, length (default 15 s, 9:16). Ask only for what is missing.
2. **Script** — hook (≤ 2 s) → problem/desire → product moment → proof/benefit → CTA. 30–40 words VO for 15 s.
3. **Storyboard** — 4–6 shots of 2–4 s; one action + one camera move each; caption per shot. Show it as a table.
4. **Route** — drafts `wan3.0-video` 480p/720p; hero product turn `kling-v3` 1080p; see powertokens-model-routing.
5. **Keyframes** — Seedream with the real packshot as reference at 9:16 (`keyframe` in the shot list) so the product stays accurate.
6. **Shot list** → `validate` → `plan` → approval → `run`.
7. **Review clips**, offer single-shot re-takes (costs again).
8. **Assemble** — `pipeline.py assemble` (VO + ducked audio + burned captions). Then offer social variants (powertokens-social-variants).


## Product consistency (required)

Real SKUs often have fixed lid/thread mechanics that Seedream invents wrong (e.g. plastic pour on screw threads). Before spending:

1. Write a **product bible** JSON (`examples` pattern / `powertokens-product-qc`). List lid modes, forbid hybrids, colors, logos, proportions, 1–3 approved refs.
2. Set shot list `"kind": "product-ad"` and `"product_bible": "<file>.json"`.
3. Append `product_qc.py constraints` text into every keyframe prompt.
4. After each keyframe: vision QC via `product_qc.py vision-prompt` (chat model `MiniMax-M3` or glm-5.x) → one retry or human stop; hero frames get human OK before i2v.

Details: `powertokens-product-qc` and repo `docs/product-consistency-qc.md`.

## Before spending

- Credentials: `python3 scripts/pt_login.py status`. If not ok: `python3 scripts/pt_login.py login` (browser sign-in; if it says `LOGIN_UNAVAILABLE`, the user sets `POWERTOKENS_API_KEY` from https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills). Never ask for the key in chat.
- Always `pipeline.py validate` → `plan` → show the estimate table → wait for an explicit yes → `run --approve-estimate <total>`.
- `INSUFFICIENT_CREDITS` → stop and tell the user. Timeouts → run the same command again (resumes, no double charge).

Never invent product claims, prices, reviews, awards or certifications.
