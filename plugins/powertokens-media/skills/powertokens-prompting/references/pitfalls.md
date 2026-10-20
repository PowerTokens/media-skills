# Failure → fix

| Symptom | Likely cause | Fix |
|---|---|---|
| Face/product changes between shots | description drift | identical description text every shot, reference images, Seedream keyframes |
| Actions blend or morph | too many actions | one action per shot or timeline beats |
| Product label garbled | model redrew the label | i2v from real packshot, "label unchanged", shorter move, close-up less |
| Hands/fingers wrong | complex hand action | simpler grip, hands partly out of frame, cut away sooner |
| Image cropped in i2v | ratio mismatch | generate keyframe at target ratio |
| Static, boring motion | no camera move named | add one move + one subject action |
| Lip-sync off | long lines | shorter quoted lines, one speaker per shot, or VO over b-roll |
| Text on video wrong | models are bad at text | add captions in assembly, not in the prompt |
| `INSUFFICIENT_CREDITS` | balance | stop, tell user, do not retry |
| Timed out | slow queue | `video.py resume TASK_ID` — never resubmit |

Pre-flight checklist before paid runs:
- [ ] model chosen via model-routing, ratio matches platform
- [ ] each shot: one action, one camera move, consistent character text
- [ ] dialogue in quotes and short; or `--no-audio` + separate VO
- [ ] estimate shown and approved by the user
