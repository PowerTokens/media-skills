# Character consistency

1. **Same words every time.** The `characters.<id>.description` is prepended to each shot. Do not
   paraphrase in shot prompts ("her coat" is fine; "a red coat" when the bible says beige is not).
2. **Reference image per character.** Seedance and Wan 3.0 accept `reference_image`; refer to it in the
   prompt as "the woman in image 1". Order: character refs first, then `ref_images` of the shot.
3. **Wan limitation:** reference images cannot be combined with a first frame. For Wan shots that need
   an exact composition, generate a Seedream keyframe *with* the character ref, then i2v from it.
4. **Two characters in one shot:** list both ids; describe positions ("Ning on the left, Kai on the right").
5. **Wardrobe/time changes:** create a new character id (`ning_night`) with its own sheet.
6. **Check:** after run, view first frames of all clips side by side before assembling.
