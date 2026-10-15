# Status

Project: eia_data_visualizations
Process: ~/.claude/d4tp-process/PROCESS.md

## Current

Post: oil-draw-update (working slug, Eric to confirm at 2a)
Step: 1
Since: 2026-10-15

## Steps

| Step | What | Confirmed | Notes |
|---|---|---|---|
| 1  | Exploration and analysis | | |
| 2a | Draft with brackets resolved | | |
| 2b | Eric's edit, Claude's look-over | | |
| 2c | Slice markup | | |
| 2d | Hero 1680x1080 + alt text | | |
| 2e | SEO | | |
| 2f | Pushed to Prismic (draft) | | |
| 2g | Mailchimp teaser | | |

## Stale

None.

## Log

- 2026-10-15 Step 1 opened. Quick Data 4 Thought on the EIA report released today (week ending October 9, 2026): one chart of weekly crude draws since the war began, split commercial and SPR, plus a diesel update and links to earlier energy-crisis posts (Eric to send the links).
- 2026-10-15 Eric's claim checked: this week's total crude draw (8.56 million barrels) is not the largest since the war; it is 11th of 32 war weeks, largest total draw since July 24. It is the largest commercial crude draw since the war began (largest since February 13, before the war). SPR unchanged this week. War start February 28, 2026, as in SPR_explainer and Sulfur. Eric: the SPR pause is explained in the SPR_explainer project, and the reserve will likely draw again after the round 4 bid round completes.
- 2026-10-15 Built scripts/weekly_draws.py (EIA API, live) -> data/weekly_draws.csv, data/weekly_draws_numbers.json, posts/oil-draw-update/images/01-weekly-crude-draws.png. House style copied from Sulfur (scripts/plot_style.py).
- 2026-10-15 Own tie-out passes. Independent tie-out (fresh agent, own API pull plus EIA history spreadsheets, 2,298 weeks per series, zero differences): every number and every bar on the chart matched. Applied its points: x-axis months in AP style; DATASETS.md wording on the total identity (holds every week since 1982), revisions, the +1 SPR quirk, and the 1982-83 gaps. Could not check: whether weekly values are ever revised (no vintage history).
