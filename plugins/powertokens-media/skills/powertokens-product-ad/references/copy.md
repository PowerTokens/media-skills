# Copy brief (hooks, captions, VO)

Captions and VO are **authored claims**, not ASR. Burn-in look is separate from **what the words say**.

**Caption style policy:** default to A (`tiktok`: white + yellow word pop, ≤3 words / ≤16 chars EN). Do **not** treat A as locked — if the user picks another look, or the line is Chinese, switch (`pill` / `caps-punch` / `zh`, 中文默认可走 `zh` 2–4 字). Only ask when the brief is ambiguous; otherwise use the default and mention it in the plan.

## Default path: product URL → claim sheet → confirm → assets

When the user pastes a product link (Amazon, Shopify, brand PDP, etc.):

1. **Fetch** the page. Use a browser tool if the HTML is empty/JS-rendered; otherwise HTTP fetch is fine.
2. **Extract only what is on the page** into `claims.json` (`examples/claim-sheet.json`):
   - `product`: name, brand, price (if shown), category/subtype guess, hero image URLs
   - `claims[]`: each benefit/spec with `source_quote` (verbatim or tight paraphrase), `source_url`, `confidence`
   - Put rankings, “#1”, awards, review counts, and competitor digs in `rejected_or_skipped` unless the user explicitly owns them
3. **Show** `python3 scripts/claim_sheet.py table claims.json` (or the same table in chat). Ask which claims to keep.
4. **Approve** with `claim_sheet.py approve … --ids …` (or mark in JSON). Status must become usable (`approved` claims only feed script/captions).
5. **Then** write hook / captions / VO / storyboard **only** from approved rows → keyframes → video.

No URL? Fall back to user brief + packshot, still using the same claim-sheet file and confirm gate.

If fetch fails (login wall, geo block, empty page): tell the user, ask for paste of title + bullets + 1 packshot — do not guess the PDP.

## Where selling points come from (required)

Only use claims from a **claim sheet** built before the storyboard:

| Source (priority) | Examples | Rule |
|---|---|---|
| User brief | name, 1–3 benefits, audience, CTA, price | Primary |
| Product URL / PDP (fetched) | title, bullets, specs, printed hold-time | Extract with quote + URL; user must approve before use |
| Packaging / spec sheet user provided | capacity, hold-time, materials, warranty | Quote or paraphrase; keep numbers exact |
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

1. Build claim sheet from URL and/or sources above (ask if thin); run `claim_sheet.py validate` + show table; wait for approve.
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
