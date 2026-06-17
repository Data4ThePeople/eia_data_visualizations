# U.S. Petroleum Inventories — Weekly Seasonality

Exploratory analysis of weekly U.S. petroleum stock data from the Energy Information Administration (EIA), with interactive seasonality charts published via [Data 4 The People](https://www.data4thepeople.com).

## Data

Four EIA weekly ending-stocks series, all in thousand barrels:

| File | Series | Description | Start |
|------|--------|-------------|-------|
| `WCRSTUS1w.xls` | WCRSTUS1 | Crude Oil | Aug 1982 |
| `WGTSTUS1w.xls` | WGTSTUS1 | Total Gasoline | Jan 1990 |
| `WDISTUS1w.xls` | WDISTUS1 | Distillate Fuel Oil (Diesel) | Aug 1982 |
| `WCSSTUS1w.xls` | WCSSTUS1 | Crude Oil in Strategic Petroleum Reserve (SPR) | Aug 1982 |

Source files are in `data/`. Week number is computed as `(day-of-year − 1) ÷ 7 + 1`, capped at 52.

## Notebook

`eia_exploration.ipynb` loads and processes all four series into a single `stocks` DataFrame, then generates the interactive HTML visualizations.

**Dependencies:** `pandas`, `matplotlib`, `numpy`, `plotly`, `xlrd`

## Visualizations

Three versioned HTML files, each opening directly in a browser (Plotly CDN, no server needed):

| File | Description |
|------|-------------|
| `petroleum_seasonality_v1.html` | Baseline — Plotly-native layout with decade color scheme |
| `petroleum_seasonality_v2.html` | D4TP design system — custom HTML chrome, native `<select>`, credit bar |
| `petroleum_seasonality_v3.html` | Adds decade toggle pills to filter which decades are shown |

All versions show one line per year (1982–present) plotted by week of year (1–52). The current year is drawn in bold red; prior years are color-coded by decade (gray → green → blue → amber → purple, light-to-dark within each decade). A product dropdown switches between Crude Oil, Total Gasoline, Distillate (Diesel), and Strategic Reserve (SPR).
