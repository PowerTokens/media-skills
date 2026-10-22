# PowerTokens Media Skills

**English** · [中文](README.zh-CN.md)

**Agent Skills** that turn Claude Code, Codex, Cursor, and other [Agent Skills](https://agentskills.io)-compatible agents into a **Seedance / Wan / Kling / Seedream / MiniMax** video desk — one [PowerTokens](https://powertokens.ai/?utm_source=github&utm_medium=oss&utm_campaign=media-skills) API key, no Chinese phone number required.

<p align="center">
  <a href="https://agentskills.io"><img src="https://img.shields.io/badge/Agent_Skills-compatible-111111?style=flat-square" alt="Agent Skills"></a>
  <a href="#install"><img src="https://img.shields.io/badge/Claude_Code-plugin-d97706?style=flat-square" alt="Claude Code"></a>
  <a href="#install"><img src="https://img.shields.io/badge/Codex-skill-10b981?style=flat-square" alt="Codex"></a>
  <a href="https://github.com/PowerTokens/media-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT"></a>
  <a href="https://powertokens.ai/models?utm_source=github&utm_medium=oss&utm_campaign=media-skills"><img src="https://img.shields.io/badge/Seedance-2.5_%2F_Mini_%2F_Fast-7c3aed?style=flat-square" alt="Seedance"></a>
  <a href="https://powertokens.ai/?utm_source=github&utm_medium=oss&utm_campaign=media-skills"><img src="https://img.shields.io/badge/PowerTokens-API-0ea5e9?style=flat-square" alt="PowerTokens"></a>
</p>

<p align="center">
  <a href="#why-this-exists">Why</a> ·
  <a href="#example-north-loop-product-ad">North Loop demo</a> ·
  <a href="#skills">Skills</a> ·
  <a href="#install">Install</a> ·
  <a href="#connect-your-powertokens-account">API Key</a> ·
  <a href="#models">Models</a>
</p>

## Why this exists

People are already shipping **Seedance 2.5 / 2.0 Mini** clips from coding agents. Most “one model, one script” skills stop at a single generate call. This pack is the **production layer** on top:

| Pain you hit with raw Seedance skills | What media-skills adds |
|---|---|
| Character / product drifts every take (“gacha loop”) | **Product bible** + part-detail unify + vision QC before i2v |
| Hook copy is vibes-only | **Claim sheet** → sourced hooks / captions / VO (reject empty atmosphere) |
| You burn credits before you know the cost | `pipeline.py plan` → approve estimate → `run` (resume, no double charge) |
| Need a full vertical ad, not one clip | Shot list → Seedream keyframes → Seedance/Wan/Kling → MiniMax VO → captions |

Built for: Agent Skills marketplaces, Claude Code plugins, Seedance 2.x agent workflows, product ads / UGC / short-form 9:16, and AI video without a Chinese account.

## Example: North Loop product ad

<p align="center">
  <img src="assets/examples/northloop/preview.jpg" width="200" alt="North Loop ad collage">
  &nbsp;
  <img src="assets/examples/northloop/s01.jpg" width="100" alt="s01 keyframe — flip-open lid, tall body">
  <img src="assets/examples/northloop/s02.jpg" width="100" alt="s02 keyframe">
  <img src="assets/examples/northloop/s03.jpg" width="100" alt="s03 keyframe">
  <img src="assets/examples/northloop/s04.jpg" width="100" alt="s04 keyframe">
</p>

<sub><strong>AI-generated demo</strong> (fictional “North Loop” thermos — not a real SKU). Pipeline: Seedream keyframes → <strong>Seedance 2.0 Mini</strong> i2v (4×4s, 9:16) → MiniMax VO + TikTok-style captions. Product bible locks body + dual-lid; part-detail refs unify onto the hero packshot. Auth: <code>POWERTOKENS_API_KEY</code>.</sub>

- Reproduce: [`tools/examples/northloop-ad.json`](tools/examples/northloop-ad.json)
- Clip: [`assets/examples/northloop/demo.mp4`](assets/examples/northloop/demo.mp4)
- Walkthrough: [`docs/examples-northloop.md`](docs/examples-northloop.md)
- Consistency playbook: [`docs/product-consistency-qc.md`](docs/product-consistency-qc.md)

<p align="center"><img src="assets/demo.gif" width="216" alt="Earlier demo: Wan 3.0 + MiniMax, Seedance Fast + Seedream ref"></p>

<sub>Also in-repo: Seedream → Wan 3.0 multi-shot + captions; Seedance Fast with image reference (480p drafts).</sub>

## Talk to your agent like this

```text
> Make a 5-second vertical video of iced coffee being poured, slow push-in, morning light
> Turn product.png into an 8-second 9:16 ad with a 15-second English voiceover
> Build a claim sheet from this PDP URL, then a clean-premium product ad with Seedance Mini
> Generate 4 storyboard frames of a cyberpunk street market with Seedream
```

The agent picks the skill, calls PowerTokens, polls the job, and writes files under `./outputs/`.

## Skills

**Core (one call each)**

| Skill | What it does |
|---|---|
| `powertokens-video` | Text-to-video, image-to-video, refs; submit → poll → download; resume without paying twice |
| `powertokens-image` | Text-to-image and reference edits (Seedream) |
| `powertokens-speech` | Text-to-speech / voiceover (MiniMax) |

**Know-how**

| Skill | What it does |
|---|---|
| `powertokens-model-routing` | Which model for which job: limits, list prices, sources |
| `powertokens-prompting` | Shot formula, camera language, timing, per-family notes, failure fixes |

**Production**

| Skill | What it does |
|---|---|
| `powertokens-pipeline` | JSON shot list → keyframes → clips → VO → assembled MP4 + captions; estimate first |
| `powertokens-product-ad` | Product URL/photo → claim sheet → vertical ad (storyboard, i2v, VO, captions) |
| `powertokens-product-qc` | Generic product bible (category → subtype → parts) + part-detail unify + vision QC |
| `powertokens-ugc-ad` | UGC / talking-head ads: category beats, cost gate before spend, character bible when someone is on camera |
| `powertokens-short-drama` | Multi-shot episodes with character refs |
| `powertokens-social-variants` | 9:16 / 1:1 / 16:9, hook A/B, cut-downs |
| `powertokens-bilingual-voiceover` | English + Chinese VO of the same cut |
| `powertokens-travel-poster` | Travel still → 3:4 collage poster (Seedream) |

Scripts are plain **Python 3.8+** stdlib — nothing to `pip install`. Assembly uses `ffmpeg` if present. Paid steps always go through `pipeline.py plan` → your yes → `run --approve-estimate <total>`.

## Use each skill

Just describe the job; the agent picks the skill. Paid steps always show an estimate first and wait for your yes. Files land in `./outputs/`.

**Core**

- **`powertokens-video`** — one clip, text-to-video or image-to-video (default Seedance 2.0 Mini).
  Try: `Animate this photo into a 5 s slow push-in, 9:16.` → MP4
- **`powertokens-image`** — one image or a reference edit with Seedream.
  Try: `Make a 3:4 poster of a lighthouse at dusk, flat illustration.` → PNG/JPG
- **`powertokens-speech`** — text-to-speech with MiniMax (default `speech-2.8-turbo`).
  Try: `Read this script aloud in a calm female voice.` → MP3/WAV

**Know-how** (no spend on its own)

- **`powertokens-model-routing`** — which model fits quality, speed, price, length, ratio or 1080p.
  Try: `Which model for a 10 s 1080p vertical clip under $1?` → a recommendation with limits and list price
- **`powertokens-prompting`** — write or fix prompts: shot structure, camera moves, timing, failure fixes.
  Try: `The face keeps drifting between shots, fix my prompt.` → rewritten prompt

**Production**

- **`powertokens-pipeline`** — any multi-shot job: JSON shot list → keyframes → clips → VO → assembled MP4. `plan` shows the estimate → you approve → `run`. All 3–4 stills are generated and QC-passed before clips render in parallel (image-to-video). VO is generated sentence by sentence; a line blocked by `CONTENT_POLICY` is rewritten once. Captions are burned in. Resumes without paying twice.
  Try: `Render this storyboard into a 20 s video.` → final MP4 + clips, stills, VO
- **`powertokens-product-ad`** — 10–30 s vertical ad from a product URL or photo. Builds a claim sheet for your approval, then hook, storyboard, keyframes that keep the real product, clips, VO and captions via the pipeline rules above. No third-party brands, logos or text in frame unless that brand is the SKU or you approved it.
  Try: `Make a 15 s vertical English ad from this product link.` → claim sheet, then final MP4
- **`powertokens-product-qc`** — keep a physical product consistent: product bible (category → subtype → parts), prompt constraints, vision QC of keyframes, including the logo check.
  Try: `Build a product bible for this sneaker and check these keyframes.` → bible JSON + pass/fail report
- **`powertokens-ugc-ad`** — phone-native UGC ad: testimonial, unboxing, problem/solution, POV demo or three reasons, with a fictional persona (character bible locked) or hands-only b-roll.
  Try: `Make a 20 s unboxing UGC ad for this bottle, hands only.` → MP4 with captions + hook variants
- **`powertokens-short-drama`** — multi-shot story episodes with recurring characters locked by reference sheets.
  Try: `Write and produce a 60 s micro-drama episode with a cliffhanger.` → beat sheet, reference sheets, episode MP4
- **`powertokens-social-variants`** — platform versions and A/B tests: 9:16 / 1:1 / 16:9, alternate hooks, 6/15/30 s cut-downs. Crops and cut-downs are free; regenerations are estimated first.
  Try: `Make square and landscape versions plus two hook variants.` → `<project>-<ratio>-<hook>.mp4` + variant table
- **`powertokens-bilingual-voiceover`** — English and Chinese (Mandarin/Cantonese) VO of the same visuals; the script is adapted to timing, not translated literally.
  Try: `Make a Mandarin version of this ad with the same shots.` → EN and ZH cuts with matching captions
- **`powertokens-travel-poster`** — travel or photography still → 3:4 "second world" collage poster with a short handwritten caption.
  Try: `Make this beach photo into a collage poster.` → 3:4 poster image

## Install

The pack is one plugin, `powertokens-media`. Installing that plugin loads every skill. Codex and Claude Code do not have a separate install-all flag. `marketplace add` only registers the source. The plugin install is the whole pack.

### Whole pack

**Claude Code**

```text
/plugin marketplace add PowerTokens/media-skills
/plugin install powertokens-media@powertokens
```

**Codex**

```bash
codex plugin marketplace add PowerTokens/media-skills
codex plugin add powertokens-media@powertokens
```

Start a new Codex thread after install so the bundled skills load.

**Copy every skill folder**

```bash
git clone https://github.com/PowerTokens/media-skills
cp -R media-skills/plugins/powertokens-media/skills/* ~/.codex/skills/
```

Claude Code uses `~/.claude/skills/`. Other hosts often use `~/.agents/skills/`. Restart the app after copying.

### One skill

Codex `$skill-installer` installs a single folder. Change the last segment to any id in the skills table:

```text
$skill-installer install https://github.com/PowerTokens/media-skills/tree/main/plugins/powertokens-media/skills/powertokens-product-ad
```

Or copy that one folder into `~/.codex/skills/`, `~/.claude/skills/`, or `~/.agents/skills/`.

### Other Agent Skills hosts

Any tool that loads `SKILL.md` folders can use `plugins/powertokens-media/skills/`. Copy the whole `skills` directory for the pack, or one skill folder for a single skill.

## Connect your PowerTokens account

1. Create a key at [powertokens.ai/api-keys](https://powertokens.ai/api-keys?utm_source=github&utm_medium=oss&utm_campaign=media-skills)
2. Put it in your shell (never paste into chat):

```bash
export POWERTOKENS_API_KEY="your-key"
```

3. Check: `python3 scripts/pt_login.py status`

If both an env key and a saved token exist, **`POWERTOKENS_API_KEY` wins**. Browser OAuth (`pt_login.py login`) lands later when PowerTokens publishes it — **API Key is enough to ship today**.

## Models

| Type | Model id | Notes |
|---|---|---|
| Video | `dreamina-seedance-2-0-mini-260615` (default, `seedance-mini`) | Cheapest; 4–15 s, max 720p, ~$0.031/s at 480p and 720p |
| Video | `wan3.0-video` | 2–30 s, 480p–1080p, native audio |
| Video | `wan3.0-video-prime` | Same as Wan 3.0, faster |
| Video | `dreamina-seedance-2-0-fast-260128` | Seedance 2.0 Fast; promo ~$0.061/s |
| Video | `dreamina-seedance-2-5-260628` | **Seedance 2.5** — longer / higher-end clips |
| Video | `kling-v3` | Kling v3, 3–15 s, up to 4K |
| Image | `seedream-4-5-251128` (default), `seedream-5-0-260128`, `dola-seedream-5-0-pro-260628` | Up to 14 refs |
| Speech | `speech-2.8-turbo` (default), `speech-2.8-hd` | MiniMax; English, Chinese, Japanese, and more |

Live ids: `python3 scripts/pt_models.py --filter seedance`. Prices: [powertokens.ai/models](https://powertokens.ai/models?utm_source=github&utm_medium=oss&utm_campaign=media-skills). Use `--dry-run` before spending.

## Prefer a GUI?

[PowerTokens Video Studio](https://github.com/PowerTokens/video-studio) — same models, side-by-side compare and batch generation.

## Development

Edit shared code in `tools/shared/`, examples in `tools/examples/`, then `python3 tools/sync_scripts.py`. Tests: `python3 -m unittest discover tests` (offline). Design notes: `docs/`.

## Topics / keywords

`agent-skills` · `claude-code` · `codex` · `seedance` · `seedance-2.5` · `wan` · `kling` · `seedream` · `minimax` · `ai-video` · `text-to-video` · `image-to-video` · `product-ad` · `ugc` · `tiktok` · `powertokens`

## License

MIT © PowerTokens
