# PowerTokens Media Skills

**Agent Skills** that turn Claude Code, Codex, Cursor, and other [Agent Skills](https://agentskills.io)-compatible agents into a **Seedance / Wan / Kling / Seedream / MiniMax** video desk — one [PowerTokens](https://powertokens.ai/?utm_source=github&utm_medium=oss&utm_campaign=media-skills) API key, no Chinese phone number.

> 中文：给 Claude Code / Codex / Cursor 装上 Seedance、Wan、可灵、Seedream、MiniMax。一个 PowerTokens Key，直接出产品广告、UGC、分镜成片。

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

**Trend fit:** Agent Skills marketplaces · Claude Code plugins · Seedance 2.x agent workflows · product ads / UGC / short-form 9:16 · AI video without a CN account.

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
| `powertokens-ugc-ad` | UGC / talking-head ads with a consistent fictional persona |
| `powertokens-short-drama` | Multi-shot episodes with character refs |
| `powertokens-social-variants` | 9:16 / 1:1 / 16:9, hook A/B, cut-downs |
| `powertokens-bilingual-voiceover` | EN + ZH VO of the same cut |
| `powertokens-travel-poster` | Travel still → 3:4 collage poster (Seedream) |

Scripts are plain **Python 3.8+** stdlib — nothing to `pip install`. Assembly uses `ffmpeg` if present. Paid steps always go through `pipeline.py plan` → your yes → `run --approve-estimate <total>`.

## Install

### Claude Code (plugin marketplace)

```text
/plugin marketplace add PowerTokens/media-skills
/plugin install powertokens-media@powertokens
```

Or copy skill folders:

```bash
git clone https://github.com/PowerTokens/media-skills
cp -r media-skills/plugins/powertokens-media/skills/* ~/.claude/skills/
```

### Codex

```text
$skill-installer install https://github.com/PowerTokens/media-skills/tree/main/plugins/powertokens-media/skills/powertokens-video
```

(repeat for other skills), or:

```bash
codex plugin marketplace add PowerTokens/media-skills
```

Manual: copy into `~/.codex/skills/` (or `~/.agents/skills/`) and restart.

### Other Agent Skills hosts

Any tool that loads `SKILL.md` folders can use `plugins/powertokens-media/skills/`.

## Connect your PowerTokens account

1. Create a key at [powertokens.ai/api-keys](https://powertokens.ai/api-keys?utm_source=github&utm_medium=oss&utm_campaign=media-skills)
2. Put it in your shell (never paste into chat):

```bash
export POWERTOKENS_API_KEY="your-key"
```

3. Check: `python3 scripts/pt_login.py status`

If both an env key and a saved token exist, **`POWERTOKENS_API_KEY` wins**. Browser OAuth (`pt_login.py login`) lands later when PowerTokens publishes it — **Key-first is enough to ship**.

## Models

| Type | Model id | Notes |
|---|---|---|
| Video | `wan3.0-video` (default) | 2–30 s, 480p–1080p, native audio |
| Video | `wan3.0-video-prime` | Same as Wan 3.0, faster |
| Video | `dreamina-seedance-2-0-mini-260615` | **Seedance 2.0 Mini** — agent-friendly cost; promo ~$0.031/s |
| Video | `dreamina-seedance-2-0-fast-260128` | Seedance 2.0 Fast; promo ~$0.061/s |
| Video | `dreamina-seedance-2-5-260628` | **Seedance 2.5** — longer / higher-end clips |
| Video | `kling-v3` | Kling v3, 3–15 s, up to 4K |
| Image | `seedream-4-5-251128` (default), `seedream-5-0-260128`, `dola-seedream-5-0-pro-260628` | Up to 14 refs |
| Speech | `speech-2.8-turbo` (default), `speech-2.8-hd` | MiniMax; EN / ZH / JA + |

Live ids: `python3 scripts/pt_models.py --filter seedance`. Prices: [powertokens.ai/models](https://powertokens.ai/models?utm_source=github&utm_medium=oss&utm_campaign=media-skills). Use `--dry-run` before spending.

## Prefer a GUI?

[PowerTokens Video Studio](https://github.com/PowerTokens/video-studio) — same models, side-by-side compare and batch gen.

## Development

Edit shared code in `tools/shared/`, examples in `tools/examples/`, then `python3 tools/sync_scripts.py`. Tests: `python3 -m unittest discover tests` (offline). Design notes: `docs/`.

## Topics / keywords

`agent-skills` · `claude-code` · `codex` · `seedance` · `seedance-2.5` · `wan` · `kling` · `seedream` · `minimax` · `ai-video` · `text-to-video` · `image-to-video` · `product-ad` · `ugc` · `tiktok` · `powertokens`

## License

MIT © PowerTokens
