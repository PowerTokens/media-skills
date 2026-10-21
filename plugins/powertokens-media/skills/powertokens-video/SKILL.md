---
name: powertokens-video
description: Generate AI videos (text-to-video and image-to-video) with Seedance, Wan and Kling through the PowerTokens API, and save the MP4 locally. Use when the user asks to make, generate or animate a video, clip, shot, b-roll, product video, or to turn an image into a video, or names Seedance, Wan or Kling.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.1"
---

# PowerTokens video

Scripts live in `scripts/` next to this file. Run them with `python3` (3.8+, no pip installs). Paths below are relative to this skill folder; outputs default to `./outputs/` in the user's current directory.

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

1. Pick settings. Defaults: `wan3.0-video`, 5 s, 720p, 16:9. Vertical for TikTok/Reels/Shorts → `--ratio 9:16`.
   - Fast cheap draft → `wan3.0-video` at 480p.
   - Most cinematic motion / storytelling → `dreamina-seedance-2-5-260628` (aliases: `seedance-2.5`; fast draft: `seedance-fast`).
   - 1080p/4K product shots → `kling-v3` (no seed).
   - `python3 scripts/video.py models` prints durations, resolutions and list prices.
2. Preview cost without spending: add `--dry-run`. Tell the user the `est_cost_usd` before long or high-res jobs (> $1).
3. Run (takes 1–10 minutes; the script polls and downloads):

```bash
python3 scripts/video.py generate -p "PROMPT" -m wan3.0-video -d 5 -r 720p --ratio 16:9 -o outputs/clip.mp4
# image-to-video: first frame from a local file or https URL
# Seedance: omit --ratio with -i (script strips it; API 400 if ratio is sent with first_frame).
# Keyframe / first frame must already be the target aspect (e.g. 9:16).
python3 scripts/video.py generate -p "the camera slowly orbits the bottle" -i product.png -m seedance-fast
# Wan/Kling i2v may still take --ratio; prefer matching the first-frame aspect.
python3 scripts/video.py generate -p "slow orbit" -i product.png -m wan3.0-video --ratio 9:16
```

4. Report the `output` path and `task_id`. If it times out or is interrupted, do **not** submit again (that charges twice); resume:
   `python3 scripts/video.py resume TASK_ID -m MODEL -o outputs/clip.mp4`

## Prompt tips

Write one shot: subject + action + setting + camera move + light + style, e.g. "close-up of iced coffee being poured, slow push-in, morning window light, commercial look". For image-to-video describe the motion, not the image. Models generate native audio by default; add `--no-audio` for silent b-roll. For real product SKUs use `powertokens-product-qc` (bible + PRODUCT LOCK) via the pipeline, not ad-hoc prompts alone.

## Models available to the user

`python3 scripts/pt_models.py --filter wan` (or `seedance`, `kling`) lists the ids the user's account can call.

Prefer a GUI? PowerTokens Video Studio: https://github.com/PowerTokens/video-studio

## Related skills

- `powertokens-model-routing` — which model to use and what it costs
- `powertokens-prompting` — prompt structure, camera language, failure fixes
- `powertokens-pipeline` — more than one clip, storyboards, final assembly
- `powertokens-product-qc` — product identity lock before expensive i2v
