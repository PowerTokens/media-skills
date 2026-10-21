# QC pipeline (short)

See also the full doc at repo root: `docs/product-consistency-qc.md`.

**P0** Product bible + prompt hard constraints.  
**P1** Pipeline refuses product-ad without bible; post-keyframe vision JSON rubric.  
**P2** Human approve hero keyframes; shot-to-shot lid compare.  
**P3** Eval fixture `examples/product-bible.thermos.json`.

Default vision chat candidate: `MiniMax-M3`. Alts: `glm-5.2`, `glm-5.1`, `glm-5-turbo`. Confirm live ids and multimodal support before spending.
