# Datasets

## EIA Weekly Petroleum Status Report: weekly ending stocks

- **What it is:** U.S. ending stocks at the end of each week (Friday), thousand barrels. EIA API v2, route `petroleum/stoc/wstk`, frequency weekly.
- **Series used:** WCRSTUS1 crude oil including SPR; WCESTUS1 commercial crude oil (excluding SPR); WCSSTUS1 crude oil in the SPR; WDISTUS1 distillate fuel oil (diesel and heating oil).
- **Vintage:** pulled October 15, 2026; latest week ending October 9, 2026. The report came out Thursday, October 15, a day late because of the Columbus Day holiday.
- **Coverage:** weekly from August 1982 for all four series.
- **How the numbers are made:** commercial stocks are estimates from EIA's weekly sample of refiners, terminals, pipelines and tank farms; the SPR figure comes from the Department of Energy and is a direct count. WCRSTUS1 equals WCESTUS1 plus WCSSTUS1 as published, in every week since 1982 (checked by the independent tie-out, October 15, 2026).
- **Revisions:** EIA rarely changes weekly numbers after release, though it does sometimes publish resubmissions; the API keeps no vintage history, so we cannot check. Monthly figures in the Petroleum Supply Monthly replace them later with fuller survey data and can differ. A weekly change is the difference of two weekly estimates, so a single week's change carries sampling noise.
- **Units and rounding:** thousand barrels; the post rounds to tenths of a million.
- **Method used here:**
  - Weekly change = this week's stocks minus last week's, for each series.
  - "Since the war began" means weeks ending after February 28, 2026: March 6 through October 9, 32 weeks. The week ending March 6 covers February 28 to March 6.
  - Rank of a draw: 1 + the number of war weeks with a larger draw. Ties do not count as larger.
  - Diesel "same week of the year": for each year, the weekly value whose date is closest to the latest week's day of the year (within three days). The 2021 to 2025 average is the mean of those five values.
- **Quirks:** the SPR weekly change is sometimes as small as 1 thousand barrels in weeks with no sales or loans (+1 in the week ending March 6), from DOE's accounting.
- **Gaps:** the 1982-83 history skips weeks (28 days before September 24, 1982; 14 days before April 29, May 13 and June 3, 1983). A week-to-week change across those gaps covers more than one week. No number in this post uses those weeks; any all-history ranking of weekly changes should drop them.
- **License:** U.S. government work, public domain.
