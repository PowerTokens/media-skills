---
name: powertokens-speech
description: Turn text into natural speech (text-to-speech, voiceover, narration) with MiniMax speech models through the PowerTokens API, saving an MP3 or WAV locally. Use when the user asks for a voiceover, narration, TTS, read-aloud audio, or a spoken version of a script.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.0"
---

# PowerTokens speech

Scripts are in `scripts/` next to this file (`python3` 3.8+, stdlib only). Outputs default to `./outputs/`.

## Credentials (check first)

Run `python3 scripts/pt_login.py status`.

- `ok: true` → go ahead.
- `ok: false` → the user needs a PowerTokens API key. They create one at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and set `POWERTOKENS_API_KEY` in their shell. New users sign up at https://powertokens.ai/?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills.
  Browser sign-in (`pt_login.py login`) is not enabled yet; it will come in a later release when PowerTokens publishes OAuth.

Never ask the user to paste a key into the chat, never write a key into files, never print it.

## Errors

Scripts print JSON. On failure read `error_type`:
`NO_CREDENTIAL`/`AUTH` → credentials step above · `INSUFFICIENT_CREDITS` → tell the user to top up (link in `next_step`), do not retry · `BAD_REQUEST` → fix the arguments · `RATE_LIMIT`/`NETWORK` → wait and retry once.

## Generate

```bash
python3 scripts/speech.py -t "TEXT" --voice English_Trustworthy_Man -o outputs/voiceover.mp3
python3 scripts/speech.py -f script.txt --voice English_Graceful_Lady --speed 1.1 --format wav
python3 scripts/speech.py --list-voices
```

Default model `speech-2.8-turbo` (use `speech-2.8-hd` for higher quality). Max 10,000 characters per call; split longer scripts by paragraph and number the files. Billing is per character. Report the saved path.

Timing: ~150 English words ≈ 1 minute. For a 15 s ad aim for 30–40 words.

## Related skills

- `powertokens-model-routing` — which model to use and what it costs
- `powertokens-prompting` — prompt structure, camera language, failure fixes
- `powertokens-pipeline` — more than one clip, storyboards, final assembly
