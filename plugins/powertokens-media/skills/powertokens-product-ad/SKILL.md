---
name: powertokens-product-ad
description: Produce a short vertical product ad (TikTok, Reels, Shorts, paid social, 9:16, 10-30 s) from a product photo and a few selling points — hook and script, storyboard, Seedream keyframes that keep the real product, image-to-video clips, voiceover, captions and an assembled MP4, through PowerTokens. Use when the user wants a product ad, promo video, e-commerce or Amazon/Shopify video, launch teaser, or "turn this product photo into a video ad".
license: MIT
metadata:
  author: PowerTokens
  version: "0.3.2"
---

# Product ad (image → vertical ad)

Scripts: `scripts/pipeline.py` (+ video/image/speech). References:
`references/copy.md` (**required** — claim sources, hook/caption reject list),
`references/workflow.md` (steps, storyboard template),
`references/checklist.md` (QA before delivery). Example: `examples/product-ad.json`.

## Workflow
1. **Brief** — product photo(s), name, audience, platform, CTA, length (default 15 s, 9:16). Collect **1–3 true selling points with sources** (user / PDP / pack). If benefits are vague, ask — do not invent numbers or praise.
2. **Claim sheet + script** — build `claim | source | where used` (see `references/copy.md`). Hook (≤ 2 s) must encode a verified claim, not mood. Then problem/desire → product moment → proof → CTA. 30–40 words VO for 15 s. Show the claim sheet; wait for yes before spending.
3. **Storyboard** — 4–6 shots of 2–4 s; one action + one camera move each; **caption = compressed claim** (not a scene title). Show it as a table with captions + VO mapped to claim rows.
4. **Route** — drafts `wan3.0-video` 480p/720p; hero product turn `kling-v3` 1080p; see powertokens-model-routing.
5. **Keyframes** — Seedream with the real packshot as reference at 9:16 (`keyframe` in the shot list) so the product stays accurate.
6. **Shot list** → `validate` → `plan` → approval → `run`.
7. **Review clips**, offer single-shot re-takes (costs again).
8. **Assemble** — `pipeline.py assemble` (VO + ducked audio + burned captions). Then offer social variants (powertokens-social-variants).


## Product consistency (required)

Real SKUs have fixed **structure/parts** that Seedream invents wrong (wrong closure, sole, zipper, ports, etc.). Before spending, build a generic product bible in order:

1. **Category → subtype → parts BOM** — identify 大类, 分型, then decompose `immutable.parts` `{id, role, how, states?}`. Write forbid from part risks; lock colors, logos, proportions, 1–3 refs (`powertokens-product-qc` / `examples/product-bible.*.json`).
2. Set shot list `"kind": "product-ad"` and `"product_bible": "<file>.json"`.
3. Append `product_qc.py constraints` text into every keyframe prompt.
4. After each keyframe: `pipeline.py run` vision QC (default on for product-ad; `MiniMax-M3` / glm-5.x) → one retry or stop (fail-closed if vision API down unless `--skip-vision-qc`); `hero: true` pauses until `approve-hero` (or `--auto-approve-hero`).

Details: `powertokens-product-qc` and repo `docs/product-consistency-qc.md`.

## Before spending

- Credentials: `python3 scripts/pt_login.py status`. If not ok: `python3 scripts/pt_login.py login` (browser sign-in; if it says `LOGIN_UNAVAILABLE`, the user sets `POWERTOKENS_API_KEY` from https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills). Never ask for the key in chat.
- Always `pipeline.py validate` → `plan` → show the estimate table → wait for an explicit yes → `run --approve-estimate <total>`.
- `INSUFFICIENT_CREDITS` → stop and tell the user. Timeouts → run the same command again (resumes, no double charge).

Never invent product claims, prices, reviews, awards or certifications.
