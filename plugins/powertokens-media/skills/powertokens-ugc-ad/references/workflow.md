# UGC routes and prompt words

Beat timings live in `beats.md`. This file is the route and the prompt language.

## Routes

- **VO over b-roll (default):** `seedance-mini`, `audio: false` on the clip, MiniMax `speech-2.8-turbo` for the lines. Write the lines first, then size shots to them (about 2.5 English words per second). One MiniMax call per line. Lines are original claims, not lyrics, verbatim slogans, celebrity endorsements, or long quotes. A `CONTENT_POLICY` block stays on that line; rewrite once, ask the user, and do not drop the rest of the VO. See `docs/speech-content-policy.md`.
- **Native speech:** `dreamina-seedance-2-5-260628`, `audio: true`, one short line in double quotes. Review lip-sync. If it fails, move that shot to the VO route instead of regenerating the whole ad.

`speech-2.8-hd` only when the user asks. Wan only for 1080p or a duration outside 4–15 s.

## Prompt words

Use: "handheld phone selfie", "front camera", "natural bathroom or kitchen light", "slightly imperfect framing", "looks at the lens", "casual tone".

Avoid: "cinematic", "studio", "commercial packshot", "hero lighting". Those belong on a product-ad, not this skill.

Native line shape: `Ava looks at the camera and says, "Two drops, morning and night."`

## Character bible

Face or named persona: `character_bible` file or inline `characters` with `description`, plus the same `ref_image` on every face shot. `validate` refuses `kind: ugc-ad` without that, unless `"characters_on_camera": false` and no shot lists a person.

Hands-only unboxing or POV: set the flag false and do not attach character ids.

## Cost

No Seedream, Seedance, Wan, Kling, or speech call until `validate` → `plan` → explicit yes → `run --approve-estimate`. See the skill's cost gate.
