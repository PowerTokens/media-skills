# Routing examples

1. "Quick vertical teaser for my app, cheap, I'll iterate a lot"
   → `seedance-mini` (`dreamina-seedance-2-0-mini-260615`), 720p, 9:16, 5 s ≈ $0.16.
   480p is the same ~$0.031/s. Mini is 4–15 s and max 720p. For 1080p or longer than 15 s, switch model.
2. "Cinematic 20-second story with two characters talking"
   → `dreamina-seedance-2-5-260628`, 720p, 20 s ≈ $4.64; dialogue in quotes; character sheets as
   reference images. Or split into shots with `powertokens-short-drama`.
3. "4K hero shot of my watch rotating, I have a packshot"
   → `kling-v3`, `-r 4k`, 5 s ≈ $2.10, packshot as first frame. No seed, so generate 1–2 takes.
4. "15 product ads, one per SKU, same template"
   → draft each on `seedance-mini` 720p via `pipeline.py` (15 × 8 s × $0.031 = $3.72), pick
   winners. Re-run 1080p heroes on `kling-v3` (Mini has no 1080p). Wan 480p is $0.05/s, not cheaper.
5. "Keep my mascot identical in 6 shots"
   → Seedream keyframe per shot using the mascot sheet as reference, then image-to-video; or Wan 3.0
   reference mode with the sheet as image 1.
