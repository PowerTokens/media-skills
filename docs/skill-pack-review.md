# PowerTokens media-skills — full skill pack review

Date: 2026-10-21 (Asia/Shanghai). Repo: `/workspace/media-skills` (local). No remote push. No paid API calls in this audit.

Scope: all **13** skills under `plugins/powertokens-media/skills/`, plus shared tools (`tools/shared/`) and docs.

Prior commits in this thread:
- `9f8e6df` — product QC category → subtype → parts BOM (generic, not thermos-only)
- `ed0e74a` — Seedance i2v omit `ratio`; auto-inject PRODUCT LOCK; keyframe bible refs
- *(this commit)* — package-wide SKILL/docs sync + this review

---

## 1. Inventory (ordered)

| # | Skill | One-line purpose | Maturity |
|---|---|---|---|
| 1 | `powertokens-video` | Single-clip t2v / i2v / resume via API | **Thin wrapper** + light routing hints |
| 2 | `powertokens-image` | Seedream t2i / ref edit | **Thin wrapper** |
| 3 | `powertokens-speech` | MiniMax TTS / VO | **Thin wrapper** |
| 4 | `powertokens-model-routing` | Which model / limits / list prices | **Know-how** (docs) |
| 5 | `powertokens-prompting` | Shot formula, camera, pitfalls | **Know-how** (docs) |
| 6 | `powertokens-pipeline` | Shot list → keyframes → clips → VO → assemble | **Workflow + code gates** |
| 7 | `powertokens-product-ad` | Product photo → vertical ad | **Workflow** (uses pipeline + QC) |
| 8 | `powertokens-product-qc` | Product bible + constraints + vision rubric | **Workflow + schema gates** |
| 9 | `powertokens-ugc-ad` | Creator / talking-head ads | **Workflow** (docs QC) |
| 10 | `powertokens-short-drama` | Multi-shot drama + character refs | **Workflow** (docs QC) |
| 11 | `powertokens-social-variants` | Ratio / hook A/B / cut-downs | **Light workflow** |
| 12 | `powertokens-bilingual-voiceover` | EN/ZH VO + captions on same visuals | **Workflow** |
| 13 | `powertokens-travel-poster` | Photo → 3:4 「第二世界」collage | **Workflow** (method + checklist) |

Shared but **not** a skill folder: `tools/shared/captions.py`, `finish.py` (now synced into assembly skills).

---

## 2. Per-skill detail

### 2.1 `powertokens-video` — v0.2.1

- **Path:** `plugins/powertokens-media/skills/powertokens-video/SKILL.md`
- **Changed this audit:** Seedance first-frame i2v docs (omit `--ratio`); link to product-qc; examples updated. Underlying `video.py` omits `ratio` when first/last frame present.
- **Top risks:** Agents still pass wrong models; product identity not gated at CLI; default 16:9 easy to misuse for TikTok.
- **Gates:** Model whitelist in `MODELS`; duration/res/ratio checks in `build()`. No spend approval on single `generate` (only `--dry-run` advice).
- **Remaining gaps:** No runtime ban list beyond whitelist; no product bible at CLI.

### 2.2 `powertokens-image` — v0.2.0

- **Path:** `plugins/powertokens-media/skills/powertokens-image/SKILL.md`
- **Changed:** unchanged (shared `video.py` sync only if any).
- **Top risks:** Invented logos/text on packshots; wrong aspect for downstream i2v; JPEG sniff rename helps but agents may still ask for `.png`.
- **Gates:** Model id list; pixel-size guidance in docs only.
- **Remaining gaps:** No schema for “product lock” on raw `image.py` calls; travel-poster / product-ad must carry discipline.

### 2.3 `powertokens-speech` — v0.2.0

- **Path:** `plugins/powertokens-media/skills/powertokens-speech/SKILL.md`
- **Changed:** unchanged.
- **Top risks:** Timing mismatch vs video; invented claims in script text; CJK burn needs font (handled in bilingual skill).
- **Gates:** Char limit note in docs; billing per character not estimated in pipeline.
- **Remaining gaps:** No claim-lint; VO cost always `not_estimated`.

### 2.4 `powertokens-model-routing` — v0.2.1

- **Path:** `plugins/powertokens-media/skills/powertokens-model-routing/SKILL.md`
- **Changed:** Seedance i2v ratio rule; explicit ban on promoting undocumented DeepSeek-v4 chat ids / Kling O1 video ids. `references/video-models.md` updated.
- **Top risks:** Stale list prices; agents use account-only ids not in pack.
- **Gates:** Docs + offline test that banned ids are not promoted in repo text. Runtime = `MODELS` whitelist only.
- **Remaining gaps:** No live price fetch; Kling reference elements still unwired.

### 2.5 `powertokens-prompting` — v0.2.1

- **Path:** `plugins/powertokens-media/skills/powertokens-prompting/SKILL.md`
- **Changed:** Identity section (product-qc + character consistency); pitfalls already list Seedance 400.
- **Top risks:** Docs-only — agents can skip; “label unchanged” still under-specified without a bible.
- **Gates:** none (pure know-how).
- **Remaining gaps:** No eval that prompts contain PRODUCT LOCK when bible exists (pipeline injects at run time).

### 2.6 `powertokens-pipeline` — v0.2.1

- **Path:** `plugins/powertokens-media/skills/powertokens-pipeline/SKILL.md`
- **Changed:** Documented bible auto-inject, Seedance ratio omit, optional `finish.py` / `captions.py`; schema product-ad section; scripts synced.
- **Top risks:** Vision QC / hero human gate still agent-only; assemble caption `MarginV=60` weaker than finish safe-zone; parallel shots can race state (lock exists).
- **Gates (enforced):** `validate` model limits + file exists; product-ad bible required; `run` needs matching `--approve-estimate`; resume by task id; Seedance omits ratio on i2v; PRODUCT LOCK appended when bible set; bible refs merged into **Seedream keyframes only**.
- **Remaining gaps:** No hard stop for `hero: true`; vision QC not called from `run`; character-bible schema (drama) not validated like product bible.

### 2.7 `powertokens-product-ad` — v0.3.0

- **Path:** `plugins/powertokens-media/skills/powertokens-product-ad/SKILL.md`
- **Changed (thread):** QC section + checklist rewritten for category→subtype→parts; finish/captions now synced into scripts.
- **Top risks:** Example shot list still thermos-themed (OK as fixture); example prompts omit PRODUCT LOCK text (OK — pipeline injects); vision multimodal unverified.
- **Gates:** via pipeline + product_qc.
- **Remaining gaps:** Hero approve + vision retry loop not automated in `run`.

### 2.8 `powertokens-product-qc` — v0.3.0

- **Path:** `plugins/powertokens-media/skills/powertokens-product-qc/SKILL.md`
- **Changed (thread):** Generic parts BOM; thermos/sneaker/bag examples; legacy `lid_modes` normalized.
- **Top risks:** Vision chat models may reject `image_url`; agents may skip vision step.
- **Gates:** `validate-bible`, `check-shotlist`, constraints emitter, verdict parser (offline).
- **Remaining gaps:** No end-to-end paid vision fixture; no auto-retry inside pipeline.

### 2.9 `powertokens-ugc-ad` — v0.2.1

- **Path:** `plugins/powertokens-media/skills/powertokens-ugc-ad/SKILL.md`
- **Changed:** Checklist + pointer to product-qc when product is on camera; finish/captions synced.
- **Top risks:** Fake testimonial / real-person likeness; lip-sync quality unverified; product bottle hybrid same as product-ad if bible skipped.
- **Gates:** pipeline validate only (characters description required if used).
- **Remaining gaps:** No `kind: ugc-ad` bible/persona gate; no automated persona face compare.

### 2.10 `powertokens-short-drama` — v0.2.1

- **Path:** `plugins/powertokens-media/skills/powertokens-short-drama/SKILL.md`
- **Changed:** Checklist tightened (identical descriptions, Seedance ratio, no invented claims); finish/captions synced.
- **Top risks:** Character drift across episodes; wardrobe paraphrasing; Wan first_frame vs ref conflict.
- **Gates:** `characters.*.description` required when referenced; refs file existence.
- **Remaining gaps:** No structured character-bible JSON schema / gate like product_qc; no shot-to-shot face QC.

### 2.11 `powertokens-social-variants` — v0.2.1

- **Path:** `plugins/powertokens-media/skills/powertokens-social-variants/SKILL.md`
- **Changed:** Generic naming (`<project>-9x16-hookA`); Seedance ratio note; finish/captions synced.
- **Top risks:** Crop cuts off product/face; regenerating without new keyframes.
- **Gates:** reformat free; paid regen uses pipeline approval.
- **Remaining gaps:** No auto safe-zone check after crop.

### 2.12 `powertokens-bilingual-voiceover` — v0.2.1

- **Path:** `plugins/powertokens-media/skills/powertokens-bilingual-voiceover/SKILL.md`
- **Changed:** “Don’t invent claims when adapting”; finish/captions synced. Example still `thermos-ad-zh` (fixture name only).
- **Top risks:** Timing overflow; literal translation; missing CJK font on burn.
- **Gates:** same as pipeline for VO-only rerun (`approve-estimate 0`).
- **Remaining gaps:** No duration lint EN vs ZH lines.

### 2.13 `powertokens-travel-poster` — v0.2.0

- **Path:** `plugins/powertokens-media/skills/powertokens-travel-poster/SKILL.md`
- **Changed:** unchanged this pass (method already forbids logos/watermarks/ad look).
- **Top risks:** Stock tear-paper gag; inventing landmarks not in photo; upper half recolored.
- **Gates:** docs checklist only; single `image.py` call after user yes.
- **Remaining gaps:** No automated visual QC vs method avoid-list.

---

## 3. Cross-cutting risks (multi-skill)

| Priority | Area | Risk | Status |
|---|---|---|---|
| P0 | Seedance i2v `ratio` | HTTP 400 TaskTypeConstraint (seen on northloop-ad) | **Enforced** in `video.build` (omit ratio with first/last frame); docs updated |
| P0 | Product identity | Invented/hybrid parts (thermos lid case) | **Partly enforced**: bible gate + auto PRODUCT LOCK; vision/hero still docs/agent |
| P1 | Constraints injection | Agents forget PRODUCT LOCK | **Enforced** when `product_bible` set (`compose_prompt` + `gen_keyframe`) |
| P1 | Character identity | Face/outfit drift (drama/UGC) | **Docs-only** (+ description required); no schema/QC like product bible |
| P1 | Captions covering subject | Assemble MarginV=60 vs finish ~60% height | finish/captions now **synced**; assemble defaults still weaker |
| P1 | Claims / compliance | Invented prices, awards, fake reviews | Docs/checklists; finish end-card can render user-supplied price — no lint |
| P2 | Forbidden model ids | undocumented DeepSeek-v4 / Kling O1 ids | Whitelist + repo text test; not a separate reject list |
| P2 | Wan first_frame ⊕ refs | Mutual exclusion | Enforced at build/run (refs cleared for Wan+image) |
| P2 | Orphan polish tools | captions/finish not in skills | **Fixed**: synced into pipeline-style skills + pipeline SKILL docs |
| P2 | Thermos-centric examples | Implies drinkware-only | Bibles include sneaker/bag; examples still named thermos (OK as fixtures) |
| P3 | Vision QC unverified | MiniMax-M3 / glm image_url support | Documented; fallback human approve |
| P3 | Price tables stale | List prices 2026-10-05 | Docs say verify on site |

**Seedance ratio code path (exact):** `tools/shared/video.py` → `build()` → `fam == "seedance"` → if media contains `first_frame` or `last_frame`, body has **no** `ratio`; else `ratio` set. Callers: `video.py generate`, `pipeline.run_shot` → `video.build(...)`.

---

## 4. Top 5 package-wide fixes (next, not only product-ad)

1. **Wire post-keyframe vision QC + hero pause into `pipeline.run`** (or a `pipeline qc` subcommand) so product-ad / any bible job cannot i2v without pass/human — today still agent-manual.
2. **Character-bible schema + gate** for `kind: short-drama` / ugc (mirror product_qc: fixed traits, ref paths, forbid wardrobe paraphrase) — biggest non-product identity hole.
3. **Unify caption safe-zone** — make `assemble` use finish-style ~60% height / left-biased margins by default; optional kinetic path documented in every production skill.
4. **Claim lint (offline)** — refuse finish end-card / captions containing award/certification patterns unless `claims_approved: true` on shot list.
5. **Live vision smoke (one cheap call)** — confirm MiniMax-M3 or glm-* accepts `image_url` on a real key; record result in `docs/product-consistency-qc.md`.

---

## 5. Quick fixes done offline in this thread

- Omit Seedance `ratio` on first-frame i2v (`video.py`).
- Auto-inject PRODUCT LOCK + keyframe bible refs (`pipeline.py`).
- Generic product bible parts BOM; multi-category examples.
- Docs: seedance.md, pitfalls, video-models, shotlist-schema, product checklists.
- Sync `captions.py` / `finish.py` into assembly skills; SKILL bumps 0.2.1 where docs changed.
- Package review doc (this file).

Tests: `python3 -m unittest discover tests` (offline). Do not push.

---

## 6. Skill folder names (for parent → user review)

```
powertokens-bilingual-voiceover
powertokens-image
powertokens-model-routing
powertokens-pipeline
powertokens-product-ad
powertokens-product-qc
powertokens-prompting
powertokens-short-drama
powertokens-social-variants
powertokens-speech
powertokens-travel-poster
powertokens-ugc-ad
powertokens-video
```

Review doc path: `docs/skill-pack-review.md`  
Primary SKILL paths: `plugins/powertokens-media/skills/<name>/SKILL.md`
