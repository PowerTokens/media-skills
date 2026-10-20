# PowerTokens Media Skills

Let Claude Code, Codex and other [Agent Skills](https://agentskills.io)-compatible agents generate **video, images and voiceovers** with Chinese frontier models — Seedance, Wan, Kling, Seedream and MiniMax — through one [PowerTokens](https://powertokens.ai/?utm_source=github&utm_medium=oss&utm_campaign=media-skills) account. No Chinese phone number or account needed.

> 中文：一个 PowerTokens 账号，让 Claude Code / Codex 直接调用 Seedance、Wan、可灵、Seedream 和 MiniMax 生成视频、图片和配音。

You ask in plain language; the agent picks the skill, calls the API, waits for the job and saves the file to `./outputs/`.

```text
> Make a 5-second vertical video of iced coffee being poured, slow push-in, morning light
> Turn product.png into an 8-second 9:16 ad with a 15-second English voiceover
> Generate 4 storyboard frames of a cyberpunk street market with Seedream
```

## Skills

| Skill | What it does |
|---|---|
| `powertokens-video` | Text-to-video and image-to-video; submits, polls, downloads the MP4; resume without paying twice |
| `powertokens-image` | Text-to-image and reference-image edits (Seedream) |
| `powertokens-speech` | Text-to-speech / voiceover (MiniMax speech) |
| `powertokens-ad-video` | Workflow: product image + copy → vertical ad clip + voiceover |

Scripts are plain Python 3.8+ standard library. Nothing to `pip install`.

## Install

### Claude Code

```text
/plugin marketplace add PowerTokens/media-skills
/plugin install powertokens-media@powertokens
```

Or copy the skill folders yourself:

```bash
git clone https://github.com/PowerTokens/media-skills
cp -r media-skills/plugins/powertokens-media/skills/* ~/.claude/skills/
```

### Codex

Ask Codex to install from GitHub:

```text
$skill-installer install https://github.com/PowerTokens/media-skills/tree/main/plugins/powertokens-media/skills/powertokens-video
```

(repeat for `powertokens-image`, `powertokens-speech`, `powertokens-ad-video`), or add the whole plugin marketplace:

```bash
codex plugin marketplace add PowerTokens/media-skills
```

Manual: copy the folders into `~/.codex/skills/` (or `~/.agents/skills/`) and restart Codex.

### Other agents

Other tools that support the Agent Skills `SKILL.md` format can use the folders under `plugins/powertokens-media/skills/`.

## Connect your PowerTokens account

**Option A — browser sign-in (coming soon).** The first time you generate something, the agent runs `scripts/pt_login.py login`, your browser opens PowerTokens, you sign in or sign up, and you're done. The token is stored in `~/.config/powertokens/credentials.json` (file mode 600).

**Option B — API key.** Create a key at [powertokens.ai/api-keys](https://powertokens.ai/api-keys?utm_source=github&utm_medium=oss&utm_campaign=media-skills) and add it to your shell profile:

```bash
export POWERTOKENS_API_KEY="your-key"
```

If both exist, `POWERTOKENS_API_KEY` wins. Check with `python3 scripts/pt_login.py status`. Don't paste keys into the chat; the skills never print them.

## Models

| Type | Model id | Notes |
|---|---|---|
| Video | `wan3.0-video` (default) | 2–30 s, 480p–1080p, native audio |
| Video | `wan3.0-video-prime` | Same as Wan 3.0, faster |
| Video | `dreamina-seedance-2-0-fast-260128` | Seedance 2.0 Fast, 4–15 s, up to 720p |
| Video | `dreamina-seedance-2-5-260628` | Seedance 2.5, 4–30 s, up to 1080p |
| Video | `kling-v3` | Kling v3, 3–15 s, 720p / 1080p / 4K |
| Image | `seedream-4-5-251128` (default), `seedream-5-0-260128`, `seedream-5-0-pro-260628` | 2K / 4K or custom size, up to 14 reference images |
| Speech | `speech-2.8-turbo` (default), `speech-2.8-hd` | MiniMax; English, Chinese, Japanese and more voices |

`python3 scripts/pt_models.py --filter seedance` shows what your account can call. Prices: [powertokens.ai/models](https://powertokens.ai/models?utm_source=github&utm_medium=oss&utm_campaign=media-skills). `--dry-run` on any script shows the request (and, for video, a cost estimate) without spending.

## Prefer a GUI?

[PowerTokens Video Studio](https://github.com/PowerTokens/video-studio) is the desktop / web app for the same models, with side-by-side model comparison and batch generation.

## Development

Edit shared code in `tools/shared/`, then run `python3 tools/sync_scripts.py` (each skill folder carries its own copy so it can be installed alone). Tests: `python3 -m unittest discover tests` (offline, no credits).

## License

MIT © PowerTokens
