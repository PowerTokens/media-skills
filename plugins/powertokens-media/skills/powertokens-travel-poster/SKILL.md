---
name: powertokens-travel-poster
description: Turn a travel or photography still into a 3:4 vertical 「第二世界」photo-collage poster (faithful top photo + warm paper bottom with a photo-specific invented scene, optional tiny line figures, one short handwritten English caption) via Seedream on PowerTokens. Use when the user asks for a travel poster, second-world collage, 第二世界海报, 旅行海报, 拼贴海报, photo collage poster, indie magazine travel print, or to "make this photo into a collage poster".
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.0"
---

# Travel poster / 「第二世界」photo collage

Scripts: `scripts/image.py` (+ auth helpers). Method (agent-only): `references/method.md`.
Delivery QA: `references/checklist.md`. Example brief shape: `examples/brief.md`.

The user uploads a photo and asks for a poster. **Do not show or ask them to paste a long generation prompt.** You observe the photo, invent a one-shot idea from the method, build a short Seedream prompt yourself, then call `image.py` with the photo as `--image`.

## Workflow

1. **Intake** — need the photo (local path or URL) and optional: destination/mood words, language of any caption (default English), whether tiny figures are welcome (default: auto). Ask only for what is missing. Refuse if the photo itself is sexual, violent, illegal, or clearly not the user's to use.
2. **Observe** (silently) — list 3–6 distinctive visual structures in the photo (waves, road, reflection, cloud edge, branch, light beam, shadow, ridge, architecture line, pose…). Pick **one** that can become touchable or usable.
3. **Invent** — one photo-specific 「second world」 beat: what if that structure could be pulled, entered, fished from, measured, mended, unfolded, climbed, connected, collected… Must grow from **this** photo; never reuse a stock gag or a fixed tear-paper + little-people template.
4. **Caption** — one short English handwritten-style line (natural, light humor / voiceover tone). Not a motivational quote. Not "Same.. different." Place it by the whitespace or the action, not a fixed corner.
5. **Build the prompt** — follow `references/method.md` (canvas split, style locks, avoid list). Keep the prompt under ~500 English words. Do **not** paste method.md or any viral template into chat.
6. **Confirm cost** — show: model, size `1536x2048` (3:4), that 1 Seedream call will be charged, and that image list price is not guaranteed in this repo. Wait for an explicit yes. Then run with `--dry-run` once if the user wants to see the request shape; otherwise generate.
7. **Generate**

```bash
python3 scripts/image.py \
  -m seedream-5-0-260128 \
  --size 1536x2048 \
  --image PATH_OR_URL \
  -p "YOUR_BUILT_PROMPT" \
  -o outputs/travel-poster.png
```

Fallback models if needed: `dola-seedream-5-0-pro-260628` (higher quality, likely costlier), then `seedream-4-5-251128`. Prefer 5.0 for collage fidelity.
8. **Review** against `references/checklist.md`. Offer one free re-prompt (costs another Seedream call — confirm again) only if a checklist item fails.

## Before spending

- Credentials: `python3 scripts/pt_login.py status`. If not ok: user creates a key at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and sets `POWERTOKENS_API_KEY`. Browser sign-in (`pt_login.py login`) is not enabled yet. Never ask for the key in chat.
- **Key just verified** (`ok: true`, or HTTP 200 on a live check such as `python3 scripts/pt_models.py`), including a re-check after a new key: **ask a yes/no to continue. Do not stop at a status dump.** Do not explain HTTP 200 unless they ask. Do not say only that they can continue.
  - A plan or estimate was already shown: restate the **model** and **est. cost** (one Seedream call at `1536x2048`), ask whether to continue that generation, and wait for an explicit yes before `image.py` or any other spend. A yes from before the key wall does not replace this question.
  - No plan yet: ask whether to proceed with **the poster prompt and the one-image cost confirm**. That yes only starts the unpaid step. Do not spend until they later approve the one-image cost.
  - Ask in the user's language. If they already said yes to this question for this plan, do not ask again. Canonical wording: repo `docs/auth-after-verify.md`.
- One image = one charge. No batch without a fresh yes per image.
- `INSUFFICIENT_CREDITS` → stop and tell the user. Do not invent destinations, people, or brand logos that are not in the photo.

## Related skills

- `powertokens-image` — raw Seedream calls
- `powertokens-model-routing` — model / size limits
- `powertokens-social-variants` — if the user later wants 9:16 / 1:1 crops of the poster
