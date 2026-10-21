---
name: powertokens-product-qc
description: Product-consistency QC for PowerTokens product ads — product bible / lock sheet, prompt hard constraints, pipeline pre-flight bible gate, post-keyframe vision rubric (MiniMax-M3 or glm-5.x via chat), optional human approve before i2v. Use when making product ads, fixing wrong lids/spouts/logos, or when the user mentions product consistency, product bible, 产品质检, 产品一致性, or thermos/SKU lock sheet.
license: MIT
metadata:
  author: PowerTokens
  version: "0.2.0"
---

# Product consistency QC

Scripts: `scripts/product_qc.py` (+ `pipeline.py` bible gate). Full playbook: repo `docs/product-consistency-qc.md`
(also summarized in `references/qc-pipeline.md`). Golden thermos-like bible: `examples/product-bible.thermos.json`.

## When to use

Any product-ad where the real SKU has fixed mechanics (lids, threads, pour modes, logos). Seedream often invents hybrids — catch them before i2v burns budget.

## Agent workflow

1. **Bible** — with the user, fill a JSON lock sheet (lid modes, forbid list, colors, logos, proportions, 1–3 refs). Validate:

```bash
python3 scripts/product_qc.py validate-bible path/to/product-bible.json
```

2. **Constraints** — append to every keyframe / i2v prompt (do not skip):

```bash
python3 scripts/product_qc.py constraints path/to/product-bible.json
```

3. **Shot list** — set `"kind": "product-ad"` and `"product_bible": "product-bible.json"`. Then:

```bash
python3 scripts/pipeline.py validate shots.json
python3 scripts/pipeline.py plan shots.json
# user approves → run --approve-estimate …
```

Validate/plan/run **refuse** if kind is product-ad and the bible is missing or invalid (`--require-product-bible` forces the gate for other kinds).

4. **After each Seedream keyframe** — build the vision chat body (cheap multimodal; default model candidate `MiniMax-M3`, alts `glm-5.2` / `glm-5.1` / `glm-5-turbo` — confirm with `pt_models.py` and that image inputs work):

```bash
python3 scripts/product_qc.py vision-prompt bible.json --keyframe outputs/.../kf_s01.png --ref product.jpg
```

Send that body to `POST /v1/chat/completions` (agent or a thin wrapper). Parse:

```bash
python3 scripts/product_qc.py parse-verdict '{"pass":false,"failures":["hybrid lid"]}'
```

On fail: one regenerate with corrected negatives from `failures`, re-check; still fail → stop for human. On pass: optional human OK for hero frames → i2v.

5. **Shot-to-shot** — reuse the same bible refs; compare lid modes across keyframes before assembly.

Avoid `kling-video-o1*`. Never promote deepseek-v4-* chat/image ids. Do not invent product claims. Vision support for chat model ids is **not fully verified** in this repo — if images are rejected, keep bible + constraints + human approve.

## Related

- `powertokens-product-ad` — production workflow (includes QC section)
- `powertokens-pipeline` — estimate / run / resume
