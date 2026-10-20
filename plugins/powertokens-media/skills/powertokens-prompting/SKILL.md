---
name: powertokens-prompting
description: Write and fix prompts for PowerTokens video, image and voice models (Wan 3.0, Seedance 2.0/2.5, Kling v3, Seedream, MiniMax speech) — shot structure, camera language, timing, dialogue and audio cues, reference-image wording, and common failure fixes. Use whenever you write a prompt for any PowerTokens generation, when a result looks wrong (morphing, extra fingers, garbled text, wrong motion, drifting faces), or when the user asks for a cinematic, ad, UGC or short-drama look.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.0"
---

# Prompting PowerTokens models

Use one universal shot formula, then apply the family notes.

**Shot formula:** `[shot size + angle] of [subject with 2–3 fixed visual traits] [doing one clear action] in [setting], [camera movement], [lighting], [style/grade]. [Audio: dialogue in quotes / SFX / music].`

Load only what you need:
- `references/camera-language.md` — shot sizes, moves, lenses, lighting words that models follow
- `references/timing-and-shots.md` — clip length vs cut length, timeline prompts, short-drama pacing
- `references/wan.md`, `references/seedance.md`, `references/kling.md` — per-family patterns
- `references/seedream.md` — image prompts, keyframes, text in images
- `references/speech.md` — voiceover scripts that sound natural
- `references/pitfalls.md` — failure → fix table and a pre-flight checklist

Core rules:
1. One action per shot. Two actions → two shots (or a timed timeline in one clip).
2. For image-to-video, describe the **motion and camera**, not what is already in the image.
3. Repeat the same character description word-for-word in every shot (or use reference images).
4. Put spoken lines in double quotes and say who speaks; keep lines short (≈ 2.5 words/second).
5. No brand claims, prices or certifications that the user did not provide.
6. Iterate by changing one variable at a time; keep the seed (Wan/Seedance) when comparing.
