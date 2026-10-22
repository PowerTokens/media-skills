---
name: powertokens-product-ad
description: Produce a short vertical product ad (TikTok, Reels, Shorts, paid social, 9:16, 10-30 s) from a product URL and/or product photo — extract a claim sheet, get user approval, then hook/script, storyboard, Seedream keyframes that keep the real product, image-to-video clips, voiceover, captions and an assembled MP4, through PowerTokens. Third-party consumer brands are forbidden as props (no MacBook, logos, or other brand-identifiable devices) unless that brand is the SKU or the user approved it. Use when the user wants a product ad, promo video, e-commerce or Amazon/Shopify video, launch teaser, pastes a product link, or says "turn this product photo into a video ad".
license: MIT
metadata:
  author: PowerTokens
  version: "0.3.9"
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
5. **Storyboard** — 4–6 shots; one action + one camera move each; caption per shot mapped to claim ids. On-screen cuts can be ~2–4 s; generate draft clips at 4–5 s (Mini's minimum) and trim in assembly. Show as a table.
6. **Route** — drafts `seedance-mini` (`dreamina-seedance-2-0-mini-260615`) at 480p or 720p, 4–15 s, ~$0.031/s (no 1080p); hero product turn `kling-v3` 1080p; see powertokens-model-routing.
7. **Keyframes** — Seedream with the real packshot as reference at 9:16 (`keyframe` in the shot list). Download hero images from the PDP when the user did not attach files (credit the URL in the bible refs).
8. **Shot list** → `validate` → `plan` → approval → `run`.
9. **Review clips**, offer single-shot re-takes (costs again).
10. **Assemble** — `pipeline.py assemble` (VO + ducked audio + burned captions). Caption burn style **defaults to A** (`tiktok`); override with `assembly.caption_style` / `captions.py --style` (`tiktok`|`pill`|`caps-punch`|`zh`) when the user asks or language needs it — same pattern as finish presets, not a hard lock. A content-policy block on one VO line does not cancel the cut: other lines stay, and assemble does **not** require every VO file once the user accepts a partial (`assemble --allow-partial-vo` — silence under the missing line, clip audio / their BGM remains). Ask first. Then offer social variants (powertokens-social-variants).

## Caption delivery (hard gate)

The file you hand the user is an MP4 with captions **burned into the picture**. `assemble` burns by default (style A / `tiktok` unless overridden).

Before sharing the final path:

1. Run `assemble` **without** `--no-captions`.
2. Confirm the JSON has `"captions_burned": true` and no `warning`.
3. Confirm every shot has caption text (`shots[].caption`, or the voiceover line for that shot copied onto `caption`) so the burn has content.

If caption text is missing, assemble still writes a clean plate, sets `captions_burned` to false, and emits a `warning` / `next_step`. Fill the shot list and re-assemble. That clean plate is not done.

`captions.srt` is a sidecar written next to the MP4. Shipping the SRT alone, or telling the user to open it, is incomplete unless they explicitly asked for softsubs only.

`--no-captions` stays for that explicit opt-out (no burn-in, or softsubs only). It still writes `captions.srt` and sets `captions_burned` to false. Pass it only when the user asked. Say that burn-in was skipped.

## Product consistency (required)

Real SKUs have fixed **structure/parts** that Seedream invents wrong (wrong closure, sole, zipper, ports, etc.). Before spending, build a generic product bible in order:

1. **Category → subtype → parts BOM** — identify 大类, 分型, then decompose `immutable.parts` `{id, role, how, states?}`. Write forbid from part risks; lock colors, logos, proportions, 1–5 refs (`powertokens-product-qc` / `examples/product-bible.*.json`). If a shot needs a separate part-detail ref (lid/sole/zipper/…), find it then **unify onto the hero product** — do not let a part-only crop rewrite body height or scene.
2. Set shot list `"kind": "product-ad"` and `"product_bible": "<file>.json"`.
3. Append `product_qc.py constraints` text into every keyframe prompt.
4. After each keyframe: `pipeline.py run` vision QC (default on for product-ad; `MiniMax-M3` / glm-5.x) → one retry or stop (fail-closed if vision API down unless `--skip-vision-qc`); `hero: true` pauses until `approve-hero` (or `--auto-approve-hero`).

### Third-party brands as props (hard rule)

Forbidden by default in keyframes, i2v clips, VO / captions / end-cards that name them, and finish overlays.

- **Cover:** logos, wordmarks, packaging, and devices or products that are clearly a specific brand (Apple MacBook / iPhone / logo; Nike swoosh; Starbucks cup mark; Amazon smile; Google/Microsoft hardware logos).
- **OK:** generic unbranded props (plain silver laptop with no logo or chin text, blank phone bezel, plain mug).
- **Exception only when** (a) the advertised SKU is that brand, or (b) the user explicitly says they have rights or want that brand shown.
- **Bible / prompts / rubric:** always add this to `immutable.forbid` (Seedream and i2v prompts also get it from `product_qc.py constraints`): `no third-party logos, wordmarks, or brand-identifiable devices (MacBook, iPhone, etc.) unless approved`.
- **QC / delivery:** if a still or clip shows a third-party mark or brand-identifiable device, fail `logo_policy_ok` and regenerate or ask — do not ship. Rewrite the prop to a generic stand-in.

Do not write legal-advice copy. Forbid the prop and rewrite it.

Details: `powertokens-product-qc` and repo `docs/product-consistency-qc.md`.

## Before spending

- Credentials: `python3 scripts/pt_login.py status`. If not ok: user creates a key at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and sets `POWERTOKENS_API_KEY`. Browser sign-in (`pt_login.py login`) is not enabled yet. Never ask for the key in chat.
- **Key just verified** (`ok: true`, or HTTP 200 on a live check such as `python3 scripts/pt_models.py`), including a re-check after a new key: **ask a yes/no to continue. Do not stop at a status dump.** Do not explain HTTP 200 unless they ask. Do not say only that they can continue.
  - A plan or estimate was already shown: restate the **model** and **est. cost**, ask whether to continue that generation, and wait for an explicit yes before `run` or any other spend. A yes from before the key wall does not replace this question.
  - No plan yet: ask whether to proceed with **intake, the claim sheet, or the storyboard — whichever is still open — then `plan`**. That yes only starts the unpaid step. Do not spend until they later approve the estimate.
  - Ask in the user's language. If they already said yes to this question for this plan, do not ask again. Canonical wording: repo `docs/auth-after-verify.md`.
- Claim sheet must be `approved` (`claim_sheet.py validate` + user yes) before `plan` / `run`.
- **Look (light touch):** default finish preset `clean-premium` (干净商业). When showing the spend estimate, one short line is enough — e.g. "默认干净商业风；要 UGC / 更电影感可以说一声." Only switch to `ugc-punchy` / `cinematic` if the user asks; do not force a three-way picker.
- Always `pipeline.py validate` → `plan` → show the estimate table → wait for an explicit yes → `run --approve-estimate <total>`.
- **EN voiceover, before spend:** say that every VO line is an original product claim from the approved claim sheet — not song lyrics, a brand slogan copied verbatim, a celebrity endorsement, or a long copyrighted quote. One MiniMax call per line (`voiceover.lines[]`). If a line comes back `CONTENT_POLICY`, follow `references/copy.md` (rewrite that line once, continue the others, ask before a partial assemble).
- `INSUFFICIENT_CREDITS` → stop and tell the user. Timeouts → run the same command again (resumes, no double charge). `CONTENT_POLICY` on one segment does not abort the job.

Never invent product claims, prices, reviews, awards or certifications.
