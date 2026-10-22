---
name: powertokens-pipeline
description: Turn a JSON shot list into a finished video with PowerTokens — Seedream keyframes, batched Wan/Seedance/Kling clips, MiniMax voiceover, then ffmpeg assembly with captions — with a cost estimate and user approval before spending, and resume after interruptions without paying twice. Use for any multi-shot job (ads, short dramas, explainers, storyboards, batches of variants), whenever the user wants more than one clip, a storyboard rendered, or a final edited video.
license: MIT
metadata:
  author: PowerTokens
  version: "0.3.0"
---

# PowerTokens shot-list pipeline

Script: `scripts/pipeline.py` (Python 3.8+, stdlib; ffmpeg needed only for `assemble`/`reformat`).
Schema: `references/shotlist-schema.md`. Examples: `examples/*.json`.

## Steps (always in this order)

1. **Credentials:** `python3 scripts/pt_login.py status`.
   - Not ok: the user creates a key at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and sets `POWERTOKENS_API_KEY`. Browser sign-in (`pt_login.py login`) is not enabled yet. Never ask for the key in chat.
   - **Valid** (`ok: true`, or HTTP 200 on a live check such as `python3 scripts/pt_models.py`), including a re-check after a new key: **ask a yes/no to continue. Do not stop at a status dump.** Do not explain HTTP 200 unless they ask. Do not say only that they can continue.
     - A plan or estimate was already shown: restate the **model** and **est. cost**, ask whether to continue that generation, and wait for an explicit yes before `run` or any other spend. A yes from before the key wall does not replace this question.
     - No plan yet: ask whether to proceed with **writing or validating the shot list, then `plan`**. That yes only starts the unpaid step. Do not spend until they later approve the estimate.
     - Ask in the user's language. If they already said yes to this question for this plan, do not ask again. Canonical wording: repo `docs/auth-after-verify.md`.
2. **Write the shot list** to `<project>.json` (use an example as a template; apply powertokens-prompting).
3. **Validate (free):** `python3 scripts/pipeline.py validate shots.json` — fix every error.
4. **Plan (free):** `python3 scripts/pipeline.py plan shots.json` → per-shot and total estimate plus
   items it cannot price (keyframes, voiceover).
5. **Ask the user** with a short table: shots, model, seconds, est. USD, not-estimated items.
   Do not continue without an explicit yes. If they want it cheaper, use Seedance Mini (the default; ~$0.031/s at 480p and 720p, 4–15 s, max 720p) or fewer seconds. 480p is not cheaper than 720p on Mini.
6. **Run (paid):** `python3 scripts/pipeline.py run shots.json --approve-estimate <video_est_usd>`.
   The script refuses if the number does not match the current plan. Up to 4 shots in parallel (`--parallel`).
7. **If anything fails or times out:** read `failed`, fix, run the same command again. Finished shots
   are skipped; submitted shots are resumed by task id (no double charge). `INSUFFICIENT_CREDITS` → stop
   and tell the user.
8. **Review:** list clips in `<workdir>/clips/`. Offer re-takes of single shots (delete that shot's entry
   in `state.json` to regenerate it — this costs again; say so).
9. **Assemble (free):** `python3 scripts/pipeline.py assemble shots.json` → normalizes to the project
   ratio, concatenates, mixes voiceover over ducked clip audio, burns captions in TikTok lower-middle safe zone (`captions.srt` also saved; override via `assembly.caption_style`).
   `--dry-run` prints the ffmpeg commands.
10. **Variants (free):** `python3 scripts/pipeline.py reformat final.mp4 --ratio 1:1 --mode crop|pad`.

Report: final path, duration, what was spent (estimate), anything not generated.

## Product ads / identity lock

If the shot list is a product ad, set `"kind": "product-ad"` and `"product_bible": "<file>.json"` (category → subtype → parts BOM). `validate` / `plan` / `run` refuse without a valid bible. When a bible is present, the pipeline **auto-appends** PRODUCT LOCK constraints to every shot and Seedream keyframe prompt, and merges existing bible refs into keyframe refs only (not Wan/Kling i2v).

**Vision QC + hero gate (in `run`):** after each Seedream keyframe, vision chat QC runs by default for product-ad (one retry on fail; still fail → no i2v). Unavailable vision API → fail-closed unless `--skip-vision-qc`. Shots with `"hero": true` pause after QC; approve with `pipeline.py approve-hero shots.json <id>` or pass `--auto-approve-hero`.

## Character bible

`kind: short-drama` needs `character_bible` or inline `characters` with descriptions (`character_qc.py`). UGC with characters: same schema. See `examples/character-bible.ning.json`.

## Claims

`validate` / `finish` refuse award/cert/fake-review wording in captions, VO, and end-cards unless `claims_approved: true`.

## Seedance i2v

With a first frame / keyframe, Seedance rejects `ratio` (HTTP 400). `video.py` omits it automatically; generate keyframes at the target aspect.

## Caption copy (content ≠ style)

Burn-in style **defaults** to kinetic TikTok **A** (`tiktok` yellow word highlight); override via `assembly.caption_style` or `captions.py --style` (`tiktok`|`pill`|`caps-punch`|`zh`) — recommended default, not locked. **Wording** comes from the shot list: `shots[].caption`, or for `finish.py` from `voiceover.lines[].caption` / `.text` (shot captions only if there is no VO). Authors must follow the powertokens-product-ad copy brief: prefer product URL → claim sheet → user approve; sourced claims only; reject mood-only lines; no spend before yes.

## Finish / kinetic captions (optional)

Finish presets: `clean-premium` (default), `ugc-punchy`, `cinematic`. **Light user awareness:** at estimate approval, one sentence naming the default and that they can ask for UGC/cinematic — no forced picker.


After `assemble`, optional polish (no credits):

```bash
python3 scripts/finish.py finish shots.json --preset clean-premium
python3 scripts/captions.py preview base.mp4 --style tiktok --text "…" --start 0.3 --end 2.9
```

`finish.py` end-card `price` / headlines must come from the user brief — never invent claims.
