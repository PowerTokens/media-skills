# MiniMax speech content-policy blocks

MiniMax speech (PowerTokens `/v1/audio/speech`, default `speech-2.8-turbo`) can reject a line for audio copyright or a content/safety policy. The API wording is mapped to a stable `error_type`: **`CONTENT_POLICY`**. Other types (`BAD_REQUEST`, `INSUFFICIENT_CREDITS`, `AUTH`, `RATE_LIMIT`, …) stay as they are.

The JSON error includes `rejected_text` (the line that was sent, or the snippet the API echoed) and, after the automatic retry, `rewrite_attempted`. The message names the segment id and a short quote of the line.

## One call per line

Multi-line ads do not send the whole script in one TTS call.

- Pipeline: each `voiceover.lines[]` entry is one call. Set `id` (`vo01`, …). Output: `<workdir>/voiceover/<id>.mp3`.
- `speech.py`: `--split-lines` (one call per non-empty line) or one invocation per line with `--segment`. Files are named with the segment id. A failure string looks like `Speech vo02 ("…")`.

A blocked segment does not cancel the other segments or the finished clips.

## Recovery

1. The script rewrites **that line once**: paraphrase; drop song lyrics, celebrity names, trademark slogans, and long quotes; keep approved claim-sheet facts (numbers, product, CTA).
2. It retries **that segment once**.
3. If the retry is spoken, state records `spoken_text` and `rewritten_from`. Tell the user what was actually said.
4. If it is still blocked, state is `content_policy` and `run` / `--split-lines` exits **7** with `voiceover_blocked`. The same text is not sent again until the line changes.
5. Ask the user. Show the rejected line, the rewrite already tried, and one or two new options. Do not invent claims.
6. Continue every other segment. Do not throw away clips.

`INSUFFICIENT_CREDITS` and auth errors still stop the job. Clips and VO lines already saved stay on disk.

## Assemble

`pipeline.py assemble` does **not** require every VO file once the user accepts a partial cut.

- Blocked lines and no `--allow-partial-vo`: assemble exits 7 and asks. Clips are untouched.
- After a yes: `assemble --allow-partial-vo` mixes the VO that exists and inserts silence for each missing line so later lines do not slide early. Ducked clip audio (or the user's own BGM in `finish`) covers the gap.
- Bilingual, EN blocked: offer a ZH-only cut only after they say yes. Do not skip a ZH cut they already approved.

`finish.py` already skips a missing line (the next line stays on its shot). It reports `voiceover_missing` when a line was absent.

## Prevention

Before spending on EN voiceover, say this: lines are original product claims from the approved claim sheet, not song lyrics, brand slogans copied verbatim, celebrity endorsements, or long copyrighted quotes.

Same rule in `powertokens-speech`, `powertokens-product-ad` (`references/copy.md`, `references/workflow.md`), `powertokens-bilingual-voiceover` (`references/adaptation.md`), and `powertokens-prompting` (`references/speech.md`).
