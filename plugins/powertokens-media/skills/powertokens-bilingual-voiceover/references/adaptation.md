# Adaptation notes

Voice pairs (ids from PT docs voice list; quality not benchmarked here):
| Tone | English | Mandarin |
|---|---|---|
| Trustworthy narrator | English_Trustworthy_Man | Chinese (Mandarin)_Reliable_Executive |
| Calm premium | English_Graceful_Lady | Chinese (Mandarin)_Wise_Women |
| News/announcer | English_Diligent_Man | Chinese (Mandarin)_News_Anchor |
| Warm, friendly | English_Gentle-voiced_man | Chinese (Mandarin)_Warm_Girl |
Cantonese voices exist (e.g. Cantonese_GentleLady); check the docs list.

Timing: if the ZH line is longer than the shot, shorten the text (do not speed > 1.15).
Numbers/brands: write how they should be spoken ("十二个小时"; brand names in Latin letters may be
read letter by letter — test).
Captions: ZH ≤ 14 characters per line on 9:16; EN ≤ 32 characters per line.
Cultural adaptation: swap idioms, units, and CTAs ("Link in bio" → "点击下方链接").

## Original lines (copyright / content policy)

EN and ZH voiceover lines must be original claims, not song lyrics, a brand slogan copied verbatim, a celebrity endorsement, or a long copyrighted quote. MiniMax returns `error_type: CONTENT_POLICY` for those. Generate **one speech call per line** so the error names that segment id and text.

On `CONTENT_POLICY`: do not cancel the other lines or the other language. The pipeline rewrites the blocked line once (paraphrase; strip the lyric, name, slogan, or quote; keep the claim-sheet fact) and retries once. If it is still blocked, ask the user with `rejected_text` and `rewrite_attempted` plus one or two new options. Then either fix that line and re-run, assemble the language that succeeded with `--allow-partial-vo` (silence / their BGM for the gap), or deliver ZH-only when EN is blocked — only after they choose. See `docs/speech-content-policy.md`.
