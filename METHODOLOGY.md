# U.S. Petroleum Inventories — Methodology

## Purpose

These visualizations answer one question at a glance: **is the current level of U.S. petroleum inventories normal, or not?**

Inventories — how much crude, gasoline, and diesel the country has in storage — are one of the clearest early signals of strain in the energy system. Plenty of cushion means the market can absorb a shock; stocks near the bottom of their range mean less room for error, and price starts doing the work inventory no longer can.

The catch is that "normal" is seasonal. Stocks naturally rise and fall every year — gasoline builds ahead of summer driving, distillate ahead of winter heating — so a raw number tells you little on its own. The same level can be alarming in one month and ordinary in another. To know if today is unusual, you have to compare it to the same point in prior years.

That's what this tool family does, in three views built on the same data:

1. **The seasonality chart** — every year as a line on a common week-1-to-52 axis, with the current year in bold red against the historical backdrop.
2. **The replay animation** — the same chart, drawn one year at a time in chronological order, so you can watch the envelope build decade by decade.
3. **The dot strip** — a single week at a time: every year becomes one dot, so you can see exactly where the current year ranks against the same week in every prior year.

Inventories tell you how much cushion the system has. The [3-2-1 crack spread](https://www.data4thepeople.com/p/crack-spread-chart/) tells you whether cheaper crude is actually reaching the pump — the two are worth reading together.

## What this page is

Every chart we publish should be something you can check, question, and rebuild yourself. This page documents exactly how we built these tools — where the data comes from, every transformation we applied, and the judgment calls we made along the way. Nothing here is proprietary. If you wanted to reproduce them from scratch, this page should get you there.

## The data source

All inventory figures come from the U.S. Energy Information Administration (EIA), the statistical arm of the U.S. Department of Energy. The data is free, public, and updated weekly. We use four weekly ending-stocks series:

| Series ID | Product | History |
|-----------|---------|---------|
| WCRSTUS1 | Crude oil (incl. SPR) | 1982–present |
| WGTSTUS1 | Total gasoline | 1990–present |
| WDISTUS1 | Distillate fuel oil / diesel | 1982–present |
| WCSSTUS1 | Strategic Petroleum Reserve (SPR) | 1982–present |

All values are reported in thousands of barrels. We do not alter, smooth, or adjust the underlying figures.

### Live API retrieval

Data is fetched directly from the EIA API on each build — no manual downloads. The endpoint is:

```
https://api.eia.gov/v2/petroleum/stoc/wstk/data/
```

Each series is requested with `frequency=weekly`, sorted oldest-first, up to 5,000 records — sufficient to cover the full history of all four series. The chart always reflects the most recent EIA release; the tradeoff is a network dependency (an internet connection and a valid API key).

## Part 1 — The seasonality chart

### Step 1: Start with what the EIA already gives you

The EIA publishes each series as a single long time series: one continuous line from the 1980s to today. It's accurate and complete, but built to show the long arc, not the current moment. Everything we do from here is reorganization, not new data.

### Step 2: Reshape the timeline into weeks-of-the-year

Instead of plotting time continuously, we split each year into its own track and align them on a common 1-to-52 week axis. For every weekly observation we compute its week-of-year and group readings by calendar year:

```
week = ((day_of_year − 1) ÷ 7) + 1,  capped at 52
```

This keeps a consistent week-to-week position across all years. The result: one line per year, all overlaid on the same axis. This is the core move — we changed the shape, not the substance.

### Step 3: Handle data quirks

Real weekly data isn't perfectly clean, so two small rules apply:

* When the day-of-year math places two readings in the same week bucket, we average them.
* When a week bucket has no reading, we leave a gap rather than inventing a value.

These choices affect at most a handful of points per year and don't change the shape of any line.

### Step 4: Color by decade

Prior years are grouped by decade, each decade a distinct color, with lines within a decade fading from a lighter shade (oldest year) to a darker shade (most recent). The current year is a bold red line drawn on top. The palette: 1980s teal, 1990s green, 2000s blue, 2010s orange, 2020s purple, current year red. This preserves the historical "envelope" reading while showing whether the pattern shifted between decades, not just between years.

### Step 5: Interactive controls

* **Product pills** — the four products are selectable as pill buttons (one active at a time): Crude Oil (incl. SPR), Total Gasoline, Distillate (Diesel), Strategic Reserve (SPR).
* **Decade toggle pills** — each decade is a clickable pill; toggling one off hides its year-lines and dims the legend swatch. All decades are active by default.
* **Hover** — hovering any line shows the year, week number, and stock level in thousands of barrels.

### Step 6: The average and its normal band

On top of the year lines we draw a dashed black line showing the average level for each week, computed across the years in the currently selected decades — always excluding the current year, so this year is never compared against itself. Toggle decades and the average recomputes; an "Average" button switches the overlay off entirely.

Two details worth knowing:

* **The average fills small interior gaps that the lines leave open.** The plotted year lines keep their gaps (step 3), but a per-week average changes membership when a year skips a week, and jumps for no seasonal reason. The earliest EIA weekly data has a handful of skipped weeks (1983 misses weeks 16, 18, and 21; 1982 misses 36–38). Only inside the average calculation, we fill a year's interior missing weeks by straight-line interpolation between neighboring readings, and a note beneath the chart says which years contain filled-in weeks. Gaps at the edge of a year's coverage are never filled — 1982's data begins at week 34, so 1982 joins the average from week 34 onward.
* **The shaded band is the interquartile range, and it only appears with all decades selected.** When every decade is on, the grey band spans the 25th to 75th percentile of the same years the average uses, week by week — the middle half of history. (Quartiles are computed by linear interpolation on sorted values, the same convention our other charts use.) With only a decade or two selected we hide it deliberately: a band from ten strongly-trending years mostly measures that era's trend, not seasonal spread.

## Part 2 — The replay animation (new)

The replay now lives on its own page rather than inside the main chart. It draws each year's line in chronological order — 1982 first, the current year last — so the historical envelope builds in front of you and you can watch the seasonal pattern (and its drift across decades) emerge.

* **Play** starts the replay; the pace is calibrated so the full history takes about 30 seconds at normal speed, and **2× / 3×** buttons speed it up.
* The y-axis is pinned for the duration of a replay, so the scale doesn't jump as lines accumulate; switching products resets the axes fresh.
* Product and decade pills work as on the main chart — animating a subset of decades replays only those years.

## Part 3 — The dot strip: where the current year stands (new)

The seasonality chart shows the whole year's shape; the dot strip asks a sharper question about a single moment: **for this week of the year, where does the current year rank against every prior year?**

* **One week at a time.** Pick a week (1–52) with the slider. For that week, every year of history becomes one dot on a horizontal axis of stock level — the same week in every year, so the comparison is seasonally like-for-like by construction.
* **Beeswarm layout.** Dots that would overlap stack vertically off the center line, so every year stays individually visible and hoverable. Vertical position carries no meaning; only the horizontal axis does.
* **Colors match the seasonality chart.** Prior years are colored by decade with the same palette; the current year is a larger, ringed red dot drawn on top. The axis is labeled in millions of barrels for readability; hover tooltips carry the exact reported values.
* **The baseline: median, mean, and IQR of all prior years.** A solid line marks the prior-year median at that week, a dashed line the mean, and a shaded band the interquartile range (25th–75th percentile, linear-interpolation convention). The current year is always excluded from these statistics. Unlike the seasonality chart's average, the dot strip's statistics use only actual reports at the selected week — no interpolated values; a year that has no report in that week simply sits that week out. Within-year duplicates in a week bucket are averaged, as on the seasonality chart.
* **Decade highlighter.** Decade chips act like a highlighter, not a filter: highlighting a decade brings its dots forward and dims the rest — including the median/mean/IQR overlay, which grays out to signal that the baseline still reflects *all* prior years, not just the highlighted ones. Nothing is removed from the chart and no statistic is recomputed.
* **Tooltips.** Hovering a dot shows its year, the week-ending report date, the exact level in thousands of barrels, and how far it sits from the prior-year median.
* **Headline.** A title above the chart states the selected week and the current year's level, updating live as you move through weeks.
* **Play through the year.** A play button animates week by week from week 1 to the latest week the current year has reached, with 2× and 3× speed toggles — watching the red dot drift through the pack shows how the current year's position has evolved. The week selector is capped at the current year's latest reported week, so every selectable week has a current-year dot.

Per-product animated GIF exports of this play-through are also produced for embedding where interactivity isn't available.

## Updating

We refresh the charts weekly. The process is mechanical: run the build scripts — they pull the latest data from the EIA API — and republish the output. One script builds the seasonality chart and the replay animation page together; a second builds the dot strip. The current-year highlight, week ranges, and all statistics update automatically; no manual editing is required.

## Honest notes and limitations

We'd rather tell you the edges of this than have you find them.

* **Week-of-year is a simplification.** The (day-of-year ÷ 7) method gives each week a stable position across years, but EIA's actual report dates are Fridays and don't align perfectly week-to-week. An alternate convention (ISO weeks, or EIA's own numbering) would shift a few points by one position. It doesn't change any line's shape or the story it tells.
* **Weekly figures are EIA estimates and get revised.** EIA's weekly numbers are timely estimates, periodically revised and later reconciled against more complete monthly data. We use the weekly series for currency and accept that recent points may move slightly.
* **History lengths differ by product.** Gasoline begins in 1990; crude, distillate, and SPR go back to 1982. Gasoline simply has fewer historical lines and dots behind it — not an error, just the limit of the public record.
* **The band is a description, not a forecast.** On both charts, the interquartile band shows where the middle half of past years actually sat. It makes no distributional assumptions, but it is not a confidence interval or a prediction: years are not independent draws, because inventories trend across decades. Read it as "the usual range," nothing stronger.
* **The seasonality average leans on a few interpolated inputs.** Six week-slots from 1982–83 are filled by straight-line interpolation before averaging (see Part 1, step 6), and a note beneath the chart says so. The dot strip takes the opposite convention — actual reports only — which means its per-week statistics can draw on slightly different year counts from week to week.
* **Decade coloring is a grouping convenience, not a claim.** Decade boundaries are calendar-based and don't correspond to any market regime or structural break. Draw your own conclusions about whether decade-level patterns are meaningful.
* **The palette is not fully colorblind-safe.** The 2020s purple and 2000s blue are hard to distinguish under deuteranopia, and the current-year red sits close to the 2010s orange. We keep the palette for consistency across our charts and mitigate it where it matters most: the current year is always the larger, ringed, topmost mark, and the dot strip's decade highlighter lets any decade be isolated without relying on hue.
* **We did not invent the data.** Every number is the EIA's. Our contribution is the reorganization — the seasonal framing, the decade coloring, the summary statistics, and the interactivity — not the underlying figures.

## Reproduce it yourself

If you want to rebuild these charts, you need only the public EIA series listed above and any tool that can reshape a spreadsheet by week-of-year. The transformations are the steps above; the statistics are ordinary medians, means, and quartiles. If you do it and get something different from us, we want to know — tell us, and we'll look.
