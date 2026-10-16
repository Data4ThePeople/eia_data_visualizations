# Datasets

## EIA Weekly Petroleum Status Report: weekly ending stocks

- **What it is:** U.S. ending stocks at the end of each week (Friday), thousand barrels. EIA API v2, route `petroleum/stoc/wstk`, frequency weekly.
- **Series used:** WCRSTUS1 crude oil including SPR; WCESTUS1 commercial crude oil (excluding SPR); WCSSTUS1 crude oil in the SPR; WDISTUS1 distillate fuel oil (diesel and heating oil); WGTSTUS1 total motor gasoline (weekly from January 1990).
- **Vintage:** pulled October 15, 2026; latest week ending October 9, 2026. The report came out Thursday, October 15, a day late because of the Columbus Day holiday.
- **Coverage:** weekly from August 20, 1982 for crude (total, commercial, SPR) and distillate. Total gasoline (WGTSTUS1) starts January 5, 1990. Checked October 16, 2026: in the API, every weekly U.S. gasoline series (total, finished motor gasoline, and the total of all crude and products) starts January 5, 1990; only gasoline blending components (WBCSTUS1) go back further, to January 7, 1983. EIA's history spreadsheets for WGTSTUS1 and WGFSTUS1 also start January 5, 1990. We did not find EIA's stated reason for the 1990 start. Monthly gasoline stocks go back further but are a different series.
- **How the numbers are made:** commercial stocks are estimates from EIA's weekly sample of refiners, terminals, pipelines and tank farms; the SPR figure comes from the Department of Energy and is a direct count. WCRSTUS1 equals WCESTUS1 plus WCSSTUS1 as published, in every week since 1982 (checked by the independent tie-out, October 15, 2026).
- **Revisions:** EIA rarely changes weekly numbers after release, though it does sometimes publish resubmissions; the API keeps no vintage history, so we cannot check. Monthly figures in the Petroleum Supply Monthly replace them later with fuller survey data and can differ. A weekly change is the difference of two weekly estimates, so a single week's change carries sampling noise.
- **Units and rounding:** thousand barrels; the post rounds to tenths of a million.
- **Method used here:**
  - Weekly change = this week's stocks minus last week's, for each series.
  - "Since the war began" means weeks ending after February 28, 2026: March 6 through October 9, 32 weeks. The week ending March 6 covers February 28 to March 6.
  - Rank of a draw: 1 + the number of war weeks with a larger draw. Ties do not count as larger.
  - Diesel "same week of the year": for each year, the weekly value whose date is closest to the latest week's day of the year (within three days). The 2021 to 2025 average is the mean of those five values.
- **API paging:** pulling several series in one request, sorted by period, repeats rows across pages once the result runs past two pages (found October 16, 2026, when gasoline was added). `fetch()` now pulls one series per request and fails on any duplicate. Every earlier number was recomputed after the change and none moved.
- **Quirks:** the SPR weekly change is sometimes as small as 1 thousand barrels in weeks with no sales or loans (+1 in the week ending March 6), from DOE's accounting.
- **Gaps:** the 1982-83 history skips weeks (28 days before September 24, 1982; 14 days before April 29, May 13 and June 3, 1983). A week-to-week change across those gaps covers more than one week. No number in this post uses those weeks; any all-history ranking of weekly changes should drop them.
- **License:** U.S. government work, public domain.

## Trace: every number in posts/oil-draw-update/POST.md

All from `scripts/weekly_draws.py` -> `data/weekly_draws_numbers.json`, independently tied out October 15, 2026 (the two share figures and the August diesel level were added after; they are ratios of tied-out figures).

| In the post | Value | Key |
|---|---|---|
| Total crude drop, week ending Oct 9 | 8.6M | total_change |
| All from commercial; largest commercial drop of the war | rank 1 | commercial_rank_since_war |
| Largest total drop, week ending May 15 | 17.8M | largest_total_draw |
| Share of May 15 from SPR | 56% | largest_total_draw_spr_share_pct |
| Rank of last week's total drop | 11th of 32 | total_rank_since_war, war_weeks |
| Largest total drop since | week ending July 24 | last_larger_total_draw |
| First week since March 20 without an SPR draw | | war_weeks_spr_unchanged, spr changes Mar 27 to Oct 2 all negative |
| Drop since war, total and SPR | 156.2M, 132.5M, 85% | cum_change_since_war, cum_spr_share_pct |
| Diesel drop, percent, level | 2.5M, 2.4%, 102.6M | distillate_change, distillate_change_pct, distillate_level |
| Lowest for this week since 1982; next lowest 2022 | 106.1M | distillate_same_week_rank_low, distillate_same_week_next_lowest |
| Below 2021-25 average | 12.2% | distillate_vs_5yr_pct |
| Lower now than at the Aug 23 diesel post | 105.6M (week ending Aug 14) | distillate_at_aug23_post |
| Gasoline rise, percent, level | 3.5M, 1.7%, 208.3M | gasoline_change, gasoline_change_pct, gasoline_level |
| Largest weekly gasoline gain since the war began | rank 1 | gasoline_build_rank_since_war |
| Gasoline below 2021-25 average | 4.4% | gasoline_vs_5yr_pct |
| Earlier years with lower gasoline this week | 15 of 36 | gasoline_same_week_years_lower, gasoline_same_week_years minus 2026 |
| Gasoline GIF alt text: above the band to week 16, inside from week 17 (late April), week 41 just below the average (208.3 vs 209.5) | | checked against avg_band() in scripts/animate_seasonality.py |

The gasoline figures were added October 16, 2026. Independent tie-out the same day (fresh agent, own API pull plus EIA's history spreadsheet, 1,919 weeks, no mismatches): every figure supported. Notes: 15 of 36 is a thin margin (2001 is 77 thousand barrels above 2026); 2026 dips just under the band in week 28 (210.5 against 211.0) and is inside it every other week from 17 to 41; 3 earlier years were higher than 2026 in week 1, so the text says "well above the usual range".
