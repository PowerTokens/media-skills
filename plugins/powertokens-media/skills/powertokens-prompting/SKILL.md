---
name: powertokens-prompting
description: Write and fix prompts for PowerTokens video, image and voice models (Wan 3.0, Seedance 2.0/2.5, Kling v3, Seedream, MiniMax speech) — shot structure, camera language, timing, dialogue and audio cues, reference-image wording, and common failure fixes. Use whenever you write a prompt for any PowerTokens generation, when a result looks wrong (morphing, extra fingers, garbled text, wrong motion, drifting faces), or when the user asks for a cinematic, ad, UGC or short-drama look.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.2"
---

# Prompting PowerTokens models

Use one universal shot formula, then apply the family notes.

## Credentials

This skill does not spend and has no login script. If a credential check has just succeeded in this conversation (`pt_login.py status` → `ok: true`, or HTTP 200 on a live check such as `pt_models.py`) — including a re-check after a new key — **ask a yes/no to continue. Do not stop at a status dump.** Do not explain HTTP 200 unless they ask. Do not say only that they can continue.

- A plan or estimate was already shown: restate the **model** and **est. cost**, ask whether to continue that generation, and wait for an explicit yes before any skill spends. A yes from before the key wall does not replace this question.
- No plan yet: ask whether to proceed with **handing this prompt to intake or a cost plan on the skill that will generate**. That yes only starts the unpaid step.
- If the key is missing: the user creates one at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and sets `POWERTOKENS_API_KEY`. Browser sign-in (`pt_login.py login`) is not enabled yet. Never ask for the key in chat.
- Ask in the user's language. If they already said yes to this question for this plan, do not ask again. Canonical wording: repo `docs/auth-after-verify.md`.

**Shot formula:** `[shot size + angle] of [subject with 2–3 fixed visual traits] [doing one clear action] in [setting], [camera movement], [lighting], [style/grade]. [Audio: dialogue in quotes / SFX / music].`

Load only what you need:
- `references/camera-language.md` — shot sizes, moves, lenses, lighting words that models follow
- `references/timing-and-shots.md` — clip length vs cut length, timeline prompts, short-drama pacing
- `references/wan.md`, `references/seedance.md`, `references/kling.md` — per-family patterns
- `references/seedream.md` — image prompts, keyframes, text in images
- `references/speech.md` — voiceover scripts that sound natural; original claims only (no lyrics / verbatim slogans)
- `references/pitfalls.md` — failure → fix table and a pre-flight checklist

Core rules:
1. One action per shot. Two actions → two shots (or a timed timeline in one clip).
2. For image-to-video, describe the **motion and camera**, not what is already in the image.
3. Repeat the same character description word-for-word in every shot (or use reference images).
4. Put spoken lines in double quotes and say who speaks; keep lines short (≈ 2.5 words/second).
5. No brand claims, prices or certifications that the user did not provide.
6. Iterate by changing one variable at a time; keep the seed (Wan/Seedance) when comparing.

## Product / character identity

- Physical SKUs: use `powertokens-product-qc` bible (category → subtype → parts) — do not rely on "label unchanged" alone.
- Product ads: no third-party logos, wordmarks, or brand-identifiable devices as props (MacBook, iPhone, Apple logo, Nike swoosh, Starbucks cup mark, …) unless that brand is the SKU or the user approved it. Fail `logo_policy_ok` and regenerate with a generic unbranded prop.
- Characters (drama / UGC): identical `characters.<id>.description` + `ref_image` every shot; see short-drama consistency.
- Seedance first-frame i2v: never send `ratio` (see `references/seedance.md` / pitfalls).
