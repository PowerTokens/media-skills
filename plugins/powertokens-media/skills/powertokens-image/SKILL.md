---
name: powertokens-image
description: Generate images from text, or edit and restyle images from reference pictures, with ByteDance Seedream through the PowerTokens API, and save them locally. Use when the user asks to create, generate or draw an image, picture, poster, product shot, thumbnail, illustration or storyboard frame, or names Seedream.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.0"
---

# PowerTokens image

Scripts are in `scripts/` next to this file (`python3` 3.8+, stdlib only). Outputs default to `./outputs/`.

## Credentials (check first)

Run `python3 scripts/pt_login.py status`.

- `ok: true` → go ahead.
- `ok: false` → tell the user they need a PowerTokens account and offer the two ways in:
  1. **Browser sign-in (default):** `python3 scripts/pt_login.py login` opens PowerTokens in the browser and saves a token to `~/.config/powertokens/`. If it returns `LOGIN_UNAVAILABLE`, browser sign-in is not live yet; use option 2.
  2. **API key:** the user creates a key at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and sets `POWERTOKENS_API_KEY` in their shell.
  New users sign up at https://powertokens.ai/?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills.

Never ask the user to paste a key into the chat, never write a key into files, never print it.

## Errors

Scripts print JSON. On failure read `error_type`:
`NO_CREDENTIAL`/`AUTH` → credentials step above · `INSUFFICIENT_CREDITS` → tell the user to top up (link in `next_step`), do not retry · `BAD_REQUEST` → fix the arguments · `RATE_LIMIT`/`NETWORK` → wait and retry once.

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
