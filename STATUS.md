# Status

Project: eia_data_visualizations
Process: ~/.claude/d4tp-process/PROCESS.md

## Current

Post: oil-draw-update
Step: done
Since: 2026-10-16

## Steps

| Step | What | Confirmed | Notes |
|---|---|---|---|
| 1  | Exploration and analysis | 2026-10-15 | Own and independent tie-outs pass |
| 2a | Draft with brackets resolved | 2026-10-16 | Claude drafted at Eric's instruction; diesel GIF added |
| 2b | Eric's edit, Claude's look-over | 2026-10-16 | Brackets resolved (gasoline section and GIF, intro link, no closing); edits 1-5 accepted; gasoline tie-out passed |
| 2c | Slice markup | 2026-10-16 | No fences needed; 19 slices, 3 images, divider once |
| 2d | Hero 1680x1080 + alt text | 2026-10-16 | Own render (scripts/hero.py), latest week outlined; alt 430 characters |
| 2e | SEO | 2026-10-16 | Meta title 57, description 150, 7 keywords; Common questions, four entries |
| 2f | Pushed to Prismic (draft) | 2026-10-16 | Draft atH3hRIAACoAnOPg, Migration Release; updated once after Eric's diesel sentence |
| 2g | Mailchimp teaser | 2026-10-16 | Eric's subject and call to action; email chart is the crude seasonality view |

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
- 2026-10-16 2d redone at Eric's request: hero is now its own render (scripts/hero.py), modeled on the SNAP_Locations series heroes: no axes or fine print, earlier weeks dimmed, the October 9 bar bright and outlined, lockup (Oil Update / 8.6 MILLION BARRELS / of commercial crude drawn in one week, the most since the war began / legend) above the bars, all inside the 0.18-0.82 square-crop band. Padded-chart hero source removed. The in-post crude chart also outlines the October 9 bar (Eric's suggestion). hero_alt rewritten (430 characters).
- 2026-10-16 Eric confirmed 2d. Step 2e opened. Eric gave no target searches; Claude chose them.
- 2026-10-16 2e: meta_title 57, description 150, 7 keywords; schema Article, section Data 4 Thought. Common questions section proposed to Eric, not applied.
- 2026-10-16 Eric accepted the Common questions section and confirmed 2e. Step 2f opened.
- 2026-10-16 2f: dry run clean (46 blocks, 29 slices, 3 images + hero, FAQPage with 4 questions), then pushed. Prismic draft atH3hRIAACoAnOPg, uid oil-draw-update, in the Migration Release; tags and author empty. No read token, so the push could not be verified from this side.
- 2026-10-16 After the push, Eric replaced the diesel follow-up sentence (heading into winter, heating oil). Same structure (46 blocks, 29 slices); 2b-2f re-run in place and the same Prismic draft updated.
- 2026-10-16 Eric confirmed 2f. Step 2g opened: EMAIL.md drafted from the post text only; hero exported as images/oil-draw-update-hero-email.jpg (1680 wide, 63KB); email chart is images/01-weekly-crude-draws.png. Waiting for Eric to approve or reject.
- 2026-10-16 Email: GIF sentence added at Eric's request. Each GIF draws in 18.0 s (diesel) and 17.4 s (gasoline) before a 5 s hold; diesel 1982-2026 is 45 years, gasoline 1990-2026 is 37 years.
- 2026-10-16 Email chart changed at Eric's request: a static render of the seasonality tool set to crude oil incl. SPR (scripts/animate_seasonality.py total --static -> images/email-crude-seasonality.png), not in the post. Alt checked: 2026 inside the band weeks 9-16 only, 698.6 in week 41, lower only in 1982 (614.0); 1983 was 699.2.
- 2026-10-16 Eric asked why gasoline starts in 1990. Confirmed in the API and EIA's spreadsheets: all weekly U.S. gasoline series start January 5, 1990 (blending components alone from 1983). Recorded in DATASETS.md.
- 2026-10-16 Eric confirmed 2g. Post oil-draw-update is complete through 2g. Not done: social posts (not yet asked for).
