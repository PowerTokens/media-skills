# Product consistency QC（产品一致性质检）

Clear English with Chinese labels. **Generic** lock sheet for any physical SKU (drinkware, footwear, bag, beauty, devices, apparel, etc.) — not thermos-only. Seedream keyframes often invent, omit, or hybridize parts; catch that before i2v.

**Trigger example (not the only case):** northloop-ad under drinkware — dual-lid thermos; a keyframe put a plastic pour opening on the screw threads. Refs alone were not enough; the model invented a hybrid. The same failure mode appears on sneakers (wrong outsole), bags (wrong closure), phones (invented ports), etc.

## Required thinking chain（必做推理链）

Fill the bible in this order — do **not** jump to lid-only fields:

| Step | Field | Chinese | What to write |
|---|---|---|---|
| **1** | `category` | **商品大类** | Broad class: drinkware, footwear, bag, beauty, consumer_electronics, apparel, furniture, food_packaging, … |
| **2** | `subtype` | **具体分型** | Concrete type inside that class: dual-lid thermos vs screw-only bottle; lace-up running shoe vs slip-on; top-zip tote vs flap backpack |
| **3** | `immutable.parts` | **组成拆解 (BOM)** | Ordered real parts `{id, role, how, states?}` — body, openings, closures, hardware, labels, accessories, sole, screen, pump, … |
| **4** | forbid / colors / logos / proportions / refs | **禁止乱改、颜色材质、logo、比例、参考图、禁止第三方品牌道具** | Derive forbid from part risks, including the default third-party brand-prop line; then lock finish, marks, silhouette, 1–3 refs |

Chinese quick labels: **结构部件/状态、禁止乱改、颜色材质、logo、比例、参考图**.

## Priority order (do these first → last)

| P | Mechanism | Cost | When |
|---|---|---|---|
| **P0** | **Product bible / lock sheet** (category → subtype → parts) before any paid gen | Free | Always for product-ad |
| **P0** | **Prompt hard constraints** from the bible (forbid wrong / hybrid parts) | Free | Every keyframe + i2v prompt |
| **P1** | **Pre-flight gate** in `pipeline plan/run`: refuse if bible missing | Free | `kind: product-ad` or `--require-product-bible` |
| **P1** | **Post-keyframe vision check** (cheap chat+vision via PT) vs bible + refs | Low (1 chat call / keyframe) | After each Seedream keyframe |
| **P2** | **Human approve** hero / packshot frames before i2v | Free (time) | Optional; default on for hero shots |
| **P2** | **Shot-to-shot lock**: same refs + compare structure modes across keyframes | Free–low | Multi-shot ads |
| **P3** | **Eval fixtures** (golden bibles per category + offline schema tests) | Free | CI / offline |

## 1. Product bible / lock sheet（产品圣经）

Create **before** storyboard spend. Store as JSON next to the shot list. Schema lives in `tools/shared/product_qc.py`. Examples:

- `tools/examples/product-bible.thermos.json` — drinkware / dual-lid thermos
- `tools/examples/product-bible.sneaker.json` — footwear / lace-up running shoe
- `tools/examples/product-bible.bag.json` — bag / top-zip tote

### Top-level required

- `product_name` — display name
- `category` — 大类 (string)
- `subtype` — 分型 (string)
- `immutable` — object (see below)
- `refs` — 1–5 `{path, shows?, kind?, part?}` approved photos (hero + optional part-detail)

### Optional top-level

- `qc_model`, `notes`, `must_match_refs` (string list of part ids that must match refs exactly)
- Each ref may set `kind`: `hero` (full SKU packshot) or `part_detail` (single BOM part close-up) and `part`: `<parts[].id>` when `kind` is `part_detail`

### `immutable` required

| Field | Meaning |
|---|---|
| **`parts`** | Canonical BOM: non-empty `[{id, role, how, states?}]`. Roles e.g. `body`, `closure`, `opening`, `hardware`, `sole`, `label`, `accessory`, `structure`. |
| `forbid` | Non-empty string list — category-agnostic + product-specific forbidden alterations (derive from part risks). Always include: `no third-party logos, wordmarks, or brand-identifiable devices (MacBook, iPhone, etc.) unless approved` |
| `colors` | Finish / material lock |
| `logos` | string or `null` / `"none"` — the SKU's own mark only. Third-party logos, wordmarks, packaging, and brand-identifiable devices in frame are forbidden unless the advertised SKU is that brand or the user explicitly approved showing it |
| `proportions` | Silhouette / geometry notes |

**Aliases (read-normalized):**

- `immutable.structure` — list of `{id, how}` → normalized into `parts` with `role=structure` if `parts` absent
- `immutable.lid_modes` — legacy thermos field → normalized into `parts` with `role=closure`

After load, the runtime bible always has `immutable.parts` (and a derived `structure` id/how list for emitters).


### Part-detail refs → unify with hero（单独部件参考必须与原产品统一）

When a shot needs a close-up of one BOM part that the hero packshot does not show clearly (open lid, sole tread, zipper pull, port layout, pump head, …):

1. Find or shoot a **part-detail** ref for that part only.
2. Tag it in `refs`: `{ "path": "…", "shows": "…", "kind": "part_detail", "part": "<parts[].id>" }`.
3. Keep at least one **hero** ref (`kind: "hero"` or an unmarked full-SKU packshot).
4. **Unify before generate:** every keyframe prompt that uses a part-detail ref must also pass the hero product ref (and the approved composition keyframe when fixing one part on an existing still). The model may change **only** the named `part`; body height, proportions, colors/finish, logo policy, and scene framing stay locked to the hero / approved frame.
5. Vision QC **fail** if the part fix shortened the body, changed silhouette, or restyled the product from the part crop.

**Trigger lesson (northloop):** a flip-lid crop alone produced a correct lid on a **too-short** bottle — rejected; regen must match the original composition and only swap the lid.

## 2. Prompt hard constraints（硬约束）

From the bible, inject an explicit block into every Seedream keyframe (and i2v) prompt. The template speaks of **structure modes / parts**, not lids:

- Keep parts identical to refs; do not invent, omit, or hybridize listed parts; do not redesign critical geometry.
- Mouth/lid/thread wording belongs only in **per-product** `how` / `forbid` text when that SKU needs it.
- **Third-party brand props:** `constraints` always appends a lock — no third-party logos, wordmarks, packaging, or brand-identifiable devices (Apple MacBook / iPhone / logo, Nike swoosh, Starbucks cup mark, Amazon smile, Google/Microsoft hardware logos) unless the advertised SKU is that brand or the user explicitly approved showing it. Generic unbranded props only (plain silver laptop with no logo or chin text, blank phone bezel, plain mug). Same ban in VO, captions, end-cards, and finish overlays that would name the mark.

Script helper: `python3 scripts/product_qc.py constraints path/to/bible.json`. **Enforced:** `pipeline.py` appends this block to every shot + keyframe prompt when `product_bible` is set (do not rely on the agent remembering).

## 3. Pre-flight checklist gate（提交前闸门）

For product-ad pipelines:

- Shot list should set `"kind": "product-ad"` and `"product_bible": "product-bible.json"` (path relative to the shot list).
- `pipeline.py validate|plan|run` **refuses** when kind is `product-ad` (or `--require-product-bible`) and the bible file is missing / fails schema.
- Agent workflow: **category → subtype → parts → forbid** with the user → validate → plan → approve spend → run.

## 4. Post-keyframe vision check（生成后视觉核对）

After each Seedream keyframe, before i2v:

1. Call a **cheap multimodal chat** model on PowerTokens (`POST /v1/chat/completions`) with: bible JSON summary + approved ref image(s) + the new keyframe.
2. Ask for **structured JSON only**:
   `{ "pass": bool, "failures": ["..."], "structure_mode_seen": "...", "rubric_answers": {...}, "notes": "..." }`
   Rubric ids: `structure_matches_refs`, `no_hybrid_or_invented_parts`, `colors_finish_ok`, `logo_policy_ok`, `proportions_silhouette_ok`.
3. Fail if structure is a hybrid not listed in `parts`, or any `forbid` is violated.
   Fail `logo_policy_ok` if the still shows a third-party mark or brand-identifiable device (MacBook, iPhone, Apple logo, Nike swoosh, Starbucks cup mark, Amazon smile, Google/Microsoft hardware logos), or if logos violate `immutable.logos`. Generic unbranded props are OK. Do not ship — regenerate once or stop for a human. The same gate applies to clips and finish overlays before delivery.
4. On **fail**: regenerate **once** with corrected negatives from `failures`, then re-check; if still fail → **stop for human**.
5. On **pass**: mark keyframe `qc: pass` in state and continue.

Legacy verdict field `lid_mode_seen` is accepted and mapped to `structure_mode_seen`.

### Which chat model id?

Confirm live ids with `python3 scripts/pt_models.py --filter glm` / `--filter MiniMax-M` (do **not** promote deepseek-v4-* or `kling-video-o1*`).

| Prefer | Model id | Notes |
|---|---|---|
| Default QC pick | `MiniMax-M3` | Listed on PT; use for short rubric JSON if multimodal is enabled on your key |
| Alt | `glm-5.2` / `glm-5.1` / `glm-5-turbo` | GLM family on PT; pick the cheapest that accepts image inputs on your account |

**Unverified here:** whether every listing accepts `image_url` parts. If the chosen model rejects images, fall back to human approve (P2) and still keep P0/P1 text constraints.

Helper: `python3 scripts/product_qc.py vision-prompt bible.json --keyframe out.png --ref product.jpg`.

## 5. Optional human approve gate（人工过英雄帧）

For shots tagged `"hero": true` or the first packshot keyframe: after vision pass (or instead of it), pause and show the still to the user. Only then submit i2v.

## 6. Shot-to-shot consistency（镜间一致）

- Reuse the **same** `ref_images` / bible refs on every product-visible keyframe.
- Prefer i2v from the **QC-passed** keyframe rather than t2v.
- After all keyframes: compare structure modes / part states across frames; flag if one frame invents a part not in `parts`.
- Optional: pass previous approved keyframe as an extra ref for later shots (identity lock).

## 7. Eval fixtures（评测夹具）

Golden bibles under `tools/examples/product-bible.*.json` + offline tests for schema / constraints / verdict parsing (no paid API). Thermos is one category fixture among others.

## Agent one-pager

1. Identify **category** → **subtype** with the user.  
2. Decompose **parts** BOM (`id` / `role` / `how` / `states?`).  
3. Write **forbid** from part risks, including `no third-party logos, wordmarks, or brand-identifiable devices (MacBook, iPhone, etc.) unless approved`; fill colors, logos, proportions, refs.
   If a part is unclear on the hero packshot, find a **part-detail** ref → tag `kind`/`part` → **unify onto the hero** before spend (body/proportions/scene locked; only that part changes).  
4. `product_qc.py validate-bible` → OK.  
5. Append `constraints` into every keyframe prompt.  
6. `pipeline validate` (bible gate) → `plan` → user approves $ → `run`.  
7. After each keyframe: vision check → one retry or human stop.  
8. Hero frames: human OK → i2v.  
9. Deliver only QC-passed clips.

See skill `powertokens-product-qc` and section in `powertokens-product-ad`.

## Pipeline wiring (v0.3)

`pipeline.py run` now executes vision QC after Seedream keyframes when a product bible is present (default on for `kind: product-ad`):

- One regenerate with augmented negatives on fail; second fail → shot `failed`, no i2v.
- Vision API / multimodal unavailable → **fail-closed** for product-ad unless `--skip-vision-qc`.
- `"hero": true` → write `hero_pending.json`, pause i2v until `approve-hero` or `--auto-approve-hero`.

Live multimodal smoke against MiniMax-M3 / GLM is **not** required for offline CI; confirm separately before relying on auto-pass.
