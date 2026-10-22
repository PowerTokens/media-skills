---
name: powertokens-image
description: Generate images from text, or edit and restyle images from reference pictures, with ByteDance Seedream through the PowerTokens API, and save them locally. Use when the user asks to create, generate or draw an image, picture, poster, product shot, thumbnail, illustration or storyboard frame, or names Seedream.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.1"
---

# PowerTokens image

Scripts are in `scripts/` next to this file (`python3` 3.8+, stdlib only). Outputs default to `./outputs/`.

## Credentials (check first)

Run `python3 scripts/pt_login.py status`.

- `ok: false` → the user needs a PowerTokens API key. They create one at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and set `POWERTOKENS_API_KEY` in their shell. New users sign up at https://powertokens.ai/?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills.
  Browser sign-in (`pt_login.py login`) is not enabled yet; it will come in a later release when PowerTokens publishes OAuth.
- `ok: true`, or a live check such as `python3 scripts/pt_models.py` returns HTTP 200 — including a re-check after a new key: **ask a yes/no to continue. Do not stop at a status dump.** Do not explain HTTP 200 unless they ask. Do not say only that they can continue.
  - A plan or estimate was already shown: restate the **model** and **est. cost**, ask whether to continue that generation, and wait for an explicit yes before `run`, `generate`, or any other spend. A yes from before the key wall does not replace this question.
  - No plan yet: ask whether to proceed with **confirming the prompt and size**. That yes only starts the unpaid step. Do not spend until they later approve the estimate.
  - Ask in the user's language. If they already said yes to this question for this plan, do not ask again. Canonical wording: repo `docs/auth-after-verify.md`.

Never ask the user to paste a key into the chat, never write a key into files, never print it.

## Errors

Scripts print JSON. On failure read `error_type`:
`NO_CREDENTIAL`/`AUTH` → credentials step above · `INSUFFICIENT_CREDITS` → tell the user to top up (link in `next_step`), do not retry · `BAD_REQUEST` → fix the arguments · `CONTENT_POLICY` → the prompt tripped a content/safety filter; rewrite it, do not send the same text again · `RATE_LIMIT`/`NETWORK` → wait and retry once.

## Generate

```bash
python3 scripts/image.py -p "PROMPT" --size 2K -o outputs/hero.png
# portrait 9:16 (pixel sizes must total at least 2560x1440 pixels for Seedream 4.5)
python3 scripts/image.py -p "PROMPT" --size 1440x2560
# use reference images (product photo, character sheet); repeat --image up to 14 times
python3 scripts/image.py -p "the same bottle on a sunny beach" --image bottle.png
# a consistent set (e.g. 4 storyboard frames)
python3 scripts/image.py -p "4 frames: ..." -n 4
```

Default model `seedream-4-5-251128`; others: `seedream-5-0-260128`, `dola-seedream-5-0-pro-260628` (`--list-models`). Use `--dry-run` to see the request without spending. Report the saved paths from `outputs`.

Prompt tips: subject, setting, composition, lighting, style, and any exact text in quotes. Keep it under ~600 English words.

These images make good first frames for the `powertokens-video` skill (`video.py generate -i <image>`).

## Related skills

- `powertokens-model-routing` — which model to use and what it costs
- `powertokens-prompting` — prompt structure, camera language, failure fixes
- `powertokens-pipeline` — more than one clip, storyboards, final assembly
