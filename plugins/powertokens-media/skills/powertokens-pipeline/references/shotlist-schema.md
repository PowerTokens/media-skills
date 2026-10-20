# Shot list JSON

```json
{
  "project": "mug-ad",                    // folder name under ./outputs/ (or set "workdir")
  "style": "Bright commercial look, soft window light.",   // prepended to every shot prompt
  "defaults": {"model": "wan3.0-video", "resolution": "720p", "ratio": "9:16", "duration": 5, "audio": false},
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

Model aliases: `wan`, `wan-prime`, `seedance-fast`, `seedance-2.5`, `kling`.
State: `<workdir>/state.json` (task ids, outputs). Plan: `<workdir>/plan.json`.
