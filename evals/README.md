# Trigger evals

`<skill>.trigger_eval.json` = queries that should / should not trigger each skill (same shape as
anthropics/skills `skill-creator` and elevenlabs/skills trigger evals). Use them with skill-creator's
description optimizer in Claude Code, or review by hand when editing a `description`.
Not run in CI (needs a model); `tests/` only checks that every skill has an eval file.
