---
name: powertokens-pipeline
description: Turn a JSON shot list into a finished video with PowerTokens — Seedream keyframes, batched Wan/Seedance/Kling clips, MiniMax voiceover, then ffmpeg assembly with captions — with a cost estimate and user approval before spending, and resume after interruptions without paying twice. Use for any multi-shot job (ads, short dramas, explainers, storyboards, batches of variants), whenever the user wants more than one clip, a storyboard rendered, or a final edited video.
license: MIT
metadata:
  author: PowerTokens
  version: "0.3.2"
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
   **Voiceover is one MiniMax call per `voiceover.lines[]` entry** (default `speech-2.8-turbo`). A line that
   returns `CONTENT_POLICY` is rewritten once and retried once; other lines still generate. `run` then exits 7
   with `voiceover_blocked` (`id`, `rejected_text`, `rewrite_attempted`). Ask the user with that line and
   rewrite options. Do not send the same text again (a second `run` skips it until the line changes).
   Clips already saved stay saved. Details: `docs/speech-content-policy.md`.
8. **Review:** list clips in `<workdir>/clips/`. Offer re-takes of single shots (delete that shot's entry
   in `state.json` to regenerate it — this costs again; say so).
9. **Assemble (free):** `python3 scripts/pipeline.py assemble shots.json` → normalizes to the project
   ratio, concatenates, mixes voiceover over ducked clip audio, burns captions in TikTok lower-middle safe zone (`captions.srt` is also saved as a sidecar; override style via `assembly.caption_style`).
   `--dry-run` prints the ffmpeg commands. See **Burned-in captions** before you treat the MP4 as delivered.
   If a VO line is `CONTENT_POLICY` blocked, assemble **asks** (exit 7) instead of failing the clips.
   It does not require every VO file once the user accepts a partial cut:
   `assemble --allow-partial-vo` uses the lines that exist and inserts silence for the gap (ducked clip audio remains; add their BGM in `finish` if they want music).
   Bilingual EN blocked: offer a ZH-only assemble only after they say yes. Do not pass `--allow-partial-vo` before that yes.
   A partial cut still burns captions unless they also asked for `--no-captions`.
10. **Variants (free):** `python3 scripts/pipeline.py reformat final.mp4 --ratio 1:1 --mode crop|pad`.

Report: final path, `"captions_burned": true`, duration, what was spent (estimate), anything not generated. If `captions_burned` is false or the result has a `warning`, fix it and re-assemble before handing over the path.

## Burned-in captions (delivery gate)

For a product ad, UGC ad, or short drama, the deliverable MP4 **must** have captions burned in. `assemble` does that by default. `captions.srt` is a sidecar. Shipping the SRT alone, or telling the user to open it, is not a complete delivery unless they explicitly asked for softsubs only.

Before sharing the final path:

1. Assemble without `--no-captions`.
2. Read the JSON: `"captions_burned": true`, and no `warning`.
3. Shots must have caption text (`shots[].caption`, or voiceover line text copied onto each shot) so the burn has content. If captions are missing, fix the shot list and re-assemble. An empty SRT means the MP4 is a clean plate; do not call it done.

`--no-captions` is the rare explicit opt-out (user asked for no burn-in or softsubs only). It skips burn-in, still writes `captions.srt`, and sets `captions_burned` to false with a `warning`. Pass it only in that case, and say burn-in was skipped. Same rule when re-assembling cut-downs or language cuts.

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

Burn-in style **defaults** to kinetic TikTok **A** (`tiktok` yellow word highlight); override via `assembly.caption_style` or `captions.py --style` (`tiktok`|`pill`|`caps-punch`|`zh`) — recommended default, not locked. **Wording** for `assemble` comes only from `shots[].caption` (copy voiceover line text onto each shot when that is where the words live). `finish.py` can also read `voiceover.lines[].caption` / `.text` (shot captions only if there is no VO). Authors must follow the powertokens-product-ad copy brief: prefer product URL → claim sheet → user approve; sourced claims only; reject mood-only lines; no spend before yes. Delivery still requires burned-in captions; see **Burned-in captions**.

## Finish / kinetic captions (optional)

Finish presets: `clean-premium` (default), `ugc-punchy`, `cinematic`. **Light user awareness:** at estimate approval, one sentence naming the default and that they can ask for UGC/cinematic — no forced picker.


After `assemble`, optional polish (no credits):

```bash
python3 scripts/finish.py finish shots.json --preset clean-premium
python3 scripts/captions.py preview base.mp4 --style tiktok --text "…" --start 0.3 --end 2.9
```

`finish.py` end-card `price` / headlines must come from the user brief — never invent claims.
