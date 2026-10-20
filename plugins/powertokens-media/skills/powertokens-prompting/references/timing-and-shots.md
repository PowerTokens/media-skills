# Timing: clip length vs cut length

Two different things:
- **Clip (generation) length** — what you request. Model limits: Wan 3.0 2–30 s, Seedance Fast
  4–15 s, Seedance 2.5 4–30 s, Kling v3 3–15 s (see model-routing).
- **Cut (shot) length** — how long each shot stays on screen in the edit.

Short-form and short-drama pacing (craft guidance, not an API limit): most cuts 1–3 s, hook in the
first 1–2 s, hold a reaction or product beat 2–3 s, rarely > 4 s on vertical feeds.

Two ways to get 1–3 s cuts:
1. **Generate short clips, cut in the edit.** Request the model minimum (Wan 2 s, Kling 3 s,
   Seedance 4 s) and trim with ffmpeg. Simple and consistent; you pay for unused seconds.
2. **Timeline prompt inside one clip.** Seedance follows time-coded beats. PT's Seedance 2.5 docs
   example uses this form: "First frame is image 1, …; 2-4s: quick cut, …; 4-6s: product close-up, …;
   6-8s: …". Keep 3–5 beats per clip, each 1–3 s, same subject description throughout.
   Kling v3 has a native `multi_shot` mode (≤ 6 shots, durations sum to total) — not wired here.

Budget rule of thumb: 30 s ad ≈ 10–15 cuts. Generate 4–6 clips of 5–8 s and cut 2–3 shots from each.
Voiceover pace: ≈ 150 English words / minute, ≈ 4–5 Chinese characters / second.
