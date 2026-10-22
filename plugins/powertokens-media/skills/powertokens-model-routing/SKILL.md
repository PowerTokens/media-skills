---
name: powertokens-model-routing
description: Pick the right PowerTokens model (default Seedance 2.0 Mini, plus Wan 3.0, Wan 3.0 Prime, Seedance 2.0 Fast, Seedance 2.5, Kling v3, Seedream, MiniMax speech) for a video, image or voice job by quality, speed, price, duration, aspect ratio, resolution and input type (text-to-video, image-to-video, reference images). Use before any PowerTokens generation, whenever the user asks "which model", compares models, has a budget, needs 1080p/4K, long clips, vertical video, or character consistency.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.2"
---

# PowerTokens model routing

Decide the model before writing prompts. Load a reference only when you need its detail:

- `references/video-models.md` — limits, list prices, inputs, sources (Wan, Seedance, Kling)
- `references/image-and-speech-models.md` — Seedream and MiniMax speech
- `references/decision-examples.md` — worked routing decisions

## Quick routing (video)

| Need | Pick | Why |
|---|---|---|
| Cheapest drafts, iteration (pack default) | `dreamina-seedance-2-0-mini-260615` (`seedance-mini`) | lowest list price in this repo, ~$0.031/s at 480p and 720p; 4–15 s, max 720p |
| Up to 30 s, 1080p, or Wan reference mode | `wan3.0-video` | 2–30 s; 480p $0.05/s · 720p $0.10/s · 1080p $0.20/s |
| Same as Wan but sooner | `wan3.0-video-prime` | faster turnaround, higher price |
| Fast previews of a Seedance look | `dreamina-seedance-2-0-fast-260128` | 4–15 s, max 720p; promo ~$0.061/s |
| Storytelling, dialogue with synced audio, multi-reference | `dreamina-seedance-2-5-260628` | 4–30 s, up to 1080p, text/image/video/audio references |
| 1080p or 4K product hero shots | `kling-v3` | 720p std / 1080p pro / 4K modes, 3–15 s, no seed |

Rules of thumb:
1. Draft on Seedance Mini (cheapest; 4–15 s, max 720p, ~$0.031/s). Use Wan or Seedance Fast only when Mini does not fit, then finalize on the model the user approved.
2. Character or product must stay identical across shots → reference images (Wan 3.0 or Seedance), or one keyframe per shot made with Seedream then image-to-video. Kling reference elements are not wired in this skill pack.
3. Wan 3.0 cannot mix reference images with first/last frame in one request (PT docs).
4. Kling v3 has no `seed`; do not promise exact re-rolls.
5. Always run `--dry-run` / `pipeline.py plan` and show the estimate before paid work.
6. Confirm availability with `python3 scripts/pt_models.py --filter <family>` when unsure; if a model id is not listed for the user's account, do not use it.

Do not route to models not listed here, even if the account exposes more.

7. Seedance **first-frame i2v:** do not send `ratio` (API 400); output follows the first frame — keyframe at target aspect. `video.py` omits `ratio` automatically when a first/last frame is present.
8. Never promote undocumented chat/image ids or Avoid `kling-video-o1*` video ids — stay on the table above.
