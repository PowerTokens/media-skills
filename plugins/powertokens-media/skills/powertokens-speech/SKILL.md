---
name: powertokens-speech
description: Turn text into natural speech (text-to-speech, voiceover, narration) with MiniMax speech models through the PowerTokens API, saving an MP3 or WAV locally. Use when the user asks for a voiceover, narration, TTS, read-aloud audio, or a spoken version of a script.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.1"
---

# PowerTokens speech

Scripts are in `scripts/` next to this file (`python3` 3.8+, stdlib only). Outputs default to `./outputs/`.

## Credentials (check first)

Run `python3 scripts/pt_login.py status`.

- `ok: false` → the user needs a PowerTokens API key. They create one at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and set `POWERTOKENS_API_KEY` in their shell. New users sign up at https://powertokens.ai/?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills.
  Browser sign-in (`pt_login.py login`) is not enabled yet; it will come in a later release when PowerTokens publishes OAuth.
- `ok: true`, or a live check such as `python3 scripts/pt_models.py` returns HTTP 200 — including a re-check after a new key: **ask a yes/no to continue. Do not stop at a status dump.** Do not explain HTTP 200 unless they ask. Do not say only that they can continue.
  - A plan or estimate was already shown: restate the **model** and **est. cost**, ask whether to continue that generation, and wait for an explicit yes before `run`, `generate`, or any other spend. A yes from before the key wall does not replace this question.
  - No plan yet: ask whether to proceed with **confirming the script and voice**. That yes only starts the unpaid step. Do not spend until they later approve the estimate.
  - Ask in the user's language. If they already said yes to this question for this plan, do not ask again. Canonical wording: repo `docs/auth-after-verify.md`.

Never ask the user to paste a key into the chat, never write a key into files, never print it.

## Errors

Scripts print JSON. On failure read `error_type`:
`NO_CREDENTIAL`/`AUTH` → credentials step above · `INSUFFICIENT_CREDITS` → tell the user to top up (link in `next_step`), do not retry · `BAD_REQUEST` → fix the arguments · `RATE_LIMIT`/`NETWORK` → wait and retry once.

`CONTENT_POLICY` → MiniMax blocked that segment (audio copyright, content policy, safety, or similar). The JSON includes `rejected_text` when the line is known, plus `segment_id` and `rewrite_attempted` when a rewrite was tried. **Do not abort the rest of the script, and do not send the same text again.**

The script already rewrites a blocked segment once (paraphrase; drop lyrics, celebrity names, trademark slogans, and long quotes; keep approved claim-sheet facts) and retries that segment once. If it is still `CONTENT_POLICY`:

1. Keep every other segment that succeeded. With `--split-lines`, exit code 7 and `voiceover_blocked` name the segment id and the rejected line; `segments` lists the files that were saved.
2. Ask the user. Show the rejected line, the rewrite already tried, and one or two new options that stay original product claims. Wait for a choice.
3. Retry only the chosen line (`--segment <id>`). Leave finished files in place.
4. Assemble only after they accept it. Partial cut: use the VO that exists and silence or their BGM for the missing line. Bilingual, EN blocked: offer a ZH-only cut. Do not pick either without a yes.

Repo note: `docs/speech-content-policy.md`.

## Generate

```bash
python3 scripts/speech.py -t "TEXT" --voice English_Trustworthy_Man -o outputs/voiceover.mp3
python3 scripts/speech.py --split-lines --segment en -f script.txt --voice English_Trustworthy_Man -o outputs/vo.mp3
python3 scripts/speech.py -t "ONE LINE" --segment vo02 -o outputs/vo02.mp3
python3 scripts/speech.py -f script.txt --voice English_Graceful_Lady --speed 1.1 --format wav
python3 scripts/speech.py --list-voices
```

Default model `speech-2.8-turbo` (use `speech-2.8-hd` for higher quality). Max 10,000 characters per call. Billing is per character. Report the saved path.

**Multi-line ads: one TTS call per voiceover line, not one call for the whole script.** Pass `--split-lines` (output `vo-<segment>.mp3`, errors name the segment id and text) or call once per line with `--segment`. A single blocked line must not drop the other lines. The pipeline shot list (`voiceover.lines[]`) does the same, one call per line.

**Before spending on EN voiceover:** lines must be original product claims from the approved claim sheet. Do not speak song lyrics, brand slogans copied verbatim, celebrity endorsements, or long copyrighted quotes. Say that when you show the EN script, before the first speech call.

Timing: ~150 English words ≈ 1 minute. For a 15 s ad aim for 30–40 words.

## Related skills

- `powertokens-model-routing` — which model to use and what it costs
- `powertokens-prompting` — prompt structure, camera language, failure fixes
- `powertokens-pipeline` — more than one clip, storyboards, final assembly
