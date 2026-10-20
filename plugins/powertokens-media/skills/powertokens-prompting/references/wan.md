# Wan 3.0 / Wan 3.0 Prime

Strengths: cheap per second, up to 30 s, native audio, first frame, first+last frame, reference mode.

Patterns:
- Text-to-video: shot formula from SKILL.md, 40–120 words. Name the camera move explicitly.
- First-frame (i2v): "The bottle slowly rotates clockwise, condensation drips, camera pushes in,
  background stays still." Motion only.
- First+last frame: describe the transition between the two images ("the closed box opens and the
  phone rises out of it").
- Reference mode: refer by order — "The woman in image 1 picks up the mug in image 2 and smiles."
  Do not combine reference images with first/last frame in one request (PT docs).
- Audio: native audio is on by default in these scripts; describe ambience and SFX. Use `--no-audio`
  for b-roll that will carry a voiceover.

Pitfalls: long multi-action prompts make actions blend; adaptive ratio may not match the platform —
set the ratio explicitly.
