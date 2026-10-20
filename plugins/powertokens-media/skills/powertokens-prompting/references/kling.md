# Kling v3

Strengths: high resolution (1080p pro, 4K), clean product motion, first/last frame.

Patterns:
- Direct, declarative prompts; one subject, one move. ≤ 2,500 characters.
- Image-to-video: first frame via `--image`, optional `--last-frame` for a controlled end pose.
- Negative prompt exists in the API (≤ 2,500 chars) but PT docs recommend phrasing negatives inside
  the positive prompt ("the label stays readable and unchanged"). Not exposed by these scripts.
- No seed: expect variation between takes; budget 2 takes for hero shots.

Not wired in this pack yet: `multi_shot` (≤ 6 shots), reference elements (≤ 3), voice ids.
Avoid `kling-video-o1*` model ids in this pack.
