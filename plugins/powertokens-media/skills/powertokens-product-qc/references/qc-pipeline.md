# QC pipeline (short)

See also the full doc at repo root: `docs/product-consistency-qc.md`.

**Thinking chain:** category（大类）→ subtype（分型）→ `immutable.parts` BOM（组成）→ forbid / colors / logos / proportions / refs.

**P0** Product bible + prompt hard constraints (structure modes / parts — any SKU).  
**P1** Pipeline refuses product-ad without bible; post-keyframe vision JSON rubric; **keyframe batch gate** — no i2v until every keyframe is `qc: pass`, then one `--parallel` video batch. A fail retries that still only; a second fail stops in the keyframe phase with shot + why (structure, third-party logo, …). Vision API down fails closed unless `--skip-vision-qc`.  
**P2** Human approve `hero: true` keyframes only (full still strip is optional / off by default); shot-to-shot structure compare.  
**P3** Eval fixtures: `examples/product-bible.thermos.json`, `.sneaker.json`, `.bag.json`.

Rubric: `structure_matches_refs`, `no_hybrid_or_invented_parts`, `colors_finish_ok`, `logo_policy_ok`, `proportions_silhouette_ok`. Verdict field: `structure_mode_seen`.

**`logo_policy_ok`:** fail if the frame shows a third-party logo, wordmark, packaging, or brand-identifiable device (MacBook, iPhone, Apple logo, Nike swoosh, Starbucks cup mark, Amazon smile, Google/Microsoft hardware logos) unless the advertised SKU is that brand or the user explicitly approved it. Also fail when marks violate `immutable.logos`. Generic unbranded props pass (plain silver laptop with no logo or chin text, blank phone bezel, plain mug). Do not ship a fail — regenerate or ask. When drafting `forbid`, always include: `no third-party logos, wordmarks, or brand-identifiable devices (MacBook, iPhone, etc.) unless approved`.

Default vision chat candidate: `MiniMax-M3`. Alts: `glm-5.2`, `glm-5.1`, `glm-5-turbo`. Confirm live ids and multimodal support before spending.

**Part-detail refs:** find the separate part image when needed, then **unify onto the hero product** — body/proportions/scene stay locked; only the named BOM part changes. Never regenerate from a part-only crop alone.
