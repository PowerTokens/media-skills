# Category beat recipes

Pick one category in the brief. Times are for a 15–20 s 9:16 cut. Generate draft clips at 4–5 s when the model minimum is higher than the on-screen beat, then trim in assemble. One spoken line per shot.

Default video for silent or VO shots is `seedance-mini`. Native on-camera speech uses Seedance 2.5 only for that face shot. Speech default stays `speech-2.8-turbo`.

| Category | On camera | Beats | Route |
|---|---|---|---|
| Testimonial | face | 0–2 s hook → use → result → CTA | native speech, or VO if lip-sync fails |
| Unboxing | hands; face only on the reaction if the user asked | open → reveal → first use → reaction | VO + `seedance-mini`; face reaction can be 2.5 |
| Problem/solution | face or hands | frustration → product → relief → CTA | VO + mini, or native speech on the face beats |
| POV demo | hands | 3–4 use steps, optional face CTA | VO + mini from keyframes |
| Three reasons | face or caption-led hands | hook → reason 1 → 2 → 3 → CTA | numbered captions; VO or native speech |

## Testimonial

1. Hook, face, ≤ 2 s of speech: one sourced benefit, not a vibe.
2. Use: the product in hand, same outfit and ref.
3. Result: what changed, still only approved claims.
4. CTA: where to go (link, code) if the user supplied it.

Shot list: `characters` includes the persona id on every face shot. `kind` is `ugc-ad`.

## Unboxing

1. Hands open the mailer. No face, no invented brand on the box.
2. Reveal the real pack. If the label must stay accurate, add a product bible.
3. First use, still hands.
4. Optional reaction face. If you add it, the character bible is required and `characters_on_camera: false` is no longer valid.

Hands-only cut: `"characters_on_camera": false` and no `characters` / `on_camera` on shots.

## Problem/solution

1. Frustration is visual (messy counter, tangled cord). Do not invent a medical or safety claim.
2. Product enters.
3. Relief matches an approved claim.
4. CTA.

## POV demo

1. Step 1 hands, keyframe at 9:16, i2v on `seedance-mini`.
2. Step 2, same hands, same framing family.
3. Step 3.
4. CTA card or a single face line. A face line needs the character bible.

## Three reasons

1. Hook that names the count ("three things").
2. Reason 1, 2, 3 — each caption is `1` `2` `3` plus the claim, not a new claim.
3. CTA.

Captions are the spoken line, shortened, not a different fact.
