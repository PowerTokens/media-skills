# Seedance 2.0 Fast / Seedance 2.5

Strengths: cinematic motion, timed multi-beat prompts, dialogue with synced audio (2.5), multimodal
references (image, video, audio).

Patterns:
- Timeline prompt (see timing-and-shots.md): "0-2s: … ; 2-4s: … ; 4-6s: …".
- Dialogue: `The man stops the woman and says, "Remember, never point at the moon."` — PT docs
  recommend double quotes for spoken lines. Generated audio is mono.
- References: "Use image 1 as the character, image 2 as the product." First frame: "First frame is
  image 1". Last frame: "final frame frozen on image 2".
- Use Seedance 2.0 Fast for drafts (≤ 720p), switch to 2.5 for finals or > 15 s / 1080p.

Pitfalls:
- **First-frame / first-last-frame i2v:** do **not** send `ratio`. The API returns HTTP 400
  `InvalidParameter.TaskTypeConstraint` ("output ratio follows the first-frame image").
  `video.py` / pipeline omit `ratio` automatically when a first or last frame is present.
  Generate the keyframe at the target aspect (e.g. 9:16) so the clip matches the platform.
- Text-to-video and reference-only (no first frame): `ratio` is required / allowed as usual.
- Task-type mismatch (`InvalidParameter.TaskTypeMismatch`): prompt implies edit/extend while
  inputs imply reference — make the prompt match the inputs.
