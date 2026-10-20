# Routing examples

1. "Quick vertical teaser for my app, cheap, I'll iterate a lot"
   → `wan3.0-video`, 480p, 9:16, 5 s ≈ $0.25 per draft. Final: same model at 720p ≈ $0.50.
2. "Cinematic 20-second story with two characters talking"
   → `dreamina-seedance-2-5-260628`, 720p, 20 s ≈ $4.64; dialogue in quotes; character sheets as
   reference images. Or split into shots with `powertokens-short-drama`.
3. "4K hero shot of my watch rotating, I have a packshot"
   → `kling-v3`, `-r 4k`, 5 s ≈ $2.10, packshot as first frame. No seed, so generate 1–2 takes.
4. "15 product ads, one per SKU, same template"
   → draft each on `wan3.0-video` 480p via `pipeline.py` (15 × 8 s × $0.05 = $6.00), pick
   winners, re-run winners at 720p/1080p.
5. "Keep my mascot identical in 6 shots"
   → Seedream keyframe per shot using the mascot sheet as reference, then image-to-video; or Wan 3.0
   reference mode with the sheet as image 1.
