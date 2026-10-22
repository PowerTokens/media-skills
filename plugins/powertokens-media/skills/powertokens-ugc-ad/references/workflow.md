# UGC formats and prompts

| Format | Shots | Notes |
|---|---|---|
| Testimonial | hook face-cam → use → result → CTA | lines in quotes, handheld selfie framing |
| Unboxing | hands POV open box → reveal → first use → reaction | mostly no faces; VO route works well |
| Problem/solution | frustration → product → relief → CTA | exaggerate the problem visually, not with claims |
| POV demo | first-person hands using product, 3–4 steps | Seedance Mini i2v from keyframes (Wan if you need 1080p or outside 4–15 s) |
| 3 reasons | hook → reason 1/2/3 → CTA | captions numbered |

Prompt style words: "handheld iPhone selfie footage", "front camera", "natural bathroom/kitchen light",
"slightly imperfect framing", "looks at the lens", "casual tone". Avoid "cinematic", "studio".

Speech in Seedance 2.5: `Ava looks at the camera and says, "Two drops, morning and night."`
One speaker, one short line per shot; longer lines drift out of sync.

VO route: write VO lines first, then size shots to the lines (≈ 2.5 words/s). One MiniMax call per line. Lines are original claims, not lyrics, verbatim slogans, celebrity endorsements, or long quotes. A `CONTENT_POLICY` block stays on that line; rewrite once, ask the user, and do not drop the rest of the VO. See `docs/speech-content-policy.md`.
