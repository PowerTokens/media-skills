---
name: powertokens-ad-video
description: Make a short vertical product ad (9:16, 5-15 s) from a product image and a few lines of copy, using PowerTokens image, video and voiceover models, for TikTok, Reels, Shorts or paid social. Use when the user asks for a product ad, promo clip, UGC-style ad or social ad for a product.
license: MIT
metadata:
  author: PowerTokens
  version: "0.1.0"
---

# PowerTokens ad video (workflow)

Uses `scripts/image.py`, `scripts/video.py` and `scripts/speech.py` in this folder (`python3`, stdlib only). Work in `./outputs/ad-<product>/`.

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

## Workflow

1. **Brief.** Get: product image (file or URL), product name, 1–3 selling points, audience, call to action. Ask only for what is missing.
2. **Plan, then confirm.** Propose a hook line, a 1-shot or 2-shot plan, voiceover script (30–40 words for 15 s), model and total estimated cost (`video.py generate ... --dry-run`). Wait for a yes before spending.
3. **Key frame (optional).** If the product photo is plain, make a styled 9:16 first frame:
   `python3 scripts/image.py -p "<product> on <scene>, ad photography" --image product.png --size 1440x2560 -o outputs/ad-x/frame.png`
4. **Clip.** Animate the frame (Seedance 2.0 Fast for drafts, Seedance 2.5 or Kling v3 for finals):
   `python3 scripts/video.py generate -m seedance-fast -i outputs/ad-x/frame.png -p "<motion + camera>" -d 8 -r 720p --ratio 9:16 --no-audio -o outputs/ad-x/clip.mp4`
5. **Voiceover.** `python3 scripts/speech.py -f outputs/ad-x/vo.txt --voice English_Trustworthy_Man -o outputs/ad-x/vo.mp3`
6. **Assemble.** If `ffmpeg` is installed, mux voice over the clip:
   `ffmpeg -i clip.mp4 -i vo.mp3 -map 0:v -map 1:a -c:v copy -shortest ad.mp4`
   Otherwise hand over the clip and audio separately. Add captions/logo only if asked.
7. Report all files and the total spent estimate.

Keep claims factual; do not invent prices, reviews or certifications for the user's product.
