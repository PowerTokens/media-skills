# After the API key checks out

Every skill in this pack follows this page. The short copy in each `SKILL.md` (Credentials or Before spending) is the same rule; this file is the canonical wording.

## When it applies

The moment a credential check **succeeds**, including a re-check after the user sets a new `POWERTOKENS_API_KEY`:

- `python3 scripts/pt_login.py status` returns `"ok": true`, or
- a live check returns HTTP 200 (for example `python3 scripts/pt_models.py` listing models)

Do this in the same turn as the success. Do not end the turn on a status report.

## What to do

Ask **one** clear yes/no question, in the user's language, and wait. Do not:

- stop after a status dump ("key is valid", "you can continue", "新 Key 已通过验证")
- explain HTTP 200 unless the user asks what the check means
- call `run`, `generate`, or any other paid command in that turn
- ask the user to paste the API key, or write or print the key

Browser sign-in (`pt_login.py login`) is not enabled yet. A missing key still means: they create one at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and set `POWERTOKENS_API_KEY` in their shell. Never ask for the key in chat.

### A plan or estimate was already shown

Restate **that** plan: model and estimated cost (and shot count or duration if you have them). Ask whether to continue **that** generation. This yes/no is the spend gate — wait for an explicit yes before `run`, `generate`, or any other spend. Approval from before the key wall does not replace this question.

> Key is valid. Continue generating with `<model>`, estimated `<cost>`? Yes or no.
>
> Key 已通过。按刚才的方案继续生成吗？模型 `<model>`，预估 `<cost>`。是或否？

### No plan yet

Ask whether to proceed with **this skill's next unpaid step** (name it). A yes here only starts intake, a prompt, or a free `plan` / `--dry-run`. It is not permission to spend. Paid work still waits for an explicit yes on the estimate.

> Key is valid. Continue with `<next unpaid step>` before anything is generated? Yes or no.
>
> Key 已通过。接下来做 `<下一步>`（先不扣费）吗？是或否？

## Next unpaid step, by skill

| Skill | Name this in the question |
|---|---|
| `powertokens-video` | picking settings and a `--dry-run` cost (default model stays Seedance Mini) |
| `powertokens-image` | confirming the prompt and size |
| `powertokens-speech` | confirming the script and voice |
| `powertokens-pipeline` | writing or validating the shot list, then `plan` |
| `powertokens-product-ad` | intake, the claim sheet, or the storyboard — whichever is still open — then `plan` |
| `powertokens-ugc-ad` | the brief, script, or shot list, then `plan` |
| `powertokens-short-drama` | the logline, character bible, or beat sheet, then `plan` |
| `powertokens-social-variants` | a free reformat vs a paid regen, then `plan` for anything paid |
| `powertokens-bilingual-voiceover` | the EN/ZH line pair for approval, then `plan` |
| `powertokens-travel-poster` | the poster prompt and the one-image cost confirm |
| `powertokens-product-qc` | the product bible (category → subtype → parts). Vision QC spends — confirm again before that call |
| `powertokens-model-routing` | handing off to the generation skill's intake or a `--dry-run` / `plan` |
| `powertokens-prompting` | handing the prompt to intake or a cost plan on the skill that will generate |

If they already answered yes to **this** question for **this** plan, do not ask it again.
