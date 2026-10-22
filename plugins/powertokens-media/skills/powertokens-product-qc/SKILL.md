---
name: powertokens-product-qc
description: Product-consistency QC for PowerTokens product ads — generic product bible (category → subtype → parts BOM), prompt hard constraints, pipeline pre-flight bible gate, post-keyframe vision rubric (MiniMax-M3 or glm-5.x via chat), optional human approve before i2v. Third-party brand props fail logo_policy_ok (MacBook, logos, other brand-identifiable devices) unless that brand is the SKU or the user approved it. Use for any physical SKU (bottle, bag, sneaker, device, cosmetics, …), product consistency, product bible, 产品质检, 产品一致性, or lock sheet — not thermos-only.
license: MIT
metadata:
  author: PowerTokens
  version: "0.3.3"
---

# Product consistency QC

Scripts: `scripts/product_qc.py` (+ `pipeline.py` bible gate). Full playbook: repo `docs/product-consistency-qc.md`
(also summarized in `references/qc-pipeline.md`).

Examples (different category trees):

- `examples/product-bible.thermos.json` — drinkware / dual-lid thermos
- `examples/product-bible.sneaker.json` — footwear / lace-up running shoe
- `examples/product-bible.bag.json` — bag / top-zip tote

## When to use

Any product-ad where the real SKU has fixed **structure/parts** (closures, soles, zippers, ports, pumps, straps, bezels, logos). Seedream often invents hybrids — catch them before i2v burns budget.

## Credentials

`python3 scripts/pt_login.py status` before any vision call or other spend. If not ok: the user creates a key at https://powertokens.ai/api-keys?utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills and sets `POWERTOKENS_API_KEY`. Browser sign-in (`pt_login.py login`) is not enabled yet. Never ask for the key in chat.

**Key just verified** (`ok: true`, or HTTP 200 on a live check such as `python3 scripts/pt_models.py`), including a re-check after a new key: **ask a yes/no to continue. Do not stop at a status dump.** Do not explain HTTP 200 unless they ask. Do not say only that they can continue.

- A plan or estimate was already shown: restate the **model** and **est. cost**, ask whether to continue that generation, and wait for an explicit yes before a vision call, `run`, or any other spend. A yes from before the key wall does not replace this question.
- No plan yet: ask whether to proceed with **the product bible (category → subtype → parts)**. That yes only starts the unpaid step. Vision QC spends — confirm again before that call.
- Ask in the user's language. If they already said yes to this question for this plan, do not ask again. Canonical wording: repo `docs/auth-after-verify.md`.

## Agent workflow (required order)

Do **not** jump to lid-specific fields. Always:

1. **Category（商品大类）** — e.g. drinkware, footwear, bag, beauty, consumer_electronics.
2. **Subtype（具体分型）** — e.g. dual-lid thermos, lace-up running shoe, top-zip tote.
3. **Parts BOM（组成拆解）** — decompose into `immutable.parts`: `{id, role, how, states?}` for body, openings, closures, hardware, labels, accessories, etc.
4. **Forbid / finish** — write `forbid` from part risks; then colors, logos, proportions, 1–5 refs (hero + optional part-detail). Always include this line in `forbid` (props around the SKU, not a legal note): `no third-party logos, wordmarks, or brand-identifiable devices (MacBook, iPhone, etc.) unless approved`. `constraints` repeats it on every Seedream / i2v prompt.
5. **Part-detail refs → unify** — if a part is unclear on the hero packshot, find a part-detail image, tag `kind: part_detail` + `part: <id>`, then **unify onto the hero product** (body/proportions/scene stay; only that part changes). Never regenerate from the part crop alone.
6. **Validate**:

```bash
python3 scripts/product_qc.py validate-bible path/to/product-bible.json
```

7. **Constraints** — append to every keyframe / i2v prompt (do not skip):

```bash
python3 scripts/product_qc.py constraints path/to/product-bible.json
```

8. **Shot list** — set `"kind": "product-ad"` and `"product_bible": "product-bible.json"`. Then:

```bash
python3 scripts/pipeline.py validate shots.json
python3 scripts/pipeline.py plan shots.json
# user approves → run --approve-estimate …
```

Validate/plan/run **refuse** if kind is product-ad and the bible is missing or invalid (`--require-product-bible` forces the gate for other kinds).

9. **After each Seedream keyframe** — build the vision chat body (cheap multimodal; default model candidate `MiniMax-M3`, alts `glm-5.2` / `glm-5.1` / `glm-5-turbo` — confirm with `pt_models.py` and that image inputs work):

```bash
python3 scripts/product_qc.py vision-prompt bible.json --keyframe outputs/.../kf_s01.png --ref product.jpg
```

Send that body to `POST /v1/chat/completions`. Parse:

```bash
python3 scripts/product_qc.py parse-verdict '{"pass":false,"failures":["hybrid part"]}'
```

On fail: regenerate **that keyframe only** (one retry) with corrected negatives from `failures`, then re-check. Do not start i2v for siblings that already passed. If the retry still fails, stop in the keyframe phase: `pipeline.py run` reports the shot and why (structure, third-party logo, hybrid part, rubric). Failed stills are not sent to video. Vision API down fails closed unless `--skip-vision-qc`.

`logo_policy_ok` is **no** when a still shows a third-party logo, wordmark, packaging, or brand-identifiable device (Apple MacBook / iPhone / logo, Nike swoosh, Starbucks cup mark, Amazon smile, Google/Microsoft hardware logos), unless the advertised SKU is that brand or the user explicitly approved it. Generic unbranded props pass (plain silver laptop with no logo or chin text, blank phone bezel, plain mug). A fail here is the same gate as any other rubric fail: regenerate that keyframe only, or ask — do not ship. Apply the same check to clips and finish overlays before delivery.

10. **Then one i2v batch** — only after every required keyframe is `qc: pass`, `run --parallel` submits video together. Human review of the full still strip is off by default; `"hero": true` still uses `approve-hero`. Reuse the same bible refs; compare structure modes / part states across keyframes before assembly.

Avoid `kling-video-o1*`. Never promote deepseek-v4-* chat/image ids. Do not invent product claims. Vision support for chat model ids is **not fully verified** in this repo — if images are rejected, keep bible + constraints + human approve.

## Related

- `powertokens-product-ad` — production workflow (includes QC section)
- `powertokens-pipeline` — estimate / run / resume
