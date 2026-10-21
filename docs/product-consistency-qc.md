# Product consistency QC（产品一致性质检）

Clear English with Chinese labels. For product ads (e.g. thermos / bottle SKUs) where Seedream keyframes invent wrong lids, threads, pour spouts, or proportions.

**Trigger case:** northloop-ad — real thermos has **two opening modes** (screw-off lid **and** plastic flip/hinge pour lid). A keyframe wrongly put a plastic lid opening on the threaded mouth. Refs alone were not enough; the model “helped” by inventing a hybrid that does not exist.

## Priority order (do these first → last)

| P | Mechanism | Cost | When |
|---|---|---|---|
| **P0** | **Product bible / lock sheet** before any paid gen | Free | Always for product-ad |
| **P0** | **Prompt hard constraints** from the bible (forbid wrong mechanisms) | Free | Every keyframe + i2v prompt |
| **P1** | **Pre-flight gate** in `pipeline plan/run`: refuse if bible missing | Free | `kind: product-ad` or `--require-product-bible` |
| **P1** | **Post-keyframe vision check** (cheap chat+vision via PT) vs bible + refs | Low (1 chat call / keyframe) | After each Seedream keyframe |
| **P2** | **Human approve** hero / packshot frames before i2v | Free (time) | Optional; default on for hero shots |
| **P2** | **Shot-to-shot lock**: same refs + compare lids across keyframes | Free–low | Multi-shot ads |
| **P3** | **Eval fixtures** (golden bible + yes/no rubric for thermos-like SKUs) | Free | CI / offline |

## 1. Product bible / lock sheet（产品圣经）

Create **before** storyboard spend. Store as JSON next to the shot list (see `tools/examples/product-bible.thermos.json` and schema in `product_qc.py`).

Immutable attributes to list:

- **Opening / lid mechanism** — enumerate *all* real modes (e.g. `screw_lid`, `flip_hinge_pour`). State what must **never** be mixed (e.g. “do not put a plastic pour spout on the metal screw threads”).
- **Colors / finish** — body, lid, gasket, cup (matte black, gloss, etc.).
- **Logos / marks** — present or absent; exact placement if present; “no invented logos”.
- **Proportions** — silhouette notes (tall slim, wide mouth, cup-lid height ratio).
- **Approved refs** — 1–3 photos: closed hero, lid open (each real mode), optional label close-up.

Chinese quick labels: 开盖方式、禁止混用、颜色材质、比例、批准参考图.

## 2. Prompt hard constraints（硬约束）

From the bible, inject an explicit block into every Seedream keyframe (and i2v) prompt, e.g.:

- Keep lid mechanism **exactly** as in reference photos.
- If showing open: only the mode described for that shot (`screw_lid` **or** `flip_hinge_pour`), never a hybrid.
- Negative: do not invent a plastic pour spout on the screw threads; do not redesign the mouth; do not add a spout, straw, or button not in refs.

Script helper: `python3 scripts/product_qc.py constraints path/to/bible.json`.

## 3. Pre-flight checklist gate（提交前闸门）

For product-ad pipelines:

- Shot list should set `"kind": "product-ad"` and `"product_bible": "product-bible.json"` (path relative to the shot list).
- `pipeline.py validate|plan|run` **refuses** when kind is `product-ad` (or `--require-product-bible`) and the bible file is missing / fails schema.
- Agent workflow: fill bible with the user → validate → plan → approve spend → run.

## 4. Post-keyframe vision check（生成后视觉核对）

After each Seedream keyframe, before i2v:

1. Call a **cheap multimodal chat** model on PowerTokens (`POST /v1/chat/completions`) with: bible JSON summary + approved ref image(s) + the new keyframe.
2. Ask for **structured JSON only**: `{ "pass": bool, "failures": ["..."], "lid_mode_seen": "...", "notes": "..." }` against a yes/no rubric (mechanism match, no hybrid lid, color/finish OK, logo policy OK, proportions OK).
3. On **fail**: regenerate **once** with corrected negatives from `failures`, then re-check; if still fail → **stop for human** (do not burn more credits).
4. On **pass**: mark keyframe `qc: pass` in state and continue.

### Which chat model id?

Confirm live ids with `python3 scripts/pt_models.py --filter glm` / `--filter MiniMax-M` (do **not** promote deepseek-v4-* or `kling-video-o1*`).

Documented candidates from PT model pages / listings (verify vision support before relying on them):

| Prefer | Model id | Notes |
|---|---|---|
| Default QC pick | `MiniMax-M3` | Listed on PT; use for short rubric JSON if multimodal is enabled on your key |
| Alt | `glm-5.2` / `glm-5.1` / `glm-5-turbo` | GLM family on PT; pick the cheapest that accepts image inputs on your account |

**Unverified here:** whether every listing accepts `image_url` parts. If the chosen model rejects images, fall back to human approve (P2) and still keep P0/P1 text constraints. Mark price as “not stored in this repo”.

Helper: `python3 scripts/product_qc.py vision-prompt bible.json --keyframe out.png --ref product.jpg` (prints messages; `--check` dry-parses a sample verdict without calling the API).

## 5. Optional human approve gate（人工过英雄帧）

For shots tagged `"hero": true` or the first packshot keyframe: after vision pass (or instead of it), pause and show the still to the user. Only then submit i2v. Free; catches mechanism errors vision models miss.

## 6. Shot-to-shot consistency（镜间一致）

- Reuse the **same** `ref_images` / bible refs on every product-visible keyframe.
- Prefer i2v from the **QC-passed** keyframe rather than t2v.
- After all keyframes: `product_qc.py compare` — same rubric across frames; flag if one frame shows screw-open and another invents flip-on-threads.
- Optional: pass previous approved keyframe as an extra ref for later shots (identity lock).

## 7. Eval fixtures（评测夹具）

Keep a tiny golden bible for thermos-like SKUs under `tools/examples/product-bible.thermos.json` + offline tests that only validate schema / constraint text / verdict parsing (no paid API).

## Agent one-pager

1. Write / load product bible with user.  
2. `product_qc.py validate-bible` → OK.  
3. Append `constraints` into every keyframe prompt.  
4. `pipeline validate` (bible gate) → `plan` → user approves $ → `run`.  
5. After each keyframe: vision check → one retry or human stop.  
6. Hero frames: human OK → i2v.  
7. Deliver only QC-passed clips.

See skill `powertokens-product-qc` and section in `powertokens-product-ad`.
