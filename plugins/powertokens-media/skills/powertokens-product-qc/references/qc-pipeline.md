# QC pipeline (short)

See also the full doc at repo root: `docs/product-consistency-qc.md`.

**Thinking chain:** category（大类）→ subtype（分型）→ `immutable.parts` BOM（组成）→ forbid / colors / logos / proportions / refs.

**P0** Product bible + prompt hard constraints (structure modes / parts — any SKU).  
**P1** Pipeline refuses product-ad without bible; post-keyframe vision JSON rubric.  
**P2** Human approve hero keyframes; shot-to-shot structure compare.  
**P3** Eval fixtures: `examples/product-bible.thermos.json`, `.sneaker.json`, `.bag.json`.

Rubric: `structure_matches_refs`, `no_hybrid_or_invented_parts`, `colors_finish_ok`, `logo_policy_ok`, `proportions_silhouette_ok`. Verdict field: `structure_mode_seen`.

Default vision chat candidate: `MiniMax-M3`. Alts: `glm-5.2`, `glm-5.1`, `glm-5-turbo`. Confirm live ids and multimodal support before spending.

**Part-detail refs:** find the separate part image when needed, then **unify onto the hero product** — body/proportions/scene stay locked; only the named BOM part changes. Never regenerate from a part-only crop alone.
