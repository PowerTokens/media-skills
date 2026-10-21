# PowerTokens Media Skills

**中文** · [English](README.md)

给 Claude Code、Codex、Cursor 以及其它兼容 [Agent Skills](https://agentskills.io) 的 Agent，装上 **Seedance / Wan / 可灵 / Seedream / MiniMax** 出片能力。一个 [PowerTokens](https://powertokens.ai/?utm_source=github&utm_medium=oss&utm_campaign=media-skills) API Key 即可，不需要国内手机号。

<p align="center">
  <a href="https://agentskills.io"><img src="https://img.shields.io/badge/Agent_Skills-compatible-111111?style=flat-square" alt="Agent Skills"></a>
  <a href="#安装"><img src="https://img.shields.io/badge/Claude_Code-plugin-d97706?style=flat-square" alt="Claude Code"></a>
  <a href="#安装"><img src="https://img.shields.io/badge/Codex-skill-10b981?style=flat-square" alt="Codex"></a>
  <a href="https://github.com/PowerTokens/media-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT"></a>
  <a href="https://powertokens.ai/models?utm_source=github&utm_medium=oss&utm_campaign=media-skills"><img src="https://img.shields.io/badge/Seedance-2.5_%2F_Mini_%2F_Fast-7c3aed?style=flat-square" alt="Seedance"></a>
  <a href="https://powertokens.ai/?utm_source=github&utm_medium=oss&utm_campaign=media-skills"><img src="https://img.shields.io/badge/PowerTokens-API-0ea5e9?style=flat-square" alt="PowerTokens"></a>
</p>

<p align="center">
  <a href="#为什么做这个">为什么做</a> ·
  <a href="#示例north-loop-产品广告">North Loop 样片</a> ·
  <a href="#技能列表">技能</a> ·
  <a href="#安装">安装</a> ·
  <a href="#接入-powertokens-账号">API Key</a> ·
  <a href="#模型">模型</a>
</p>

## 为什么做这个

越来越多人已经在用编码 Agent 跑 **Seedance 2.5 / 2.0 Mini**。多数「一个模型、一个脚本」的 skill 只做到单次生成。本仓库是上面的**生产层**：

| 只用裸 Seedance skill 时的痛点 | media-skills 补上什么 |
|---|---|
| 角色 / 产品每镜漂移（抽卡） | **产品 bible** + 部件参考统一到原产品 + i2v 前视觉质检 |
| 钩子文案只有氛围、没有卖点 | **Claim sheet** → 有出处的钩子 / 字幕 / 旁白（拒绝空氛围句） |
| 还没估清费用就烧额度 | `pipeline.py plan` → 批准估算 → `run`（可续跑、不重复扣费） |
| 要的是整支竖屏广告，不是单镜头 | 分镜表 → Seedream 关键帧 → Seedance/Wan/可灵 → MiniMax 旁白 → 烧字幕 |

面向：Agent Skills 市场、Claude Code 插件、Seedance 2.x Agent 工作流、产品广告 / UGC / 9:16 短视频，以及不方便注册国内账号时的出海出片。

## 示例：North Loop 产品广告

<p align="center">
  <img src="assets/examples/northloop/preview.jpg" width="200" alt="North Loop 广告拼图">
  &nbsp;
  <img src="assets/examples/northloop/s01.jpg" width="100" alt="s01 关键帧 — 翻盖、高瓶身">
  <img src="assets/examples/northloop/s02.jpg" width="100" alt="s02 关键帧">
  <img src="assets/examples/northloop/s03.jpg" width="100" alt="s03 关键帧">
  <img src="assets/examples/northloop/s04.jpg" width="100" alt="s04 关键帧">
</p>

<sub><strong>AI 生成演示素材</strong>（虚构品牌「North Loop」保温杯，非真实商品）。流程：Seedream 关键帧 → <strong>Seedance 2.0 Mini</strong> 图生视频（4×4 秒，9:16）→ MiniMax 旁白 + TikTok 风格字幕。产品 bible 锁定瓶身与双盖结构；单独部件参考统一回主产品图。鉴权：<code>POWERTOKENS_API_KEY</code>。</sub>

- 复现分镜：[`tools/examples/northloop-ad.json`](tools/examples/northloop-ad.json)
- 样片：[`assets/examples/northloop/demo.mp4`](assets/examples/northloop/demo.mp4)
- 走查说明：[`docs/examples-northloop.md`](docs/examples-northloop.md)
- 一致性手册：[`docs/product-consistency-qc.md`](docs/product-consistency-qc.md)

<p align="center"><img src="assets/demo.gif" width="216" alt="早期演示：Wan 3.0 + MiniMax，Seedance Fast + Seedream 参考"></p>

<sub>仓库里还有：Seedream → Wan 3.0 多镜 + 字幕；Seedance Fast 带图参考（480p 草稿）。</sub>

## 可以这样跟 Agent 说话

```text
> 做一段 5 秒竖屏视频：冰咖啡倒入杯中，缓慢推进，晨光
> 把 product.png 做成 8 秒 9:16 广告，配 15 秒英文旁白
> 根据这个商品页链接做 claim sheet，再用 Seedance Mini 出干净商业风产品广告
> 用 Seedream 出 4 张赛博朋克夜市分镜静帧
```

Agent 会选对应 skill，调用 PowerTokens，轮询任务，并把结果写到 `./outputs/`。

## 技能列表

**核心（单次调用）**

| 技能 | 作用 |
|---|---|
| `powertokens-video` | 文生视频、图生视频、参考图；提交 → 轮询 → 下载；可续跑不重复扣费 |
| `powertokens-image` | 文生图与参考编辑（Seedream） |
| `powertokens-speech` | 语音合成 / 旁白（MiniMax） |

**选型与提示**

| 技能 | 作用 |
|---|---|
| `powertokens-model-routing` | 什么任务用什么模型：限制、标价、来源 |
| `powertokens-prompting` | 分镜公式、镜头语言、时长、各模型族注意点、失败修复 |

**成片生产**

| 技能 | 作用 |
|---|---|
| `powertokens-pipeline` | JSON 分镜 → 关键帧 → 镜头 → 旁白 → 成片 MP4 + 字幕；先估费 |
| `powertokens-product-ad` | 商品链接/照片 → claim sheet → 竖屏广告（分镜、图生视频、旁白、字幕） |
| `powertokens-product-qc` | 通用产品 bible（大类 → 分型 → 部件）+ 部件参考统一 + 视觉质检 |
| `powertokens-ugc-ad` | UGC / 口播风广告，固定虚构人设 |
| `powertokens-short-drama` | 多镜短剧，角色参考图一致 |
| `powertokens-social-variants` | 9:16 / 1:1 / 16:9、钩子 A/B、裁剪 |
| `powertokens-bilingual-voiceover` | 同一成片的中英旁白版本 |
| `powertokens-travel-poster` | 旅行静物 → 3:4 拼贴海报（Seedream） |

脚本是纯 **Python 3.8+** 标准库，不用 `pip install`。成片拼接需要本机有 `ffmpeg`。付费步骤一律：`pipeline.py plan` → 你确认 → `run --approve-estimate <总额>`。

## 安装

### Claude Code（插件市场）

```text
/plugin marketplace add PowerTokens/media-skills
/plugin install powertokens-media@powertokens
```

或手动拷贝技能目录：

```bash
git clone https://github.com/PowerTokens/media-skills
cp -r media-skills/plugins/powertokens-media/skills/* ~/.claude/skills/
```

### Codex

```bash
codex plugin marketplace add PowerTokens/media-skills
```

在**新**对话里，用自然语言说要生成视频或做一条产品广告即可（不必再贴安装命令）。

仅装单个 skill：

```text
$skill-installer install https://github.com/PowerTokens/media-skills/tree/main/plugins/powertokens-media/skills/powertokens-product-ad
```

手动：拷到 `~/.codex/skills/`（或 `~/.agents/skills/`）后重启。

### 其它 Agent Skills 宿主

凡是能加载 `SKILL.md` 目录的工具，都可以用 `plugins/powertokens-media/skills/`。

## 接入 PowerTokens 账号

1. 在 [powertokens.ai/api-keys](https://powertokens.ai/api-keys?utm_source=github&utm_medium=oss&utm_campaign=media-skills) 创建 Key  
2. 写进环境变量（不要贴进聊天）：

```bash
export POWERTOKENS_API_KEY="your-key"
```

3. 检查：`python3 scripts/pt_login.py status`

若环境变量和本地已存 token 同时存在，**以 `POWERTOKENS_API_KEY` 为准**。浏览器 OAuth（`pt_login.py login`）等 PowerTokens 正式发布后再上——**今天用 API Key 就够跑通**。

## 模型

| 类型 | 模型 id | 说明 |
|---|---|---|
| 视频 | `wan3.0-video`（默认） | 2–30 秒，480p–1080p，原生音频 |
| 视频 | `wan3.0-video-prime` | 同 Wan 3.0，更快 |
| 视频 | `dreamina-seedance-2-0-mini-260615` | **Seedance 2.0 Mini** — 适合 Agent 高频试错；促销约 $0.031/秒 |
| 视频 | `dreamina-seedance-2-0-fast-260128` | Seedance 2.0 Fast；促销约 $0.061/秒 |
| 视频 | `dreamina-seedance-2-5-260628` | **Seedance 2.5** — 更长 / 更高规格 |
| 视频 | `kling-v3` | 可灵 v3，3–15 秒，最高 4K |
| 图像 | `seedream-4-5-251128`（默认）、`seedream-5-0-260128`、`dola-seedream-5-0-pro-260628` | 最多 14 张参考图 |
| 语音 | `speech-2.8-turbo`（默认）、`speech-2.8-hd` | MiniMax；中 / 英 / 日等 |

线上可用 id：`python3 scripts/pt_models.py --filter seedance`。价格：[powertokens.ai/models](https://powertokens.ai/models?utm_source=github&utm_medium=oss&utm_campaign=media-skills)。花钱前先 `--dry-run`。

## 独立产品

[PowerTokens Video Studio](https://github.com/PowerTokens/video-studio)（`PowerTokens/video-studio`）是独立的桌面/图形界面产品。本仓库只有 Agent skills。

## 开发

改共享代码请编辑 `tools/shared/`，示例在 `tools/examples/`，然后跑 `python3 tools/sync_scripts.py`。测试：`python3 -m unittest discover tests`（离线）。设计说明见 `docs/`。

## 话题 / 关键词

`agent-skills` · `claude-code` · `codex` · `seedance` · `seedance-2.5` · `wan` · `kling` · `seedream` · `minimax` · `ai-video` · `text-to-video` · `image-to-video` · `product-ad` · `ugc` · `tiktok` · `powertokens`

## 许可证

MIT © PowerTokens
