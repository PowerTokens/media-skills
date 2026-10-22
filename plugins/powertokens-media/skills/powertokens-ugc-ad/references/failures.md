# Failure modes

Fix the row, then re-run the same command when the pipeline says it will resume. Do not start a second paid job for a shot that already has a task id.

| What you see | Likely cause | What to do |
|---|---|---|
| `validate` / `plan` / `run` refuses: character bible | A face or `ugc-ad` kind is on the list and there is no `character_bible` or inline `characters` with `description` | Write the bible, or set `characters_on_camera` false only for a hands-only cut with no character ids |
| Persona changes between shots | Description was paraphrased, or `ref_image` was dropped | Paste the same description; reuse the same ref on every face shot |
| `CHARACTER LOCK` ignored and wardrobe drifts | Shot prompt contradicts `forbid` | Delete the contradicting words; keep the lock line |
| Lip-sync drifts or the mouth keeps moving after the line | Line longer than ~10 words, or more than one speaker | Shorten the line, or switch that shot to VO over `seedance-mini` b-roll |
| `run` exits before spend, estimate mismatch | Plan changed after the user said yes | `plan` again, show the new total, wait for yes, pass that exact number |
| `INSUFFICIENT_CREDITS` | Balance too low | Stop. Send the top-up link in `next_step`. Do not retry |
| Timeout / `NETWORK` after submit | Poll stopped | Run the same `run` again. Finished and submitted shots resume |
| `captions_burned` is false, or assemble prints a warning | Shot `caption` empty, or `--no-captions` | Put the spoken line on `caption` and assemble without `--no-captions`, unless they asked for softsubs only |
| Product label or shape changes | Pack is readable and there is no product bible | Add `powertokens-product-qc` before more i2v |
| Award, "clinically proven", or fake buyer language | Claim lint, or a made-up review | Delete it. Use the approved claim sheet only |
| A face appears in a hands-only shot | Prompt did not forbid a person, or the opt-out was set while a character id was still on the shot | Prompt "hands only, no face", keep `characters_on_camera` false, and remove character ids |
| Hook variant replaced the whole ad | The hook re-take rewrote later shots | Re-generate only the hook shot id; leave the other state entries |
