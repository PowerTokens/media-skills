---
name: powertokens-pipeline
description: Turn a JSON shot list into a finished video with PowerTokens — Seedream keyframes, batched Wan/Seedance/Kling clips, MiniMax voiceover, then ffmpeg assembly with captions — with a cost estimate and user approval before spending, and resume after interruptions without paying twice. Use for any multi-shot job (ads, short dramas, explainers, storyboards, batches of variants), whenever the user wants more than one clip, a storyboard rendered, or a final edited video.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.0"
---

# PowerTokens shot-list pipeline

Script: `scripts/pipeline.py` (Python 3.8+, stdlib; ffmpeg needed only for `assemble`/`reformat`).
Schema: `references/shotlist-schema.md`. Examples: `examples/*.json`.

## Steps (always in this order)

1. **Credentials:** `python3 scripts/pt_login.py status` (see the powertokens-video skill for login / key setup).
2. **Write the shot list** to `<project>.json` (use an example as a template; apply powertokens-prompting).
3. **Validate (free):** `python3 scripts/pipeline.py validate shots.json` — fix every error.
4. **Plan (free):** `python3 scripts/pipeline.py plan shots.json` → per-shot and total estimate plus
   items it cannot price (keyframes, voiceover).
5. **Ask the user** with a short table: shots, model, seconds, est. USD, not-estimated items.
   Do not continue without an explicit yes. If they want it cheaper, re-route (480p drafts, fewer seconds).
6. **Run (paid):** `python3 scripts/pipeline.py run shots.json --approve-estimate <video_est_usd>`.
   The script refuses if the number does not match the current plan. Up to 4 shots in parallel (`--parallel`).
7. **If anything fails or times out:** read `failed`, fix, run the same command again. Finished shots
   are skipped; submitted shots are resumed by task id (no double charge). `INSUFFICIENT_CREDITS` → stop
   and tell the user.
8. **Review:** list clips in `<workdir>/clips/`. Offer re-takes of single shots (delete that shot's entry
   in `state.json` to regenerate it — this costs again; say so).
9. **Assemble (free):** `python3 scripts/pipeline.py assemble shots.json` → normalizes to the project
   ratio, concatenates, mixes voiceover over ducked clip audio, burns captions (`captions.srt` also saved).
   `--dry-run` prints the ffmpeg commands.
10. **Variants (free):** `python3 scripts/pipeline.py reformat final.mp4 --ratio 1:1 --mode crop|pad`.

Report: final path, duration, what was spent (estimate), anything not generated.
