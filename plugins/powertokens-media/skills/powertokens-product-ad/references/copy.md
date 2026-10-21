# Copy brief (hooks, captions, VO)

Captions and VO are **authored claims**, not ASR. Style (TikTok kinetic / yellow pop) is separate from **what the words say**.

## Where selling points come from (required)

Only use claims from a **claim sheet** built before the storyboard:

| Source (priority) | Examples | Rule |
|---|---|---|
| User brief | name, 1–3 benefits, audience, CTA, price | Primary |
| Product page / packaging / spec sheet user provided | capacity, hold-time, materials, warranty | Quote or paraphrase; keep numbers exact |
| Visible on the packshot | logo wordmark, printed claim on label | OK if readable in refs |
| Assistant invention | fake hours, awards, “#1”, reviews, competitor digs | **Forbidden** |

If the brief has mood but no concrete benefit → **stop and ask** for 1–3 true selling points. Do not fill gaps with lifestyle poetry.

After drafting the claim sheet, show the user a table: `claim | source | used in (hook/caption/VO/end-card)` and get a yes before `plan` / spend.

## Hook / caption / VO jobs

| Beat | Job | Bad (reject) | Better (if claim exists) |
|---|---|---|---|
| Hook ≤2s | Specific tension or pattern break tied to a **verified** benefit | “First light.” “Morning vibes.” | “6 a.m. Still hot.” (only if hold-time is approved) |
| Benefit caption | Name the mechanism or proof in 1–3 words / short phrase | “Premium feel.” “Adventure ready.” | “12 hours hot.” “No lukewarm sip.” |
| Proof | Show the claim happening on camera; words match the visual | Vague lifestyle line over a pretty shot | Same number/benefit as VO while the demo plays |
| CTA | Clear next step; price only if user-supplied | “Shop the vibe.” | “Link below.” / user CTA |

Captions must **match VO meaning** (same claim, can be shorter). Kinetic style = shorten; do not change the claim.

## Hard reject list (rewrite before lock)

Reject a line if **any** is true:

1. **Mood-only** — time-of-day / weather / scenery with no product benefit (`First light.`, `Golden hour.`, `On the trail.` alone).
2. **Generic category praise** — could fit any bottle/brand (`Built for early starts.` with no distinct proof; `Stay hydrated.`; `Premium outdoor.`).
3. **Unsourced number or superlative** — hours, %, “hottest”, “#1”, awards, certifications, fake reviews.
4. **Mismatch** — caption promises a demo the shot does not show, or disagrees with VO / end-card.
5. **Interchangeable** — swap brand name and the line still works for a competitor with no edit.

## Write loop (before shot list lock)

1. Build claim sheet from sources above (ask if thin).
2. Draft 2–3 hooks that each encode **one** claim; pick one + keep others for A/B (`powertokens-social-variants`).
3. One caption per shot = compressed claim or curiosity gap, not a scene title.
4. VO: 30–40 words / 15s; every sentence maps to a claim-sheet row.
5. Run claim lint; then self-check against the reject list; show user the table.

## Northloop anti-pattern → grounded rewrite

Given approved claims only: *insulated bottle keeps coffee hot ~12 hours; outdoor / early use; brand North Loop*.

| Beat | Reject (atmospheric) | Prefer (claim-tied) |
|---|---|---|
| s01 | First light. | 6 a.m. Still hot. |
| s02 | Still hot. | Pour it. Still hot. |
| s03 | 12 hours out. | 12 hours. Still hot. |
| s04 | Built for early starts. | North Loop. Still hot. |

If the user has **not** approved “12 hours” / “still hot”, ask — do not keep those numbers from a prior demo file.
