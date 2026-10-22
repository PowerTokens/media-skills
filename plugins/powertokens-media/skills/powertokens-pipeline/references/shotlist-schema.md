# Shot list JSON

```json
{
  "project": "mug-ad",                    // folder name under ./outputs/ (or set "workdir")
  "style": "Bright commercial look, soft window light.",   // prepended to every shot prompt
  "defaults": {"model": "seedance-mini", "resolution": "720p", "ratio": "9:16", "duration": 5, "audio": false},
  "characters": {
    "mia": {"description": "Mia, 28, short black bob, yellow raincoat.", "ref_image": "refs/mia.png"}
  },
  "shots": [
    {
      "id": "s01",
      "prompt": "Close-up, Mia lifts the mug and smiles, slow push-in.",   // required
      "characters": ["mia"],              // description prepended; ref_image added as reference
      "duration": 4, "model": "seedance-fast",      // any default can be overridden per shot
      "image": "product.png",             // optional first frame (file or https URL)
      "ref_images": ["product.png"],      // optional extra references (Wan/Seedance only)
      "keyframe": {"prompt": "…", "ref_images": ["product.png"], "model": "seedream-4-5-251128"},
      "caption": "Keeps coffee hot for 12 hours"   // burned in at assemble, timed to this shot
    }
  ],
  "voiceover": {"model": "speech-2.8-turbo", "voice": "English_Trustworthy_Man",
                "lines": [{"id": "vo01", "text": "…"}, {"id": "vo02", "text": "…", "voice": "…"}]},
  "assembly": {"clip_audio_volume": 0.25}
}
```
(Comments are for reading only; real files must be plain JSON.)

Rules enforced by `validate`:
- model limits (seconds, resolution, ratio) per model-routing;
- Wan 3.0: `image`/`keyframe` and reference images cannot be combined — when a Wan shot has a
  first frame, character reference images are skipped at run time (description text still applies);
- Kling: no reference images in this pack;
- referenced local files must exist.

Model aliases: `seedance-mini` (pack default), `wan`, `wan-prime`, `seedance-fast`, `seedance-2.5`, `kling`.
`seedance-mini` is 4–15 s and max 720p (~$0.031/s at 480p and 720p). 1080p/4K heroes stay on `kling`.
State: `<workdir>/state.json` (task ids, outputs). Plan: `<workdir>/plan.json`.

## Product-ad fields

```json
{
  "kind": "product-ad",
  "product_bible": "product-bible.json"
}
```

- `kind: product-ad` (or `--require-product-bible`) makes `validate` / `plan` / `run` refuse without a valid bible.
- When a bible is present, `pipeline.py` **auto-appends** `product_qc.constraints_block` to every shot prompt and Seedream keyframe prompt, and merges existing bible `refs` into **Seedream keyframe** refs only (not Wan/Kling i2v — first-frame + constraints carry the lock).
- **Vision QC + batch gate (wired, default on for product-ad):** `run` generates every Seedream keyframe and requires machine QC `pass` before it submits **any** i2v/video. One regenerate of the failed still only; a second fail stops in the keyframe phase (`qc_gate.report` lists the shot and why: structure, third-party logo, hybrid part, …). Failed stills are not sent to video. Sibling shots that already passed wait. After every required keyframe passes, i2v goes out as one `--parallel` batch. Vision API unavailable → **fail-closed** unless `--skip-vision-qc` (also disables the batch gate).
- Per-shot `"hero": true` — after the batch QC gate is open, writes `hero_pending.json` and **pauses that shot's i2v** until `pipeline.py approve-hero <shotlist> <shot_id>` (or `--auto-approve-hero` for CI). The full still strip is not a required human pause.

Flags on `run`: `--vision-qc` · `--skip-vision-qc` · `--auto-approve-hero` · `--parallel`.

## Character bible (short-drama / UGC)

```json
{
  "kind": "short-drama",
  "character_bible": "character-bible.json",
  "characters": {
    "ning": {"description": "…", "traits": ["…"], "forbid": ["…"], "ref_image": "refs/ning.png"}
  }
}
```

- `kind: short-drama` requires `character_bible` **or** inline `characters` with non-empty `description` (schema via `character_qc.py`). `validate` / `plan` / `run` refuse without it. `"characters_on_camera": false` does not waive a short drama.
- `kind: ugc-ad` fails closed the same way when anyone is on camera. Hands-only / no face: set `"characters_on_camera": false` and do not set shot `characters`, `on_camera`, or `face_cam`.
- Any other shot list that sets those on-camera fields also refuses without a valid bible.
- When a shot names a character that has `forbid`, `pipeline.py` appends a `CHARACTER LOCK` line to that shot prompt (the description is prepended as well).
- Example: `examples/character-bible.ning.json`.

## Claims lint

Captions, voiceover lines, and `finish.end_card` / hook text are scanned for award / certification / fake-review patterns. Refuse unless `"claims_approved": true` on the shot list.

## Voiceover lines

One array entry is one MiniMax speech call (`speech-2.8-turbo` unless `model` is set). Give every line an `id` so a failure names that segment. Do not put the whole script in a single `text`.

Lines must be original claims, not song lyrics, verbatim slogans, celebrity endorsements, or long copyrighted quotes. A block is stored as `state.voiceover.<id>.status = "content_policy"` with `rejected_text` and `rewrite_attempted`. `run` rewrites and retries that line once, then continues. The same text is not sent again until you change it. `assemble --allow-partial-vo` fills a missing line with silence after the user accepts a partial cut.

## Assemble captions

`assemble` burns `shots[].caption` into the MP4 by default (TikTok/Reels lower-middle safe zone) and also writes `captions.srt`. For a product ad, UGC ad, or short drama the deliverable is that MP4 with captions burned in. The SRT is a sidecar, not a substitute. Kinetic default is A (`tiktok`); override with `assembly.caption_style` or finish/`captions.py --style` (`tiktok`|`pill`|`caps-punch`|`zh`) — not locked.

`--no-captions` skips burn-in and still writes the SRT. It is an explicit opt-out for when the user asked for softsubs only or no on-screen captions. The result sets `captions_burned` to false.

If no shot has caption text, burn-in has nothing to draw. Assemble still writes the MP4, sets `captions_burned` to false, and emits a `warning` plus `next_step`. Copy caption text (or the voiceover line for that shot) onto each shot and re-assemble. Do not hand over that clean plate as finished.
