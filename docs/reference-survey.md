# Reference survey (2026-10-20)

Stars as seen on GitHub on 2026-10-20 (UTC+8). We read structure and approach only; no text was
copied. Repos without a declared license (`none`) were not quoted at all.

| Repo | Stars | License | What we took |
|---|---:|---|---|
| [anthropics/skills](https://github.com/anthropics/skills) (skill-creator) | 182k | none in API | Progressive disclosure (metadata → SKILL.md < 500 lines → `references/`); "pushy", trigger-rich descriptions that say *when* to use; trigger evals (should / should not trigger) → our `evals/` |
| [openai/plugins](https://github.com/openai/plugins) + [Codex plugin docs](https://developers.openai.com/codex/plugins/build) | 7.5k | none in API | Portable `plugin.json` with `extensions.com.openai`, repo marketplace `.agents/plugins/marketplace.json` |
| [openai/skills](https://github.com/openai/skills) (deprecated) | 28k | none in API | Same SKILL.md format; installer installs single skill folders → each skill folder ships its own scripts |
| [fal-ai-community/skills](https://github.com/fal-ai-community/skills) | 253 | none in API | Split into model-routing / per-family prompting / production skills (commercial, ugc, storytelling, cinematography); "load reference X when you need Y" pointers |
| [elevenlabs/skills](https://github.com/elevenlabs/skills) | 497 | MIT | Per-skill `evals/` with `trigger_eval.json`; separate setup/onboarding skill for keys |
| [elevenlabs/elevenlabs-mcp](https://github.com/elevenlabs/elevenlabs-mcp) | 1.5k | MIT | Warn about cost before paid tool calls |
| [heygen-com/skills](https://github.com/heygen-com/skills) | 506 | MIT | Very explicit descriptions with "Use when… / NOT for…"; blocking readiness gates before submit; references for prompt craft, troubleshooting, motion vocabulary; MCP-or-key dual auth path |
| [MiniMax-AI/skills](https://github.com/MiniMax-AI/skills) | 13.7k | MIT | Vendor packs ship as a plugin with many skills; bilingual README |
| [MiniMax-AI/MiniMax-MCP](https://github.com/MiniMax-AI/MiniMax-MCP) | 1.6k | MIT | Media tools return file paths; async video task → poll pattern |
| [runwayml/runway-api-mcp-server](https://github.com/runwayml/runway-api-mcp-server) | 23 | MIT | Thin official MCP; confirms value of workflow skills on top of raw tools |
| [remotion-dev/skills](https://github.com/remotion-dev/skills) | 5.4k | none in API | Separate captions / render skills → our assemble step with SRT + burn-in |
| [scenario-labs/skills](https://github.com/scenario-labs/skills) | 1.1k | MIT | Model-catalog style routing tables |
| [Comfy-Org/comfy-skills](https://github.com/Comfy-Org/comfy-skills) | 232 | MIT | Workflow-as-JSON → our JSON shot list |
| [black-forest-labs/skills](https://github.com/black-forest-labs/skills) | 134 | MIT | Model-family prompting guides from the model vendor |
| [creatify-ai/ai-ad-prompt-guide](https://github.com/creatify-ai/ai-ad-prompt-guide) | 43 | MIT | Ad-specific prompt structure (hook first, product fidelity) |
| [beshuaxian/higgsfield-seedance2-jineng](https://github.com/beshuaxian/higgsfield-seedance2-jineng) | 978 | none | (structure only) many narrow scenario skills around Seedance 2.0 — shows demand for Seedance-specific prompting |
| [AKCodez/higgsfield-claude-skills](https://github.com/AKCodez/higgsfield-claude-skills) | 445 | none | (structure only) one skill per production task (UGC, product, cinematic) |
| [machina-exm/film-studio-skills](https://github.com/machina-exm/film-studio-skills) | 154 | none | (structure only) pipeline stages as separate skills: script → storyboard → shots → edit |
| [yuvalsuede/agent-media-skill](https://github.com/yuvalsuede/agent-media-skill) | 42 | Apache-2.0 | CLI-backed skill; agent calls a script, not raw HTTP |
| [Cripacx/mediagen](https://github.com/Cripacx/mediagen) | 52 | MIT | Single skill + scripts; outputs to a local folder |
| [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | 77k | none | Submission target; categories used there (media/creative) |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | 36k | MIT | Submission target (cross-agent skills) |
| [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | 15k | none | Submission target |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | 56k | other | Submission target |
| [affaan-m/ECC](https://github.com/affaan-m/ECC) (everything-claude-code) | 285k | — | Large general harness; no media-generation skill worth adopting found in a quick scan |

Not found / not checked: an official Replicate, Higgsfield or Kling skills repo (searched names
returned 404 or were rate-limited); Codex curated skills beyond openai/skills.

## Patterns applied in this repo
1. **Progressive disclosure** — short SKILL.md bodies with explicit "load `references/x.md` when…".
2. **Trigger-rich descriptions** — what + when + typical phrasings, < 1024 chars; trigger evals in `evals/`.
3. **Routing → prompting → production layering** (fal) with PT-only models and cited limits.
4. **Worked examples** — `examples/*.json` shot lists per scenario; routing decision examples.
5. **Cost gate** — `pipeline.py plan` + `run --approve-estimate` must match; unknown prices listed, not guessed.
6. **Failure handling** — stable `error_type`s, resume by task id, pitfalls table.
7. **Checklists** — delivery/QA checklists per production skill (HeyGen-style gates).
8. **Self-contained skill folders** — every skill installable alone (Codex installer, manual copy).
