# Second-world travel poster — generation method (agent checklist)

Build a **fresh** Seedream prompt for each photo from this checklist. Do not paste this file, and do not paste any viral Chinese template, into the chat or into the image as invisible text.

## Canvas and layout (always)

- Output **3:4 vertical**. Request size `1536x2048` (meets Seedream pixel floor; aspect exactly 3:4).
- Strict **upper / lower 1:1 split** of the canvas.
- **Upper half:** the original photograph, preserved faithfully — subject, pose, space, color, natural light. Only crop as needed to fit the half. Do not recolor, restyle, illustrate over, or redesign the photo.
- **Lower half:** warm off-white / cream paper (print stock feel), generous negative space. Not a second photo, not a busy illustration field.

## Observe first (required)

Before writing the prompt, name concrete structures visible in **this** upload, for example:

- water: wave crests, shoreline, foam, reflection on wet sand
- path: road, trail, rail, bridge span, staircase
- sky: cloud edge, light shaft, fog bank, star field (only if present)
- land: ridge, cliff, dune, terrace, field furrow
- built: window, arch, balcony, doorway, roof line
- organic: branch silhouette, reed, rope, shadow shape
- figure: a distinctive pose or gesture already in the photo

Pick **one** primary structure. The lower half must answer: *what if that structure became touchable or usable?*

## Invent the second world (must be photo-specific)

Translate the chosen structure into a single clear action that only makes sense for this photo, e.g. (illustrative — invent your own, do not reuse these as defaults):

- shoreline foam → a paper "pond" cutout someone dips a cup into
- mountain ridge → a foldable cardboard skyline being carefully creased
- road vanishing point → a paper strip road continuing onto the desk, a tiny figure walking onto it
- window light → a scrap of yellow paper being "borrowed" as a lantern
- reflection → a mirror shard of paper being lifted so the scene peeks through

Allowed action verbs (pick one family): pull, push, enter, fish out, measure, mend, unfold, climb, connect, collect, pour, pin, stitch, open, lean on.

**Forbidden defaults:** jagged tear-paper edge as the only idea; stock "tiny people standing on a torn photo"; reused gag from a previous run; random leaves, stars, stickers, washi tape decoration with no link to the photo.

## Collage cut shape

The boundary between photo and paper should **interpret** the photo (pond silhouette, light rectangle, road strip, cloud scallop, architectural edge) — not a generic torn edge every time.

## Optional figures (0–3)

- Minimal **black line-drawn** people or hands who **use** the structure (pulling, measuring, climbing…), not decorative posing.
- Skip entirely if the upper photo already has strong human action.
- Never crowd; never turn the lower half into a comic panel.

## Caption (one line)

- Short English, handwritten / indie-magazine voice.
- Natural, lightly funny, or soft voiceover — as if someone muttered it while looking at the print.
- Place next to the whitespace or the action (say where in the prompt).
- **Not** motivational quotes, **not** "Same.. different.", **not** destination hashtags, **not** brand slogans.

## Style locks (put near the end of the prompt)

Real photograph (upper) + warm paper (lower) + sparse black ink doodle. Clean, bright, restrained. Handmade collage / indie print magazine. No ad lighting, no product packshot look, no dense illustration, no watercolor wash over the photo, no heavy grain filter on the upper half.

## Avoid list (always include a short negative / avoid clause)

Do not: recolor or restyle the original photo; fill the paper with decoration; pack many figures; use a fixed tear template; paste motivational text; look like an ad or travel-agency brochure; add logos or watermarks; invent famous landmarks that are not in the photo.

## Prompt shape (write this, don't show the user)

```
3:4 vertical poster, canvas split exactly in half.
Upper half: [faithful description of the uploaded photo — keep subject, pose, space, color, natural light; only necessary crop]. Use the reference image as the upper photograph.
Lower half: warm off-white paper, large empty margins.
[One sentence: the photo-specific second-world beat + how the cut shape follows the photo.]
[0–3 line figures and what they are doing, or "no added figures".]
Handwritten English caption "[line]" placed [where].
Style: real photo + warm paper + minimal black ink doodle; clean bright restrained handmade collage, indie magazine print.
Avoid: ad look, dense illustration, crowded figures, generic torn edge, random stickers, recoloring the original photo.
```

Keep total length under ~500 English words. One idea, one action, one caption.
