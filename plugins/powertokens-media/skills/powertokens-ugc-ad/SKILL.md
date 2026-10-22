---
name: powertokens-ugc-ad
description: Make a phone-native vertical UGC ad — testimonial, unboxing, problem/solution, POV demo, or three-reasons — with a fictional persona or hands-only b-roll, short spoken lines, burned-in captions, and hook variants, through PowerTokens. Use when the user asks for UGC, creator-style, talking-head, influencer-style, unboxing, testimonial, or a TikTok ad that looks filmed on a phone. NOT for a packshot commercial or product-URL claim-sheet ad (powertokens-product-ad), a multi-shot story episode (powertokens-short-drama), a single clip with no ad beats (powertokens-video), or a desktop GUI editor.
license: MIT
metadata:
  author: PowerTokens
  version: "0.3.1"
---

# UGC / talking-head ad

This is a procedure. Do the steps in order. Load a reference only when that step says so.

- Category beats: `references/beats.md`
- Prompt words and the two routes: `references/workflow.md`
- What breaks and how to recover: `references/failures.md`
- Delivery checklist: `references/checklist.md`
- Optional watch-the-MP4 pass: `references/qc.md`
- Example shot list: `examples/ugc-ad.json`

Distinct from `powertokens-product-ad` (packshot commercial from a URL and claim sheet). If the pack must stay accurate while a person is also on camera, still run this procedure and add a product bible from `powertokens-product-qc`.

## Procedure

1. **Brief (free).** Product, sourced benefits, audience, length (15–30 s, 9:16), CTA, and whether a face is on camera. Persona is fictional: age, look, outfit, setting. Do not imitate a real person or call them a real customer.
2. **Pick one category** and copy its beat recipe from `references/beats.md` (testimonial, unboxing, problem/solution, POV demo, three-reasons). Do not invent a sixth structure unless the user asked for one.
3. **Script.** Spoken, casual, one line per shot, about 10 words or fewer. Hooks and captions must map to a sourced claim from the product-ad copy brief. Reject mood-only lines.
4. **Character bible, before any still or clip.** If a face or named persona is on camera, write `character_bible` or inline `characters` with a non-empty `description` (traits, outfit, `forbid`, `ref_image`). Set `"kind": "ugc-ad"`. `pipeline.py validate` refuses without that bible. Hands-only / no face: set `"characters_on_camera": false` and do not put character ids or `on_camera` on shots. A false flag does not waive a shot that lists a person.
5. **Persona still (paid, only after the cost gate below).** Seedream, neutral face + half body, plain background. Reuse that file as `ref_image` on every face shot. Same description words every shot.
6. **Route.**
   - *Native speech:* `dreamina-seedance-2-5-260628`, line in double quotes, `audio: true`. Lip-sync is not verified here — review every take.
   - *VO over b-roll (default video):* silent hands/product shots on `seedance-mini` (4–15 s, max 720p, ~$0.031/s) plus MiniMax `speech-2.8-turbo`. Use Wan only for 1080p or a length outside 4–15 s. Use `speech-2.8-hd` only if the user asks. One MiniMax call per line. A `CONTENT_POLICY` block stays on that line: rewrite once, ask, and do not drop the other lines (`references/workflow.md`).
7. **Shot list → cost gate → spend → assemble.** Details in **Cost gate**. Then `assemble` with captions burned in. `--no-captions` only when the user explicitly asked for softsubs only. Before sharing the MP4, confirm JSON `captions_burned: true` and that each shot has `caption` text (or the spoken line copied onto the shot). A `warning` means fix and re-assemble. `captions.srt` is a sidecar.
8. **Offer 2–3 hook variants** only if they want them (re-generate the hook shot; say it costs again).
9. **Optional QC.** After assemble, walk `references/qc.md` if they want a watch-pass. It does not replace the delivery checklist.

## Cost gate (before any paid call)

Paid calls are Seedream persona/keyframes, Seedance/Wan/Kling clips, and MiniMax speech. Do not start them from a chat guess.

1. `python3 scripts/pipeline.py validate shots.json` — free. Fix every error, including a missing character bible.
2. `python3 scripts/pipeline.py plan shots.json` — free. Read the table: shots, model, seconds, est. USD, and items with no price (keyframes, speech billed per character).
3. Show that table. Wait for an explicit yes. A yes to "draft the script" is not a yes to spend.
4. `python3 scripts/pipeline.py run shots.json --approve-estimate <video_est_usd>`. The script refuses if the number does not match the current plan.
5. A one-line voice test is still a speech call. Name `speech-2.8-turbo`, say billing is per character, and wait for yes before that call too.

`INSUFFICIENT_CREDITS` → stop and tell the user. Timeouts → run the same command again (resumes, no double charge).

## Credentials

- `python3 scripts/pt_login.py status`. If not ok: user creates a key at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and sets `POWERTOKENS_API_KEY`. Browser sign-in (`pt_login.py login`) is not enabled yet. Never ask for the key in chat.
- **Key just verified** (`ok: true`, or HTTP 200 on a live check such as `python3 scripts/pt_models.py`), including a re-check after a new key: **ask a yes/no to continue. Do not stop at a status dump.** Do not explain HTTP 200 unless they ask. Do not say only that they can continue.
  - A plan or estimate was already shown: restate the **model** and **est. cost**, ask whether to continue that generation, and wait for an explicit yes before `run` or any other spend. A yes from before the key wall does not replace this question.
  - No plan yet: ask whether to proceed with **the brief, script, or shot list, then `plan`**. That yes only starts the unpaid step. Do not spend until they later approve the estimate.
  - Ask in the user's language. If they already said yes to this question for this plan, do not ask again. Canonical wording: repo `docs/auth-after-verify.md`.

Disclose AI-generated personas where the platform or law requires it. Never fake reviews, awards, or results.

When the product pack is readable on camera, also set `product_bible` (`powertokens-product-qc`).
