# Status

Project: eia_data_visualizations
Process: ~/.claude/d4tp-process/PROCESS.md

## Current

Post: oil-draw-update
Step: 2c
Since: 2026-10-16

## Steps

| Step | What | Confirmed | Notes |
|---|---|---|---|
| 1  | Exploration and analysis | 2026-10-15 | Own and independent tie-outs pass |
| 2a | Draft with brackets resolved | 2026-10-16 | Claude drafted at Eric's instruction; diesel GIF added |
| 2b | Eric's edit, Claude's look-over | 2026-10-16 | Brackets resolved (gasoline section and GIF, intro link, no closing); edits 1-5 accepted; gasoline tie-out passed |
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
- 2026-10-15 Eric sent nine earlier energy-crisis links and confirmed Step 1 and the slug oil-draw-update. Step 2a opened. At Eric's instruction ("yes go ahead and draft it") Claude wrote the whole draft: crude update with the chart, diesel update, a reference list of the nine posts, a bracket for Eric's closing, and About the data. Publish date set to October 16 for Eric to confirm. Share figures (56% of the May 15 draw, 85% of the drop since the war from the SPR) and the diesel level at the August 23 post added to scripts/weekly_draws.py.
- 2026-10-15 Step 2a: at Eric's request, an animated GIF of the diesel seasonality chart added to the diesel section (scripts/animate_seasonality.py -> images/02-diesel-seasonality.gif, 124 frames, 23 seconds, 0.44 MB). Same look, decade colors and average/IQR method as petroleum_seasonality_v2_viz.html; years before 2000 take one frame each, 2000s and 2010s two, 2020s four, then 2026 one week per frame at 240 ms, holding the final frame 5 seconds. The label on the 2026 line shows only real weekly values. Alt text checked against the data: 2026 is below the interquartile band from week 21 on, and below every past year in week 41 (lowest past value 106.2 by week index).
- 2026-10-16 Eric confirmed 2a. Step 2b opened: Eric edits POST.md, then Claude looks it over.
- 2026-10-16 Step 2b look-over. Brackets resolved at Eric's instruction: intro-page link (welcome-to-data4thepeople, from Eric); a gasoline section with its own animated GIF (images/03-gasoline-seasonality.gif); no closing, bracket removed. Gasoline figures added to scripts/weekly_draws.py; fetch() changed to one series per request after a five-series pull repeated rows across pages; all earlier numbers unchanged. Legend now lists only decades with data. Look-over edits to Eric's prose proposed in chat as a numbered list.
- 2026-10-16 Eric accepted look-over edits 1 to 5 (lowercase the, comma for hyphen, past few months, had all known, see through, here is).
- 2026-10-16 Independent tie-out of the gasoline section: all figures supported. Claude's own sentence changed from "well above past years" to "well above the usual range" (3 earlier years were higher in week 1).
- 2026-10-16 Eric confirmed 2b. Step 2c opened.
- 2026-10-16 2c: defaults only, no fences needed (no embeds; divider already above About the data). Importer convert-only: 37 blocks, 19 slices, 3 images, divider once. Hero warnings expected until 2d.
- 2026-10-16 2d: hero from the crude draws chart (Eric's choice). scripts/weekly_draws.py now also renders the chart on a 9.4x6.0 in canvas (images/oil-draw-update-hero-source.png) so type stays legible, padded by hero pad to images/oil-draw-update-hero-1680x1080.png. Legend and plot top now placed in inches, which also re-spaced the in-post chart (layout only, same data). hero_alt 440 characters. hero check and importer: no warnings.
