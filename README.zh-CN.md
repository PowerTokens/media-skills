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
| `powertokens-ugc-ad` | UGC / 口播广告：按品类写节拍，付费前过费用门，出镜必须有角色 bible |
| `powertokens-short-drama` | 多镜短剧，角色参考图一致 |
| `powertokens-social-variants` | 9:16 / 1:1 / 16:9、钩子 A/B、裁剪 |
| `powertokens-bilingual-voiceover` | 同一成片的中英旁白版本 |
| `powertokens-travel-poster` | 旅行静物 → 3:4 拼贴海报（Seedream） |

脚本是纯 **Python 3.8+** 标准库，不用 `pip install`。成片拼接需要本机有 `ffmpeg`。付费步骤一律：`pipeline.py plan` → 你确认 → `run --approve-estimate <总额>`。

## 各 skill 用法

直接说需求，Agent 会自己挑技能。付费步骤一律先报预估费用，等你确认。文件输出到 `./outputs/`。

**核心**

- **`powertokens-video`**：单个镜头，文生视频或图生视频（默认 Seedance 2.0 Mini）。
  试试：`把这张照片做成 5 秒缓慢推近的竖版视频` → MP4
- **`powertokens-image`**：用 Seedream 出单张图或按参考图改图。
  试试：`画一张黄昏灯塔的 3:4 扁平插画海报` → PNG/JPG
- **`powertokens-speech`**：MiniMax 语音合成（默认 `speech-2.8-turbo`）。
  试试：`用沉稳的女声把这段稿子读出来` → MP3/WAV

**选型与提示**（本身不花钱）

- **`powertokens-model-routing`**：按画质、速度、价格、时长、比例、分辨率选模型。
  试试：`10 秒 1080p 竖版、预算 1 美元以内，用哪个模型？` → 推荐方案，附限制和标价
- **`powertokens-prompting`**：写提示词或修提示词：镜头结构、运镜、时长、常见失败修复。
  试试：`人物的脸在镜头之间一直漂，帮我改提示词` → 改写后的提示词

**成片生产**

- **`powertokens-pipeline`**：所有多镜头任务：JSON 分镜 → 关键帧 → 镜头 → 旁白 → 成片 MP4。先 `plan` 报预估，你确认后才 `run`。3–4 张静帧全部生成并过检后，才并行图生视频。旁白逐句生成，某句被 `CONTENT_POLICY` 拦截就改写一次重试。字幕烧录进画面。中断可续跑，不重复扣费。
  试试：`把这个分镜渲染成 20 秒视频` → 成片 MP4，以及各镜头、静帧、旁白
- **`powertokens-product-ad`**：从商品链接或照片出 10–30 秒竖版广告。先整理卖点表（claim sheet）给你确认，再写钩子、分镜、保留真实商品的关键帧、镜头、旁白和字幕，规则同上。画面里不出现第三方品牌、Logo 或文字，除非该品牌就是商品本身或你已同意。
  试试：`用这个商品链接做一条 15 秒竖版英文广告` → 卖点表，然后是成片 MP4
- **`powertokens-product-qc`**：保证实物商品前后一致：产品 bible（大类 → 分型 → 部件）、提示词硬约束、关键帧视觉质检（含 Logo 检查）。
  试试：`给这双球鞋建产品 bible，并检查这些关键帧` → bible JSON + 通过/不通过报告
- **`powertokens-ugc-ad`**：手机原生感的 UGC 广告：真实测评、开箱、痛点/解决、第一视角演示、三个理由。用虚构人设（锁定角色 bible）或只拍手部。
  试试：`给这个水杯做一条 20 秒开箱 UGC 广告，只拍手` → 带字幕的 MP4 + 多个钩子版本
- **`powertokens-short-drama`**：多镜头短剧，角色参考图贯穿每个镜头，保持一致。
  试试：`写并制作一集 60 秒、结尾留悬念的微短剧` → 节拍表、角色参考图、单集 MP4
- **`powertokens-social-variants`**：多平台版本与 A/B 测试：9:16 / 1:1 / 16:9、不同钩子、6/15/30 秒剪短版。裁剪和剪短免费，重新生成先估费。
  试试：`做方形和横版各一版，再加两个钩子版本` → `<project>-<ratio>-<hook>.mp4` + 版本对照表
- **`powertokens-bilingual-voiceover`**：同一套画面配英文和中文（普通话/粤语）旁白；按时长改写稿子，不逐字直译。
  试试：`这条广告画面不变，出一个普通话版本` → 中英两版成片，字幕对应
- **`powertokens-travel-poster`**：旅行或摄影照片 → 3:4「第二世界」拼贴海报，配一句简短手写说明。
  试试：`把这张海边照片做成拼贴海报` → 3:4 海报图

## 安装

整包是一个插件 `powertokens-media`。装上这个插件就会带上全部技能。Codex 和 Claude Code 没有单独的“全部安装”开关。`marketplace add` 只登记来源，真正装上整包的是后面的插件安装。

### 整包

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

装完后新开一个 Codex 对话，技能才会出现。

**拷贝全部技能目录**

```bash
git clone https://github.com/PowerTokens/media-skills
cp -R media-skills/plugins/powertokens-media/skills/* ~/.codex/skills/
```

Claude Code 用 `~/.claude/skills/`。其它宿主多用 `~/.agents/skills/`。拷完后重启应用。

### 只装一个技能

Codex 的 `$skill-installer` 一次只装一个目录。把路径最后一段换成技能表里的任意 id：

```text
$skill-installer install https://github.com/PowerTokens/media-skills/tree/main/plugins/powertokens-media/skills/powertokens-product-ad
```

也可以只把那一个文件夹拷进 `~/.codex/skills/`、`~/.claude/skills/` 或 `~/.agents/skills/`。

### 其它宿主

凡是能加载 `SKILL.md` 目录的工具，都可以用 `plugins/powertokens-media/skills/`。要整包就拷整个 `skills` 目录，要单个技能就拷一个子文件夹。

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
| 视频 | `dreamina-seedance-2-0-mini-260615`（默认，`seedance-mini`） | 最便宜；4–15 秒，最高 720p，480p 与 720p 均约 $0.031/秒 |
| 视频 | `wan3.0-video` | 2–30 秒，480p–1080p，原生音频 |
| 视频 | `wan3.0-video-prime` | 同 Wan 3.0，更快 |
| 视频 | `dreamina-seedance-2-0-fast-260128` | Seedance 2.0 Fast；促销约 $0.061/秒 |
| 视频 | `dreamina-seedance-2-5-260628` | **Seedance 2.5** — 更长 / 更高规格 |
| 视频 | `kling-v3` | 可灵 v3，3–15 秒，最高 4K |
| 图像 | `seedream-4-5-251128`（默认）、`seedream-5-0-260128`、`dola-seedream-5-0-pro-260628` | 最多 14 张参考图 |
| 语音 | `speech-2.8-turbo`（默认）、`speech-2.8-hd` | MiniMax；中 / 英 / 日等 |

线上可用 id：`python3 scripts/pt_models.py --filter seedance`。价格：[powertokens.ai/models](https://powertokens.ai/models?utm_source=github&utm_medium=oss&utm_campaign=media-skills)。花钱前先 `--dry-run`。

## 更想用图形界面？

[PowerTokens Video Studio](https://github.com/PowerTokens/video-studio) — 同一批模型，支持并排对比与批量生成。

## 开发

改共享代码请编辑 `tools/shared/`，示例在 `tools/examples/`，然后跑 `python3 tools/sync_scripts.py`。测试：`python3 -m unittest discover tests`（离线）。设计说明见 `docs/`。

## 话题 / 关键词

`agent-skills` · `claude-code` · `codex` · `seedance` · `seedance-2.5` · `wan` · `kling` · `seedream` · `minimax` · `ai-video` · `text-to-video` · `image-to-video` · `product-ad` · `ugc` · `tiktok` · `powertokens`

## 许可证

MIT © PowerTokens
