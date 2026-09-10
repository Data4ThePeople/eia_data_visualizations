# inventory_dot_strip.py
#
# Generates an interactive HTML "dot strip" of U.S. weekly petroleum
# inventory data sourced from the EIA (U.S. Energy Information Administration).
#
# For a selected week of the year, every year (1982-present) is drawn as one
# dot on a horizontal axis, so you can see exactly where the current year
# lands against the full history at the same point in the season. Prior-year
# median / mean / IQR are overlaid, decades can be highlighted from the
# legend, and a play button animates through the weeks of the current year.
#
# To run:  python inventory_dot_strip.py
# Output:  inventory_dot_strip_viz.html  (open in any web browser)
#
# Requirements: pandas, requests, python-dotenv
#   Install with:  pip install pandas requests python-dotenv

import base64
import json
import mimetypes
import os

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
EIA_API_KEY = os.environ["EIA_API_KEY"]

_EIA_API_URL = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"


def fetch_eia(series_id, col_name):
    params = {
        "api_key": EIA_API_KEY,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[series][]": series_id,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": 5000,
    }
    resp = requests.get(_EIA_API_URL, params=params, timeout=30)
    resp.raise_for_status()
    records = resp.json()["response"]["data"]
    df = (
        pd.DataFrame(records)[["period", "value"]]
        .rename(columns={"period": "date", "value": col_name})
    )
    df["date"] = pd.to_datetime(df["date"])
    df[col_name] = pd.to_numeric(df[col_name])
    return df.set_index("date").sort_index()


# ── Fetch each EIA series via API ──────────────────────────────────────────────
crude      = fetch_eia("WCRSTUS1", "crude_oil")
spr        = fetch_eia("WCSSTUS1", "spr")
distillate = fetch_eia("WDISTUS1", "distillate")
gasoline   = fetch_eia("WGTSTUS1", "gasoline")

stocks = crude.join([spr, distillate, gasoline], how="outer")
stocks.index = pd.to_datetime(stocks.index)
stocks = stocks.sort_index()

# Sanity check that the API is returning the most recent data
print(f"Last available week of data: {stocks.index.max():%Y-%m-%d}")


# ── Compute week-of-year and calendar year columns ─────────────────────────────
doy = stocks.index.day_of_year.to_series(index=stocks.index)
stocks["year"] = stocks.index.year
stocks["week"] = ((doy - 1) // 7 + 1).clip(upper=52).astype(int)

CURRENT_YEAR = int(stocks.index.year.max())


# ── Product definitions ────────────────────────────────────────────────────────
PRODUCTS = {
    "crude_oil":  ("Crude Oil (incl. SPR)",   "WCRSTUS1", "1982"),
    "gasoline":   ("Total Gasoline",          "WGTSTUS1", "1990"),
    "distillate": ("Distillate (Diesel)",     "WDISTUS1", "1982"),
    "spr":        ("Strategic Reserve (SPR)", "WCSSTUS1", "1982"),
}


# ── Decade colour palette (mid tones from the seasonality chart) ───────────────
DECADE_MID = {
    1980: "rgba(0,140,175,0.90)",
    1990: "rgba(18,122,42,0.90)",
    2000: "rgba(10,72,172,0.90)",
    2010: "rgba(185,85,5,0.90)",
    2020: "rgba(108,35,162,0.90)",
}
CURRENT_RED = "#c0392b"


# ── Serialize chart data to JSON ───────────────────────────────────────────────
# One record per year per product: parallel arrays of week number, value
# (thousand barrels), and week-ending report date. Two reports that land in
# the same week bucket are averaged (latest date kept), matching the
# duplicate-week handling in the seasonality chart.
chart_data = {}
for col in PRODUCTS:
    s = stocks[["year", "week", col]].dropna(subset=[col]).copy()
    s["date"] = s.index
    g = (
        s.groupby(["year", "week"], as_index=False)
        .agg(value=(col, "mean"), date=("date", "max"))
    )
    rows = []
    for yr, grp in g.groupby("year"):
        grp = grp.sort_values("week")
        rows.append({
            "year":   int(yr),
            "decade": int(yr) // 10 * 10,
            "w":      grp["week"].astype(int).tolist(),
            "v":      [int(round(x)) for x in grp["value"]],
            "d":      grp["date"].dt.strftime("%Y-%m-%d").tolist(),
        })
    chart_data[col] = rows

# Week selection is capped at the latest week with current-year data, so every
# selectable week has a current-year dot and valid header deltas.
latest_weeks = {}
for col, rows in chart_data.items():
    cur = [r for r in rows if r["year"] == CURRENT_YEAR]
    latest_weeks[col] = max(cur[0]["w"]) if cur else 0
    print(f"{col}: {CURRENT_YEAR} data through week {latest_weeks[col]}")

all_decades = sorted({
    row["decade"]
    for series in chart_data.values()
    for row in series
    if row["year"] < CURRENT_YEAR
})

product_labels = {col: label for col, (label, _, _) in PRODUCTS.items()}


def src(sid, sy):
    return (
        f"EIA series {sid} — Weekly U.S. Ending Stocks, {sy}–present, "
        f"thousand barrels. Week = (day-of-year / 7), capped at 52; two reports "
        f"in the same week are averaged. Median, mean, and IQR use prior years "
        f"only (excludes {CURRENT_YEAR}), from actual reports at the selected week."
    )

source_notes = {col: src(sid, sy) for col, (_, sid, sy) in PRODUCTS.items()}


# ── D4TP logo ──────────────────────────────────────────────────────────────────
LOGO_PATH = r"C:\Users\amand\Workspace\D4TP\logos\d4tp-text-dark@2x.png"
_mime = mimetypes.guess_type(LOGO_PATH)[0] or "image/png"
with open(LOGO_PATH, "rb") as _f:
    LOGO_SRC = f"data:{_mime};base64,{base64.b64encode(_f.read()).decode()}"


# ── Build legend + control HTML ────────────────────────────────────────────────
decade_chips_html = ""
for dec in all_decades:
    mid = DECADE_MID[dec]
    decade_chips_html += (
        f'<button class="decade-chip" data-decade="{dec}" data-color="{mid}" '
        f'aria-pressed="false"><span class="chip-dot" '
        f'style="background:{mid}"></span>{dec}s</button>'
    )

product_pills_html = ""
for col, (label, _, _) in PRODUCTS.items():
    on = " on" if col == "crude_oil" else ""
    pressed = "true" if col == "crude_oil" else "false"
    product_pills_html += (
        f'<button class="product-pill{on}" data-product="{col}" '
        f'aria-pressed="{pressed}">{label}</button>'
    )


# ── Output file name ───────────────────────────────────────────────────────────
OUTPUT = "inventory_dot_strip_viz.html"


HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>U.S. Petroleum Inventories - Where {CURRENT_YEAR} Stands</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{
  --bg-primary:    #ffffff; --bg-secondary: #f5f4ef; --bg-tertiary: #efece4;
  --text-primary:  #1a1a1a; --text-secondary: #555550; --text-tertiary: #888880;
  --border: rgba(0,0,0,0.12); --border-strong: rgba(0,0,0,0.25);
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg-primary: #1a1a1a;   --bg-secondary: #232220; --bg-tertiary: #2c2c2a;
    --text-primary: #e8e6df; --text-secondary: #a8a59b; --text-tertiary: #6b6962;
    --border: rgba(255,255,255,0.12); --border-strong: rgba(255,255,255,0.25);
  }}
}}
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{background:var(--bg-primary);overflow-x:hidden;}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",sans-serif;
      color:var(--text-primary);padding:20px;max-width:1100px;margin:0 auto;line-height:1.5;}}
.hdr{{margin-bottom:14px;}}
.hdr h1{{font-size:22px;font-weight:600;margin-bottom:4px;line-height:1.25;}}
.hdr p{{font-size:13px;color:var(--text-secondary);max-width:700px;}}
.ctrls{{
  display:grid;
  grid-template-columns:auto 1fr;
  gap:14px;
  margin-bottom:12px;padding:12px 14px;
  background:var(--bg-secondary);border-radius:10px;
  align-items:end;
}}
.ctrl-grp{{display:flex;flex-direction:column;gap:5px;}}
.ctrl-grp label{{
  font-size:11px;color:var(--text-secondary);
  text-transform:uppercase;letter-spacing:0.04em;font-weight:600;
}}
.product-pills{{display:flex;gap:5px;flex-wrap:wrap;}}
.product-pill{{
  padding:8px 14px;font-size:13px;
  background:var(--bg-primary);color:var(--text-secondary);
  border:0.5px solid var(--border);border-radius:7px;
  cursor:pointer;font-family:inherit;
  transition:background 0.12s,color 0.12s,border-color 0.12s;
  min-height:38px;white-space:nowrap;
}}
.product-pill:hover{{border-color:var(--border-strong);}}
.product-pill.on{{
  background:var(--text-primary);color:var(--bg-primary);
  border-color:var(--text-primary);
}}
.week-ctrl{{display:flex;align-items:center;gap:10px;}}
.week-ctrl input[type=range]{{
  flex:1;min-width:80px;min-height:38px;cursor:pointer;accent-color:{CURRENT_RED};
}}
#play-btn{{
  width:44px;min-height:38px;font-size:15px;line-height:1;
  background:var(--bg-primary);color:var(--text-primary);
  border:0.5px solid var(--border);border-radius:7px;cursor:pointer;font-family:inherit;
  transition:border-color 0.12s;flex-shrink:0;
}}
#play-btn:hover{{border-color:var(--border-strong);}}
.speed-btn{{
  width:36px;min-height:38px;font-size:12px;line-height:1;
  background:var(--bg-primary);color:var(--text-secondary);
  border:0.5px solid var(--border);border-radius:7px;cursor:pointer;font-family:inherit;
  transition:background 0.12s,color 0.12s,border-color 0.12s;flex-shrink:0;
}}
.speed-btn:hover{{border-color:var(--border-strong);}}
.speed-btn.on{{
  background:var(--text-primary);color:var(--bg-primary);
  border-color:var(--text-primary);
}}
.headline{{font-size:19px;font-weight:600;color:var(--text-primary);
  letter-spacing:-0.01em;margin:4px 2px 10px;line-height:1.4;}}
#chart{{width:100%;}}
.legend{{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:2px;
         font-size:12px;color:var(--text-secondary);}}
.legend-item{{display:flex;align-items:center;gap:7px;}}
.leg-dot{{display:inline-block;width:11px;height:11px;border-radius:50%;flex-shrink:0;
  border:1.5px solid var(--bg-primary);box-shadow:0 0 0 0.5px var(--border);}}
.leg-median{{display:inline-block;width:3px;height:14px;border-radius:1px;flex-shrink:0;
  background:var(--text-primary);}}
.leg-mean{{display:inline-block;width:3px;height:14px;flex-shrink:0;
  background-image:repeating-linear-gradient(180deg,var(--text-primary) 0 3px,rgba(0,0,0,0) 3px 5px);}}
.leg-iqr{{display:inline-block;width:18px;height:12px;border-radius:2px;flex-shrink:0;
  background:rgba(128,128,128,0.25);}}
.leg-label{{white-space:nowrap;}}
.chips-row{{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-top:10px;}}
.chips-caption{{font-size:11px;color:var(--text-secondary);text-transform:uppercase;
  letter-spacing:0.04em;font-weight:600;margin-right:4px;}}
.decade-chip{{
  display:inline-flex;align-items:center;gap:6px;
  padding:5px 12px;font-size:12px;border-radius:999px;
  background:var(--bg-primary);color:var(--text-secondary);
  border:0.5px solid var(--border);cursor:pointer;font-family:inherit;
  transition:background 0.12s,color 0.12s,border-color 0.12s;min-height:30px;
}}
.decade-chip:hover{{border-color:var(--border-strong);}}
.decade-chip .chip-dot{{display:inline-block;width:9px;height:9px;border-radius:50%;flex-shrink:0;}}
.decade-chip.on .chip-dot{{background:#fff !important;}}
#clear-hl{{
  background:none;border:none;color:var(--text-secondary);font-size:12px;
  text-decoration:underline;cursor:pointer;font-family:inherit;padding:5px 6px;
}}
.notes{{font-size:11px;color:var(--text-secondary);margin-top:12px;line-height:1.6;
        padding-top:12px;border-top:0.5px solid var(--border);}}
.notes strong{{color:var(--text-primary);font-weight:500;}}
.credit-bar{{display:flex;justify-content:flex-end;align-items:center;
             margin-top:14px;padding-top:12px;border-top:0.5px solid var(--border);}}
@media(max-width:700px){{
  body{{padding:14px;}} .hdr h1{{font-size:18px;}}
  .ctrls{{grid-template-columns:1fr;}}
  .headline{{font-size:16px;}}
}}
</style>
</head>
<body>

<div class="hdr">
  <h1>U.S. Petroleum Inventories &#8212; Where {CURRENT_YEAR} Stands</h1>
  <p>Each dot is one year&#8217;s stocks at the same week of the year, so every
  comparison is seasonally like-for-like. {CURRENT_YEAR} in red; prior years
  colored by decade. Pick a week, or press play to watch {CURRENT_YEAR} unfold.</p>
</div>

<div class="ctrls">
  <div class="ctrl-grp">
    <label>Product</label>
    <div class="product-pills" id="product-pills" role="group" aria-label="Product">
      {product_pills_html}
    </div>
  </div>
  <div class="ctrl-grp">
    <label for="week-slider">Week</label>
    <div class="week-ctrl">
      <button id="play-btn" aria-label="Play through the weeks of {CURRENT_YEAR}">&#9654;</button>
      <button id="speed-2x" class="speed-btn" aria-pressed="false" aria-label="Play at double speed">2x</button>
      <button id="speed-3x" class="speed-btn" aria-pressed="false" aria-label="Play at triple speed">3x</button>
      <input type="range" id="week-slider" min="1" max="52" step="1" value="1"
             aria-label="Week of year">
    </div>
  </div>
</div>

<div class="headline" id="headline"></div>

<div id="chart"></div>

<div class="legend">
  <div class="legend-item"><span class="leg-dot" style="background:{CURRENT_RED}"></span><span class="leg-label">{CURRENT_YEAR}</span></div>
  <div class="legend-item"><span class="leg-median"></span><span class="leg-label">Median (prior years)</span></div>
  <div class="legend-item"><span class="leg-mean"></span><span class="leg-label">Mean</span></div>
  <div class="legend-item"><span class="leg-iqr"></span><span class="leg-label">IQR (25th&#8211;75th)</span></div>
</div>

<div class="chips-row">
  <span class="chips-caption">Highlight decades</span>
  {decade_chips_html}
  <button id="clear-hl" hidden>clear</button>
</div>

<div class="notes">
  <strong>Source:</strong> <span id="source-note">{source_notes['crude_oil']}</span>
</div>

<div class="credit-bar">
  <img src="{LOGO_SRC}" alt="D4TP" style="height:24px;width:auto;opacity:0.85;">
</div>

<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<script>
const CURRENT_YEAR   = {CURRENT_YEAR};
const CHART_DATA     = {json.dumps(chart_data)};
const LATEST_WEEK    = {json.dumps(latest_weeks)};
const SOURCE_NOTES   = {json.dumps(source_notes)};
const PRODUCT_LABELS = {json.dumps(product_labels)};

const RED = '{CURRENT_RED}';
const DECADE_RGB = {{
  1980:[0,140,175], 1990:[18,122,42], 2000:[10,72,172],
  2010:[185,85,5],  2020:[108,35,162],
}};
// The 2000s and 2020s mid tones fall below 3:1 contrast on the dark surface,
// so dark mode swaps in a lighter step from the same decade ramps used by the
// seasonality chart (both clear 3.2:1 on #1a1a1a).
const DECADE_RGB_DARK = Object.assign({{}}, DECADE_RGB,
  {{2000:[48,106,192], 2020:[145,80,188]}});
function decadeRgb(dec) {{
  return (darkMq.matches ? DECADE_RGB_DARK : DECADE_RGB)[dec];
}}

// ── Theme helpers ──────────────────────────────────────────────────────────────
const darkMq   = window.matchMedia('(prefers-color-scheme: dark)');
const reduceMq = window.matchMedia('(prefers-reduced-motion: reduce)');
function inkColor()    {{ return darkMq.matches ? 'rgba(232,230,223,0.95)' : 'rgba(26,26,26,0.95)'; }}
function mutedColor()  {{ return darkMq.matches ? '#a8a59b' : '#555550'; }}
function surfaceColor(){{ return darkMq.matches ? '#1a1a1a' : '#ffffff'; }}
function gridColor()   {{ return darkMq.matches ? 'rgba(255,255,255,0.10)' : 'rgba(210,215,225,0.7)'; }}
function bandColor()   {{ return darkMq.matches ? 'rgba(160,160,160,0.20)' : 'rgba(128,128,128,0.16)'; }}

// ── Formatting helpers ─────────────────────────────────────────────────────────
const MINUS = '\\u2212';
const fmtComma = v => Math.round(v).toLocaleString('en-US');
const fmtMbbl  = v => (v/1000).toLocaleString('en-US',
  {{minimumFractionDigits:1, maximumFractionDigits:1}}) + 'M';
function signed(v, fmt) {{ return (v < 0 ? MINUS : '+') + fmt(Math.abs(v)); }}
function ordinal(n) {{
  const s = ['th','st','nd','rd'], v = n % 100;
  return n + (s[(v-20)%10] || s[v] || s[0]);
}}
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function fmtDate(iso) {{
  const [y,m,d] = iso.split('-').map(Number);
  return MONTHS[m-1] + ' ' + d + ', ' + y;
}}

// ── Per-product index: dots by week, prior-year stats, fixed x range ───────────
// Stats always cover ALL prior years with an actual report at that week —
// decade highlighting never changes them.
function quantile(sorted, p) {{
  const n = sorted.length;
  if (!n) return null;
  const pos = (n-1)*p, lo = Math.floor(pos), frac = pos - lo;
  return lo + 1 < n ? sorted[lo] + (sorted[lo+1]-sorted[lo])*frac : sorted[lo];
}}

const INDEX = {{}};
for (const p in CHART_DATA) {{
  const byWeek = {{}};
  let mn = Infinity, mx = -Infinity;
  CHART_DATA[p].forEach(r => {{
    for (let i = 0; i < r.w.length; i++) {{
      const wk = r.w[i], v = r.v[i];
      mn = Math.min(mn, v); mx = Math.max(mx, v);
      if (!byWeek[wk]) byWeek[wk] = {{ prior: [], cur: null }};
      if (r.year === CURRENT_YEAR) byWeek[wk].cur = {{ value: v, date: r.d[i] }};
      else byWeek[wk].prior.push({{ year: r.year, decade: r.decade, value: v, date: r.d[i] }});
    }}
  }});
  for (const wk in byWeek) {{
    const W = byWeek[wk];
    W.prior.sort((a, b) => a.year - b.year);
    const vals = W.prior.map(o => o.value).sort((a, b) => a - b);
    const n = vals.length;
    W.stats = n ? {{
      n,
      mean:    vals.reduce((a, v) => a + v, 0) / n,
      median:  quantile(vals, 0.5),
      q1:      quantile(vals, 0.25),
      q3:      quantile(vals, 0.75),
      minYear: W.prior[0].year,
      maxYear: W.prior[W.prior.length-1].year,
    }} : null;
    // ascending rank of each prior year's value (1 = lowest)
    W.rank = {{}};
    W.prior.map((o, i) => i)
      .sort((a, b) => W.prior[a].value - W.prior[b].value)
      .forEach((pi, k) => {{ W.rank[W.prior[pi].year] = k + 1; }});
  }}
  const pad = (mx - mn) * 0.04;
  INDEX[p] = {{ byWeek, xrange: [mn - pad, mx + pad] }};
}}

// ── Responsive tiers ───────────────────────────────────────────────────────────
// Breakpoints mirror the CSS @media(max-width:700px) query — keep them in sync.
function tierFor(w) {{ return w < 450 ? 'xs' : w < 700 ? 'sm' : 'lg'; }}

const TIER_CFG = {{
  lg: {{height:280, margin:{{t:16,b:58,l:16,r:16}}, dot:9, curDot:16, nticks:9, titleSize:16, fontSize:14, tickFmt:','}},
  sm: {{height:250, margin:{{t:12,b:50,l:12,r:12}}, dot:8, curDot:14, nticks:6, titleSize:14, fontSize:12, tickFmt:','}},
  xs: {{height:230, margin:{{t:12,b:48,l:8, r:8}},  dot:7, curDot:12, nticks:5, titleSize:13, fontSize:12, tickFmt:','}},
}};

// ── State ──────────────────────────────────────────────────────────────────────
let currentProduct = 'crude_oil';
let currentWeek = LATEST_WEEK[currentProduct];
const highlighted = new Set();
let playing = false, playTimer = null;
let lastTier = tierFor(window.innerWidth);
let speed = 1;                        // 1x, 2x or 3x — set by the speed toggles
const STEP_MS = 650;
function stepMs() {{ return STEP_MS / speed; }}
function transMs() {{
  if (reduceMq.matches) return 0;
  return Math.round(Math.min(450, stepMs() * 0.7));
}}

// ── Beeswarm layout ────────────────────────────────────────────────────────────
// Greedy: walk dots in value order, place each in the row (0, +1, -1, +2, ...)
// whose most recent dot is far enough away horizontally. Rows sit one dot
// apart vertically so cross-row dots can't collide; if every row is crowded
// (heavy clustering), fall back to the least-crowded row and accept a slight
// overlap. Returns y offsets in axis units (y range is [-1.5, 1.5]).
function swarmOffsets(values, x0, x1, plotW, plotH, dotPx) {{
  const pxPerUnit = plotW / (x1 - x0);
  const spacing = dotPx + 2;
  const maxRow = Math.max(1, Math.floor((plotH * 0.3 - dotPx) / spacing));
  const order = [0];
  for (let k = 1; k <= maxRow; k++) order.push(k, -k);
  const lastX = {{}};
  const rows = new Array(values.length);
  values.map((v, i) => [v, i]).sort((a, b) => a[0] - b[0]).forEach(([v, i]) => {{
    const x = (v - x0) * pxPerUnit;
    let chosen = null, fallback = order[0], fallbackGap = -Infinity;
    for (const r of order) {{
      const gap = (r in lastX) ? x - lastX[r] : Infinity;
      if (gap >= spacing) {{ chosen = r; break; }}
      if (gap > fallbackGap) {{ fallbackGap = gap; fallback = r; }}
    }}
    if (chosen === null) chosen = fallback;
    lastX[chosen] = x;
    rows[i] = chosen;
  }});
  const yPerPx = 3 / plotH;
  return rows.map(r => r * spacing * yPerPx);
}}

// ── Traces ─────────────────────────────────────────────────────────────────────
function plotDims(tier) {{
  const c = TIER_CFG[tier];
  const w = document.getElementById('chart').clientWidth || 800;
  return {{
    plotW: Math.max(w - c.margin.l - c.margin.r, 100),
    plotH: c.height - c.margin.t - c.margin.b,
  }};
}}

function buildTraces(tier) {{
  const c = TIER_CFG[tier];
  const W = INDEX[currentProduct].byWeek[currentWeek];
  const s = W.stats;
  const [x0, x1] = INDEX[currentProduct].xrange;
  const dims = plotDims(tier);
  const dimming = highlighted.size > 0;
  const overlayOp = dimming ? 0.35 : 1;

  // 2026 joins the swarm so it never sits on top of a prior-year dot
  const values = W.prior.map(o => o.value);
  if (W.cur) values.push(W.cur.value);
  const ys = swarmOffsets(values, x0, x1, dims.plotW, dims.plotH, c.dot);

  // The axis is plotted in million barrels; the payload and tooltips stay in
  // thousand barrels (the EIA series unit).
  const toM = v => v / 1000;

  const priorColors = W.prior.map(o => {{
    const [r, g, b] = decadeRgb(o.decade);
    const a = !dimming ? 0.88 : (highlighted.has(o.decade) ? 0.95 : 0.15);
    return `rgba(${{r}},${{g}},${{b}},${{a}})`;
  }});
  const priorCustom = W.prior.map(o => {{
    const rk = W.rank[o.year];
    const rankStr = rk - 1 <= s.n - rk
      ? `${{ordinal(rk)}} lowest of ${{s.n}} years`
      : `${{ordinal(s.n - rk + 1)}} highest of ${{s.n}} years`;
    return [o.year, fmtDate(o.date), fmtComma(o.value),
            signed(o.value - s.median, fmtComma), rankStr];
  }});

  const traces = [
    {{ // IQR band
      x: [s.q1, s.q3, s.q3, s.q1, s.q1].map(toM), y: [-1, -1, 1, 1, -1],
      type: 'scatter', mode: 'lines', fill: 'toself',
      fillcolor: bandColor(), line: {{width: 0}},
      opacity: overlayOp, hoverinfo: 'skip',
    }},
    {{ // median line
      x: [toM(s.median), toM(s.median)], y: [-1, 1], type: 'scatter', mode: 'lines',
      line: {{color: inkColor(), width: 2.5}},
      opacity: overlayOp, hoverinfo: 'skip',
    }},
    {{ // mean line
      x: [toM(s.mean), toM(s.mean)], y: [-1, 1], type: 'scatter', mode: 'lines',
      line: {{color: inkColor(), width: 2, dash: 'dash'}},
      opacity: overlayOp, hoverinfo: 'skip',
    }},
    {{ // median label
      x: [toM(s.median)], y: [1.28], type: 'scatter', mode: 'text',
      text: ['median ' + fmtMbbl(s.median)],
      textfont: {{size: 11, color: mutedColor()}},
      textposition: 'middle center', cliponaxis: false,
      opacity: overlayOp, hoverinfo: 'skip',
    }},
    {{ // mean label
      x: [toM(s.mean)], y: [-1.28], type: 'scatter', mode: 'text',
      text: ['mean ' + fmtMbbl(s.mean)],
      textfont: {{size: 11, color: mutedColor()}},
      textposition: 'middle center', cliponaxis: false,
      opacity: overlayOp, hoverinfo: 'skip',
    }},
    {{ // prior-year dots
      x: W.prior.map(o => toM(o.value)), y: ys.slice(0, W.prior.length),
      type: 'scatter', mode: 'markers',
      marker: {{size: c.dot, color: priorColors,
                line: {{width: 1.5, color: surfaceColor()}}}},
      customdata: priorCustom,
      hovertemplate:
        '<b>%{{customdata[0]}}</b> &#183; week ending %{{customdata[1]}}<br>' +
        '%{{customdata[2]}} thousand barrels<br>' +
        '%{{customdata[3]}} vs prior-year median &#183; %{{customdata[4]}}' +
        '<extra></extra>',
    }},
    {{ // current-year dot — drawn last, never dimmed
      x: W.cur ? [toM(W.cur.value)] : [], y: W.cur ? [ys[ys.length - 1]] : [],
      type: 'scatter', mode: 'markers',
      marker: {{size: c.curDot, color: RED,
                line: {{width: 2, color: surfaceColor()}}}},
      customdata: W.cur ? [[
        fmtDate(W.cur.date), fmtComma(W.cur.value),
        signed(W.cur.value - s.median, fmtComma),
        `higher than ${{W.prior.filter(o => o.value < W.cur.value).length}} of ${{s.n}} prior years`,
      ]] : [],
      hovertemplate:
        `<b>${{CURRENT_YEAR}}</b> &#183; week ending %{{customdata[0]}}<br>` +
        '%{{customdata[1]}} thousand barrels<br>' +
        '%{{customdata[2]}} vs prior-year median &#183; %{{customdata[3]}}' +
        '<extra></extra>',
    }},
  ];
  return traces;
}}

function layoutFor(tier) {{
  const c = TIER_CFG[tier];
  return {{
    margin: c.margin,
    plot_bgcolor: 'rgba(0,0,0,0)', paper_bgcolor: 'rgba(0,0,0,0)',
    xaxis: {{
      title: {{text: '<b>Million barrels</b>', font: {{size: c.titleSize}}}},
      range: INDEX[currentProduct].xrange.map(v => v / 1000),
      nticks: c.nticks, tickformat: c.tickFmt, separatethousands: true,
      gridcolor: gridColor(), showgrid: true, zeroline: false, fixedrange: true,
    }},
    yaxis: {{visible: false, range: [-1.5, 1.5], fixedrange: true}},
    showlegend: false,
    hovermode: 'closest',
    dragmode: false,
    font: {{family: '-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",sans-serif',
            size: c.fontSize, color: mutedColor()}},
    height: c.height,
    uirevision: 'dotstrip',
  }};
}}

// ── Headline ───────────────────────────────────────────────────────────────────
function updateHeadline() {{
  const cur = INDEX[currentProduct].byWeek[currentWeek].cur;
  if (!cur) return;   // weeks are capped, so this shouldn't happen
  document.getElementById('headline').innerHTML =
    `Week ${{currentWeek}} &#8212; ${{PRODUCT_LABELS[currentProduct]}}, ` +
    `${{CURRENT_YEAR}}: ${{fmtMbbl(cur.value)}} bbl`;
}}

// ── Render + navigation ────────────────────────────────────────────────────────
const config = {{responsive: true, displayModeBar: false}};

function render() {{
  Plotly.react('chart', buildTraces(lastTier), layoutFor(lastTier), config);
  updateHeadline();
}}

const slider = document.getElementById('week-slider');

function goToWeek(wk, animated) {{
  currentWeek = wk;
  if (+slider.value !== wk) slider.value = wk;
  updateHeadline();
  const ms = animated ? transMs() : 0;
  if (ms > 0) {{
    try {{
      Plotly.animate('chart', {{data: buildTraces(lastTier)}},
        {{transition: {{duration: ms, easing: 'cubic-in-out'}},
          frame: {{duration: ms, redraw: false}}}});
    }} catch (e) {{
      Plotly.react('chart', buildTraces(lastTier), layoutFor(lastTier), config);
    }}
  }} else {{
    Plotly.react('chart', buildTraces(lastTier), layoutFor(lastTier), config);
  }}
}}

// ── Play through the weeks of the current year ─────────────────────────────────
const playBtn = document.getElementById('play-btn');

function setPlayIcon() {{
  playBtn.innerHTML = playing ? '&#9208;'
    : (currentWeek >= LATEST_WEEK[currentProduct] ? '&#8635;' : '&#9654;');
  playBtn.setAttribute('aria-label',
    playing ? 'Pause' : 'Play through the weeks of ' + CURRENT_YEAR);
}}

function stopPlay() {{
  playing = false;
  clearTimeout(playTimer);
  setPlayIcon();
}}

function tick() {{
  if (!playing) return;
  if (currentWeek >= LATEST_WEEK[currentProduct]) {{ stopPlay(); return; }}
  goToWeek(currentWeek + 1, true);
  playTimer = setTimeout(tick, stepMs());
}}

playBtn.addEventListener('click', () => {{
  if (playing) {{ stopPlay(); return; }}
  if (currentWeek >= LATEST_WEEK[currentProduct]) goToWeek(1, false);
  playing = true;
  setPlayIcon();
  playTimer = setTimeout(tick, stepMs());
}});

// Speed toggles: 2x/3x multiply the play rate; clicking the active one
// returns to 1x. A speed change applies from the next step.
const speedBtns = {{2: document.getElementById('speed-2x'),
                    3: document.getElementById('speed-3x')}};
function syncSpeedBtns() {{
  for (const s in speedBtns) {{
    const on = speed === +s;
    speedBtns[s].classList.toggle('on', on);
    speedBtns[s].setAttribute('aria-pressed', on);
  }}
}}
for (const s in speedBtns) {{
  speedBtns[s].addEventListener('click', () => {{
    speed = (speed === +s) ? 1 : +s;
    syncSpeedBtns();
  }});
}}

slider.addEventListener('input', () => {{
  stopPlay();
  goToWeek(+slider.value, false);
  setPlayIcon();
}});

function syncProductPills() {{
  document.querySelectorAll('.product-pill').forEach(pill => {{
    const on = pill.dataset.product === currentProduct;
    pill.classList.toggle('on', on);
    pill.setAttribute('aria-pressed', on);
  }});
}}

document.querySelectorAll('.product-pill').forEach(pill => {{
  pill.addEventListener('click', () => {{
    if (pill.dataset.product === currentProduct) return;
    stopPlay();
    currentProduct = pill.dataset.product;
    const maxW = LATEST_WEEK[currentProduct];
    slider.max = maxW;
    currentWeek = Math.min(currentWeek, maxW);
    slider.value = currentWeek;
    document.getElementById('source-note').textContent = SOURCE_NOTES[currentProduct];
    syncProductPills();
    render();
    setPlayIcon();
  }});
}});

// ── Decade highlighter (Tableau-style: dims, never filters) ────────────────────
function syncChips() {{
  document.querySelectorAll('.decade-chip').forEach(chip => {{
    const on = highlighted.has(+chip.dataset.decade);
    chip.classList.toggle('on', on);
    chip.setAttribute('aria-pressed', on);
    chip.style.background  = on ? chip.dataset.color : '';
    chip.style.color       = on ? '#fff' : '';
    chip.style.borderColor = on ? chip.dataset.color : '';
  }});
  document.getElementById('clear-hl').hidden = highlighted.size === 0;
}}

document.querySelectorAll('.decade-chip').forEach(chip => {{
  chip.addEventListener('click', () => {{
    const dec = +chip.dataset.decade;
    if (highlighted.has(dec)) highlighted.delete(dec);
    else highlighted.add(dec);
    syncChips();
    render();
  }});
}});

document.getElementById('clear-hl').addEventListener('click', () => {{
  highlighted.clear();
  syncChips();
  render();
}});

// ── Resize / theme change ──────────────────────────────────────────────────────
// Swarm positions depend on plot width in px, so recompute on every settle,
// not just on tier changes.
let resizeTimer = null;
window.addEventListener('resize', () => {{
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {{
    lastTier = tierFor(window.innerWidth);
    render();
  }}, 150);
}});
darkMq.addEventListener('change', render);

// ── Init ───────────────────────────────────────────────────────────────────────
slider.max = LATEST_WEEK[currentProduct];
slider.value = currentWeek;
syncChips();
setPlayIcon();
// Re-render once mounted: the initial render can add a scrollbar, changing the
// chart width the beeswarm was computed against.
Plotly.newPlot('chart', buildTraces(lastTier), layoutFor(lastTier), config)
  .then(() => render());
</script>
</body>
</html>"""

# ── Write the HTML file ────────────────────────────────────────────────────────
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"Saved: {OUTPUT}  ({os.path.getsize(OUTPUT):,} bytes)")
