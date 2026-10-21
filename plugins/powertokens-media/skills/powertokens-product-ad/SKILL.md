---
name: powertokens-product-ad
description: Produce a short vertical product ad (TikTok, Reels, Shorts, paid social, 9:16, 10-30 s) from a product URL and/or product photo — extract a claim sheet, get user approval, then hook/script, storyboard, Seedream keyframes that keep the real product, image-to-video clips, voiceover, captions and an assembled MP4, through PowerTokens. Use when the user wants a product ad, promo video, e-commerce or Amazon/Shopify video, launch teaser, pastes a product link, or says "turn this product photo into a video ad".
license: MIT
metadata:
  author: PowerTokens
  version: "0.3.3"
---

# Product ad (URL / image → vertical ad)

Scripts: `scripts/pipeline.py` (+ video/image/speech), `scripts/claim_sheet.py`. References:
`references/copy.md` (**required** — URL→claim sheet→confirm, hook reject list),
`references/workflow.md` (steps, storyboard template),
`references/checklist.md` (QA before delivery).
Examples: `examples/claim-sheet.json`, `examples/product-ad.json`.

## Workflow

1. **Intake** — accept a **product URL** and/or packshot(s), plus audience / platform / CTA / length (default 15 s, 9:16). Prefer URL when the user has a PDP.
2. **Extract claim sheet** — fetch the page (browser if the storefront is JS-heavy). Pull name, brand, price (optional), bullets/specs with numbers, hero image URLs. Write `claims.json` in the shape of `examples/claim-sheet.json`. Mark shaky lines `needs_confirm` or put them in `rejected_or_skipped` — **never invent**. Render with `python3 scripts/claim_sheet.py table claims.json`.
3. **User confirms claims** — show the table; wait for an explicit yes (or which ids to keep). Then `python3 scripts/claim_sheet.py approve claims.json --ids c1,c2 -o claims.approved.json`. **No keyframes / video spend before this.**
4. **Script from approved claims only** — hook (≤ 2 s) encodes a verified claim → problem/desire → product moment → proof → CTA. 30–40 words VO for 15 s. Captions = compressed claims (see `copy.md`).
5. **Storyboard** — 4–6 shots of 2–4 s; one action + one camera move each; caption per shot mapped to claim ids. Show as a table.
6. **Route** — drafts `wan3.0-video` 480p/720p; hero product turn `kling-v3` 1080p; see powertokens-model-routing.
7. **Keyframes** — Seedream with the real packshot as reference at 9:16 (`keyframe` in the shot list). Download hero images from the PDP when the user did not attach files (credit the URL in the bible refs).
8. **Shot list** → `validate` → `plan` → approval → `run`.
9. **Review clips**, offer single-shot re-takes (costs again).
10. **Assemble** — `pipeline.py assemble` (VO + ducked audio + burned captions, default kinetic style `tiktok` / A). Then offer social variants (powertokens-social-variants).

## Product consistency (required)

Real SKUs have fixed **structure/parts** that Seedream invents wrong (wrong closure, sole, zipper, ports, etc.). Before spending, build a generic product bible in order:

1. **Category → subtype → parts BOM** — identify 大类, 分型, then decompose `immutable.parts` `{id, role, how, states?}`. Write forbid from part risks; lock colors, logos, proportions, 1–3 refs (`powertokens-product-qc` / `examples/product-bible.*.json`).
2. Set shot list `"kind": "product-ad"` and `"product_bible": "<file>.json"`.
3. Append `product_qc.py constraints` text into every keyframe prompt.
4. After each keyframe: `pipeline.py run` vision QC (default on for product-ad; `MiniMax-M3` / glm-5.x) → one retry or stop (fail-closed if vision API down unless `--skip-vision-qc`); `hero: true` pauses until `approve-hero` (or `--auto-approve-hero`).

Details: `powertokens-product-qc` and repo `docs/product-consistency-qc.md`.

## Before spending

- Credentials: `python3 scripts/pt_login.py status`. If not ok: `python3 scripts/pt_login.py login` (browser sign-in; if it says `LOGIN_UNAVAILABLE`, the user sets `POWERTOKENS_API_KEY` from https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills). Never ask for the key in chat.
- Claim sheet must be `approved` (`claim_sheet.py validate` + user yes) before `plan` / `run`.
- Always `pipeline.py validate` → `plan` → show the estimate table → wait for an explicit yes → `run --approve-estimate <total>`.
- `INSUFFICIENT_CREDITS` → stop and tell the user. Timeouts → run the same command again (resumes, no double charge).

Never invent product claims, prices, reviews, awards or certifications.
