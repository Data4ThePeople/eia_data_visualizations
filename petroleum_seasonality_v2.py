# petroleum_seasonality_v2.py
#
# Generates an interactive HTML chart of U.S. weekly petroleum inventory
# data sourced from the EIA (U.S. Energy Information Administration).
#
# Each product is shown as one line per year, colored by decade.
# The chart includes a product dropdown and decade toggle pills.
#
# To run:  python petroleum_seasonality_v2.py
# Output:  petroleum_seasonality_v2_viz.html  (open in any web browser)
#
# Requirements: pandas, requests, python-dotenv
#   Install with:  pip install pandas requests python-dotenv
#
# Changes from v1:
#   - Axis titles are bold and larger (14px)
#   - Responsive layout tiers for small screens: chart height, margins, tick
#     density, fonts, y-label format, and touch zoom adapt below 700px/450px

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
    "crude_oil":  ("Crude Oil",               "WCRSTUS1", "1982"),
    "gasoline":   ("Total Gasoline",          "WGTSTUS1", "1990"),
    "distillate": ("Distillate (Diesel)",     "WDISTUS1", "1982"),
    "spr":        ("Strategic Reserve (SPR)", "WCSSTUS1", "1982"),
}


# ── Decade colour palette ──────────────────────────────────────────────────────
DECADE_CFG = {
    1980: {"mid": "rgba(0,140,175,0.90)",  "label": "1980s",
           "lr": 110, "lg": 200, "lb": 225, "la": 0.28,
           "dr":   0, "dg": 120, "db": 150, "da": 0.86},
    1990: {"mid": "rgba(18,122,42,0.90)",   "label": "1990s",
           "lr": 120, "lg": 200, "lb": 135, "la": 0.28,
           "dr":  18, "dg": 122, "db":  42, "da": 0.86},
    2000: {"mid": "rgba(10,72,172,0.90)",   "label": "2000s",
           "lr": 118, "lg": 168, "lb": 228, "la": 0.28,
           "dr":  10, "dg":  72, "db": 172, "da": 0.88},
    2010: {"mid": "rgba(185,85,5,0.90)",    "label": "2010s",
           "lr": 248, "lg": 178, "lb":  82, "la": 0.28,
           "dr": 185, "dg":  85, "db":   5, "da": 0.88},
    2020: {"mid": "rgba(108,35,162,0.90)",  "label": "2020s",
           "lr": 200, "lg": 148, "lb": 228, "la": 0.28,
           "dr": 108, "dg":  35, "db": 162, "da": 0.88},
}

# ── Average-overlay colours ────────────────────────────────────────────────────
AVG_LINE = "rgba(17,17,17,0.95)"    # mean — dashed black
AVG_BAND = "rgba(128,128,128,0.18)" # ±1σ fill — light gray, faint by design
AVG_PILL = "#3a3a3a"                # active pill (white text, AA contrast)


# ── Serialize chart data to JSON ───────────────────────────────────────────────
chart_data = {}
for col in PRODUCTS:
    s = stocks[["year", "week", col]].dropna(subset=[col]).copy()
    s["decade"] = (s["year"] // 10) * 10
    rows = []
    for yr, grp in s.groupby("year"):
        g = grp.sort_values("week")
        rows.append({
            "year":   int(yr),
            "decade": int(g["decade"].iloc[0]),
            "x":      g["week"].tolist(),
            "y":      g[col].tolist(),
        })
    chart_data[col] = rows

all_decades = sorted({
    row["decade"]
    for series in chart_data.values()
    for row in series
    if row["year"] < CURRENT_YEAR
})


def src(sid, sy):
    return (
        f"EIA series {sid} — Weekly U.S. Ending Stocks, {sy}–present, "
        f"thousand barrels. Latest year: {CURRENT_YEAR}. "
        "Week = (day-of-year / 7), capped at 52."
    )

source_notes = {col: src(sid, sy) for col, (_, sid, sy) in PRODUCTS.items()}

# Per-product note naming years whose interior missing weeks are interpolated
# in the average/band calculation (empty string when a product has none).
interp_notes = {}
for col, rows in chart_data.items():
    gap_years = sorted({
        r["year"] for r in rows
        if r["year"] < CURRENT_YEAR
        and set(range(min(r["x"]), max(r["x"]) + 1)) - set(r["x"])
    })
    if not gap_years:
        interp_notes[col] = ""
        continue
    if len(gap_years) == 1:
        yrs = str(gap_years[0])
    elif len(gap_years) == 2:
        yrs = f"{gap_years[0]} and {gap_years[1]}"
    else:
        yrs = ", ".join(map(str, gap_years[:-1])) + f", and {gap_years[-1]}"
    interp_notes[col] = (
        f"A few weeks missing from the {yrs} weekly record are filled by "
        "linear interpolation when computing the average and ±1σ band; "
        "the plotted year lines leave those gaps open."
    )


# ── D4TP logo ──────────────────────────────────────────────────────────────────
LOGO_PATH = r"C:\Users\amand\Workspace\D4TP\logos\d4tp-text-dark@2x.png"
_mime = mimetypes.guess_type(LOGO_PATH)[0] or "image/png"
with open(LOGO_PATH, "rb") as _f:
    LOGO_SRC = f"data:{_mime};base64,{base64.b64encode(_f.read()).decode()}"


# ── Build legend HTML ──────────────────────────────────────────────────────────
legend_items = (
    f'  <div class="legend-item">'
    f'<span class="leg-line" style="background:#c0392b;height:3px;opacity:1"></span>'
    f'<span class="leg-label">{CURRENT_YEAR}</span></div>'
)
legend_items += (
    f'\n  <div class="legend-item" data-role="avg">'
    f'<span class="leg-band"></span>'
    f'<span class="leg-label">Average &plusmn;1&sigma; (all decades)</span></div>'
)
for dec in sorted(DECADE_CFG, reverse=True):
    if dec not in all_decades:
        continue
    d = DECADE_CFG[dec]
    legend_items += (
        f'\n  <div class="legend-item" data-decade="{dec}">'
        f'<span class="leg-line" style="background:{d["mid"]}"></span>'
        f'<span class="leg-label">{d["label"]}</span></div>'
    )

decade_pills_html = ""
for dec in all_decades:
    d = DECADE_CFG[dec]
    decade_pills_html += (
        f'<button class="decade-pill active" data-decade="{dec}" '
        f'data-color="{d["mid"]}">{d["label"]}</button>'
    )

decade_pills_html += (
    f'<button class="decade-pill active" id="avg-pill" '
    f'data-color="{AVG_PILL}">Average &plusmn;1&sigma;</button>'
)

select_options = "\n".join(
    f'      <option value="{col}">{label}</option>'
    for col, (label, _, _) in PRODUCTS.items()
)


# ── Output file name ───────────────────────────────────────────────────────────
OUTPUT = "petroleum_seasonality_v2_viz.html"


HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>U.S. Petroleum Inventories - Weekly Seasonality</title>
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
  grid-template-columns:auto 1fr auto;
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
.ctrl-grp select{{
  font-size:14px;padding:8px 32px 8px 11px;
  background:var(--bg-primary);color:var(--text-primary);
  border:0.5px solid var(--border);border-radius:7px;font-family:inherit;cursor:pointer;
  -webkit-appearance:none;appearance:none;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path d='M0 0l5 6 5-6z' fill='%23555'/></svg>");
  background-repeat:no-repeat;background-position:right 12px center;min-height:38px;
}}
.decade-pills{{display:flex;gap:5px;flex-wrap:wrap;}}
.decade-pill{{
  padding:8px 14px;font-size:13px;
  background:var(--bg-primary);color:var(--text-secondary);
  border:0.5px solid var(--border);border-radius:7px;
  cursor:pointer;font-family:inherit;
  transition:background 0.12s,color 0.12s,border-color 0.12s,opacity 0.12s;
  min-height:38px;white-space:nowrap;
}}
.decade-pill:hover{{border-color:var(--border-strong);}}
.decade-pill.off{{
  background:var(--bg-primary) !important;
  color:var(--text-tertiary) !important;
  border-color:var(--border) !important;
  opacity:0.55;
}}
.legend{{display:flex;flex-wrap:wrap;gap:6px 16px;margin-bottom:8px;
         font-size:12px;color:var(--text-secondary);}}
.legend-item{{display:flex;align-items:center;gap:7px;transition:opacity 0.15s;}}
.leg-line{{display:inline-block;width:22px;height:2px;border-radius:1px;flex-shrink:0;}}
.leg-band{{display:inline-block;width:22px;height:10px;border-radius:2px;flex-shrink:0;
  background-color:rgba(128,128,128,0.35);
  background-image:repeating-linear-gradient(90deg,{AVG_LINE} 0 4px,rgba(0,0,0,0) 4px 7px);
  background-size:100% 2px;background-position:0 center;background-repeat:no-repeat;}}
.leg-label{{white-space:nowrap;}}
#chart{{width:100%;}}
#year-banner{{
  position:absolute;top:10px;right:28px;z-index:5;pointer-events:none;
  font-size:clamp(22px,4vw,34px);font-weight:700;letter-spacing:0.02em;
  font-variant-numeric:tabular-nums;opacity:0;transition:opacity 0.25s;
}}
.notes{{font-size:11px;color:var(--text-secondary);margin-top:12px;line-height:1.6;
        padding-top:12px;border-top:0.5px solid var(--border);}}
.notes strong{{color:var(--text-primary);font-weight:500;}}
.credit-bar{{display:flex;justify-content:flex-end;align-items:center;
             margin-top:14px;padding-top:12px;border-top:0.5px solid var(--border);}}
.d4tp-logo{{display:inline-block;text-decoration:none;opacity:0.85;transition:opacity 0.15s;}}
.d4tp-logo:hover{{opacity:1;}}
.d4tp-logo svg{{display:block;height:24px;width:auto;}}
.logo-light-mode{{display:inline-block;}} .logo-dark-mode{{display:none;}}
@media(prefers-color-scheme:dark){{
  .logo-light-mode{{display:none;}} .logo-dark-mode{{display:inline-block;}}
}}
@media(max-width:700px){{
  body{{padding:14px;}} .hdr h1{{font-size:18px;}}
  .ctrls{{grid-template-columns:1fr;}}
}}
</style>
</head>
<body>

<div class="hdr">
  <h1>U.S. Petroleum Inventories &#8212; Weekly Seasonality</h1>
  <p>Stocks by week of year (1&#8211;52), one line per year. {CURRENT_YEAR} bolded in red; prior years shaded by decade.</p>
</div>

<div class="ctrls">
  <div class="ctrl-grp">
    <label for="product-sel">Product</label>
    <select id="product-sel">
{select_options}
    </select>
  </div>
  <div class="ctrl-grp">
    <label>Decades</label>
    <div class="decade-pills" id="decade-pills">
      {decade_pills_html}
    </div>
  </div>
  <div class="ctrl-grp">
    <label>Replay</label>
    <div class="decade-pills">
      <button class="decade-pill" id="play-btn">&#9654; Play</button>
      <button class="decade-pill" id="speed-2x">2&times;</button>
      <button class="decade-pill" id="speed-3x">3&times;</button>
    </div>
  </div>
</div>

<div class="legend" id="legend">
{legend_items}
</div>

<div id="chart-wrap" style="position:relative;">
  <div id="chart"></div>
  <div id="year-banner"></div>
</div>

<div class="notes">
  <strong>Source:</strong> <span id="source-note">{source_notes['crude_oil']}</span>
  <span id="interp-note-row"><br><strong>Note:</strong> <span id="interp-note">{interp_notes['crude_oil']}</span></span>
</div>

<div class="credit-bar">
  <img src="{LOGO_SRC}" alt="D4TP" style="height:24px;width:auto;opacity:0.85;">
</div>

<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<script>
const CURRENT_YEAR  = {CURRENT_YEAR};
const CHART_DATA    = {json.dumps(chart_data)};
const SOURCE_NOTES  = {json.dumps(source_notes)};
const INTERP_NOTES  = {json.dumps(interp_notes)};

const AVG_LINE_COLOR = '{AVG_LINE}';
const AVG_BAND_COLOR = '{AVG_BAND}';
const DECADE_MID     = {json.dumps({d: c["mid"] for d, c in DECADE_CFG.items()})};

const DECADE_PALETTES = {{
  1980:{{lr:110,lg:200,lb:225,la:0.28,dr:0,  dg:120,db:150,da:0.86}},
  1990:{{lr:120,lg:200,lb:135,la:0.28,dr:18, dg:122,db:42, da:0.86}},
  2000:{{lr:118,lg:168,lb:228,la:0.28,dr:10, dg:72, db:172,da:0.88}},
  2010:{{lr:248,lg:178,lb:82, la:0.28,dr:185,dg:85, db:5,  da:0.88}},
  2020:{{lr:200,lg:148,lb:228,la:0.28,dr:108,dg:35, db:162,da:0.88}},
}};

function decadeRgba(decade, frac) {{
  const p = DECADE_PALETTES[decade];
  const r = Math.round(p.lr + frac*(p.dr-p.lr));
  const g = Math.round(p.lg + frac*(p.dg-p.lg));
  const b = Math.round(p.lb + frac*(p.db-p.lb));
  const a = (p.la + frac*(p.da-p.la)).toFixed(2);
  return `rgba(${{r}},${{g}},${{b}},${{a}})`;
}}

let currentProduct = 'crude_oil';
const selectedDecades = new Set({json.dumps(all_decades)});
const ALL_DECADE_COUNT = {len(all_decades)};
let showAverage = true;

function computeAvgStats(product) {{
  const perWeekVals = {{}};                 // week -> [one value per contributing year]
  CHART_DATA[product].forEach(s => {{
    if (s.year >= CURRENT_YEAR || !selectedDecades.has(s.decade)) return;
    const wk = {{}};                        // average duplicate week buckets within the year first
    for (let i = 0; i < s.x.length; i++) {{
      const w = s.x[i];
      if (!wk[w]) wk[w] = {{sum: 0, n: 0}};
      wk[w].sum += s.y[i]; wk[w].n++;
    }}
    // Interior gaps (e.g. 1983 skips weeks 16/18/21): fill by linear
    // interpolation between the nearest reported weeks so the average
    // doesn't jump when a low or high year drops out for one week.
    // Leading/trailing gaps (1982 starts at week 34) stay unfilled.
    const have = Object.keys(wk).map(Number).sort((a, b) => a - b);
    for (let w = have[0] + 1; w < have[have.length - 1]; w++) {{
      if (wk[w]) continue;
      let lo = w - 1; while (!wk[lo]) lo--;
      let hi = w + 1; while (!wk[hi]) hi++;
      const vLo = wk[lo].sum / wk[lo].n, vHi = wk[hi].sum / wk[hi].n;
      wk[w] = {{ sum: vLo + (vHi - vLo) * (w - lo) / (hi - lo), n: 1 }};
    }}
    for (const w in wk) {{
      if (!perWeekVals[w]) perWeekVals[w] = [];
      perWeekVals[w].push(wk[w].sum / wk[w].n);
    }}
  }});
  const weeks = Object.keys(perWeekVals).map(Number).sort((a, b) => a - b);
  if (!weeks.length) return null;
  const mean = [], lower = [], upper = [];
  weeks.forEach(w => {{
    const vals = perWeekVals[w];
    const m = vals.reduce((a, v) => a + v, 0) / vals.length;
    mean.push(m);
    if (vals.length < 2) {{ lower.push(null); upper.push(null); return; }}  // no band without 2+ years
    const sd = Math.sqrt(vals.reduce((a, v) => a + (v - m) * (v - m), 0) / (vals.length - 1));  // sample std
    lower.push(m - sd); upper.push(m + sd);
  }});
  return {{ weeks, mean, lower, upper }};
}}

// Year traces in chronological order (prior years, then the current year).
function buildYearTraces(product) {{
  const series = CHART_DATA[product];
  const prior  = series.filter(s => s.year < CURRENT_YEAR);

  const decadeGroups = {{}};
  prior.forEach(s => {{
    if (selectedDecades.has(s.decade)) {{
      if (!decadeGroups[s.decade]) decadeGroups[s.decade] = [];
      decadeGroups[s.decade].push(s.year);
    }}
  }});

  const priorTraces = [];
  prior.forEach(s => {{
    if (!selectedDecades.has(s.decade)) return;
    const grp  = decadeGroups[s.decade];
    const frac = grp.indexOf(s.year) / Math.max(grp.length - 1, 1);
    priorTraces.push({{
      x: s.x, y: s.y, type: 'scatter', mode: 'lines',
      line: {{ color: decadeRgba(s.decade, frac), width: 1 }},
      meta: {{ year: s.year, decade: s.decade }},
      hovertemplate: `Year: ${{s.year}}<br>Week: %{{x}}<br>%{{y:,.0f}} thousand barrels<extra></extra>`,
    }});
  }});

  const cur = series.find(s => s.year === CURRENT_YEAR);
  const curTrace = cur ? {{
    x: cur.x, y: cur.y, type: 'scatter', mode: 'lines',
    line: {{ color: '#c0392b', width: 2.8 }},
    meta: {{ year: CURRENT_YEAR, decade: (CURRENT_YEAR / 10 | 0) * 10 }},
    hovertemplate: `Year: ${{CURRENT_YEAR}}<br>Week: %{{x}}<br>%{{y:,.0f}} thousand barrels<extra></extra>`,
  }} : null;

  return {{ priorTraces, curTrace }};
}}

function buildTraces(product) {{
  const {{ priorTraces, curTrace }} = buildYearTraces(product);
  const traces = [];

  const stats = showAverage ? computeAvgStats(product) : null;
  // A std dev from one or two decades (~10-30 years) mostly reflects that
  // era's trend, not seasonal spread — only band the full history.
  const showBand = stats && selectedDecades.size === ALL_DECADE_COUNT;

  if (showBand) {{
    traces.push({{
      x: stats.weeks, y: stats.lower, type: 'scatter', mode: 'lines',
      line: {{ width: 0 }}, hoverinfo: 'skip', connectgaps: false,
    }});
    traces.push({{
      x: stats.weeks, y: stats.upper, type: 'scatter', mode: 'lines',
      line: {{ width: 0 }}, fill: 'tonexty', fillcolor: AVG_BAND_COLOR,
      hoverinfo: 'skip', connectgaps: false,
    }});
  }}

  priorTraces.forEach(t => traces.push(t));

  if (stats) {{
    traces.push({{
      x: stats.weeks, y: stats.mean, type: 'scatter', mode: 'lines',
      line: {{ color: AVG_LINE_COLOR, width: 3, dash: 'dash' }},
      hovertemplate: 'Average (selected decades)<br>Week: %{{x}}<br>%{{y:,.0f}} thousand barrels<extra></extra>',
    }});
  }}

  if (curTrace) traces.push(curTrace);

  return traces;
}}

// Breakpoints mirror the CSS @media(max-width:700px) query — keep them in sync.
function tierFor(w) {{ return w < 450 ? 'xs' : w < 700 ? 'sm' : 'lg'; }}

function tickvalsBy(step) {{
  const v = [];
  for (let wk = 1; wk <= 52; wk += step) v.push(wk);
  return v;
}}

const TIER_CFG = {{
  lg: {{height:500, margin:{{t:14,b:60,l:88,r:16}}, tickStep:2, titleSize:14, fontSize:12}},
  sm: {{height:420, margin:{{t:12,b:50,l:52,r:10}}, tickStep:4, titleSize:12, fontSize:11}},
  xs: {{height:370, margin:{{t:12,b:46,l:48,r:8}},  tickStep:8, titleSize:12, fontSize:11}},
}};

function layoutFor(tier) {{
  const c = TIER_CFG[tier];
  const layout = {{
    margin: c.margin,
    plot_bgcolor:'rgba(0,0,0,0)', paper_bgcolor:'rgba(0,0,0,0)',
    xaxis:{{
      title:{{text:'<b>Week of year</b>', font:{{size:c.titleSize}}}},
      tickmode:'array',
      tickvals:tickvalsBy(c.tickStep),
      range:[0.5,52.5], gridcolor:'rgba(210,215,225,0.7)', showgrid:true, zeroline:false,
    }},
    yaxis:{{
      title:{{text:'<b>Thousand barrels</b>', font:{{size:c.titleSize}}}},
      gridcolor:'rgba(210,215,225,0.7)', showgrid:true, zeroline:false,
    }},
    showlegend: false,
    font:{{family:'-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",sans-serif',size:c.fontSize}},
    height: c.height,
    uirevision: 'seasonality',
  }};
  if (tier === 'lg') {{
    layout.yaxis.tickformat = ',';
    layout.yaxis.separatethousands = true;
  }} else {{
    layout.yaxis.tickformat = '~s';   // "1.5M" — full values remain in the hover text
    layout.yaxis.automargin = true;
    layout.dragmode = false;          // don't trap page scroll on touch screens
  }}
  return layout;
}}

function currentLayout() {{ return layoutFor(tierFor(window.innerWidth)); }}

const config = {{responsive:true, displayModeBar:false}};

// Re-measure once rendered: the initial render can add a scrollbar, and
// Plotly's responsive handler doesn't notice the narrower viewport on its own.
Plotly.newPlot('chart', buildTraces(currentProduct), currentLayout(), config)
  .then(() => Plotly.Plots.resize('chart'));

function syncLegend() {{
  const bandOn = selectedDecades.size === ALL_DECADE_COUNT;
  document.querySelectorAll('#legend .legend-item[data-decade]').forEach(el => {{
    el.style.opacity = selectedDecades.has(+el.dataset.decade) ? '1' : '0.25';
  }});
  const avgItem = document.querySelector('#legend .legend-item[data-role="avg"]');
  if (avgItem) {{
    avgItem.style.opacity = (showAverage && selectedDecades.size) ? '1' : '0.25';
    avgItem.querySelector('.leg-label').textContent =
      bandOn ? 'Average ±1σ (all decades)' : 'Average (selected decades)';
    avgItem.querySelector('.leg-band').style.backgroundColor = bandOn ? '' : 'transparent';
  }}
  const avgPillEl = document.getElementById('avg-pill');
  if (avgPillEl) avgPillEl.textContent = bandOn ? 'Average ±1σ' : 'Average';
}}

document.querySelectorAll('.decade-pill[data-decade]').forEach(pill => {{
  const decade = +pill.dataset.decade;
  const color  = pill.dataset.color;

  function applyStyle() {{
    const on = selectedDecades.has(decade);
    pill.classList.toggle('off', !on);
    pill.style.background  = on ? color : '';
    pill.style.color       = on ? '#fff' : '';
    pill.style.borderColor = on ? color : '';
  }}

  applyStyle();

  pill.addEventListener('click', () => {{
    if (selectedDecades.has(decade)) selectedDecades.delete(decade);
    else                              selectedDecades.add(decade);
    applyStyle();
    syncLegend();
    redraw();
  }});
}});

const avgPill = document.getElementById('avg-pill');
function styleAvgPill() {{
  avgPill.classList.toggle('off', !showAverage);
  avgPill.style.background  = showAverage ? avgPill.dataset.color : '';
  avgPill.style.color       = showAverage ? '#fff' : '';
  avgPill.style.borderColor = showAverage ? avgPill.dataset.color : '';
}}
styleAvgPill();
avgPill.addEventListener('click', () => {{
  showAverage = !showAverage;
  styleAvgPill();
  syncLegend();
  redraw();
}});

// ── Replay animation: draw each year's line in chronological order ────────────
const ANIM_SECONDS = 30;   // full history at 1x; the rate scales for subsets
const playBtn   = document.getElementById('play-btn');
const speedBtns = [[document.getElementById('speed-2x'), 2],
                   [document.getElementById('speed-3x'), 3]];
const yearBanner = document.getElementById('year-banner');
let anim = null;
let yAxisFrozen = false;   // y-range pinned during playback

function updateAnimButtons() {{
  playBtn.innerHTML = anim ? '&#9632; Stop' : '&#9654; Play';
  speedBtns.forEach(([b, sp]) => {{
    const on = anim && anim.speed === sp;
    b.style.background  = on ? '#3a3a3a' : '';
    b.style.color       = on ? '#fff' : '';
    b.style.borderColor = on ? '#3a3a3a' : '';
  }});
}}

// Every full redraw goes through here: it cancels any running playback and
// unpins the y-axis so the chart returns to its normal autoranged state.
function redraw() {{
  if (anim) {{
    cancelAnimationFrame(anim.raf);
    anim = null;
    updateAnimButtons();
  }}
  yearBanner.style.opacity = 0;
  const lay = currentLayout();
  if (yAxisFrozen) {{
    lay.yaxis.autorange = true;
    yAxisFrozen = false;
  }}
  Plotly.react('chart', buildTraces(currentProduct), lay, config);
}}

function animStep(now) {{
  if (!anim) return;
  const target = Math.min(anim.total,
    anim.prog0 + (now - anim.t0) / 1000 * anim.speed * anim.rate);
  anim.lastPts = target;
  let remaining = Math.floor(target);
  const idxs = [], xs = [], ys = [];
  let k = -1;   // the trace currently being drawn (last one with any points)
  for (let i = 0; i < anim.full.length; i++) {{
    const n = Math.min(anim.counts[i], remaining);
    remaining -= n;
    if (n > 0) k = i;
    if (n !== anim.shown[i]) {{
      anim.shown[i] = n;
      idxs.push(i);
      xs.push(anim.full[i].x.slice(0, n));
      ys.push(anim.full[i].y.slice(0, n));
    }}
  }}

  // Arrow head at the drawing tip, aimed at the next point to be drawn.
  // angleref:'previous' angles the tip marker along anchor->tip, so aiming
  // at the NEXT point means anchoring at its mirror across the tip.
  if (k >= 0 && idxs.length) {{
    const t = anim.full[k], n = anim.shown[k];
    const tx = t.x[n - 1], ty = t.y[n - 1];
    let px, py;
    if (n < anim.counts[k]) {{        // mirror the next point through the tip
      px = 2 * tx - t.x[n]; py = 2 * ty - t.y[n];
    }} else if (n > 1) {{             // year complete: keep the travel direction
      px = t.x[n - 2]; py = t.y[n - 2];
    }} else {{ px = tx - 1; py = ty; }}
    idxs.push(anim.arrowIdx);
    xs.push([px, tx]);
    ys.push([py, ty]);
    if (k !== anim.curTrace) {{       // new year: recolor arrow, update banner
      anim.curTrace = k;
      const color = t.meta.year === CURRENT_YEAR ? '#c0392b' : DECADE_MID[t.meta.decade];
      Plotly.restyle('chart', {{ 'marker.color': color }}, [anim.arrowIdx]);
      yearBanner.textContent = t.meta.year;
      yearBanner.style.color = color;
      yearBanner.style.opacity = 1;
    }}
  }}

  if (idxs.length) Plotly.restyle('chart', {{ x: xs, y: ys }}, idxs);
  if (target >= anim.total) {{
    redraw();   // playback finished: restore band, average, and autorange
    return;
  }}
  anim.raf = requestAnimationFrame(animStep);
}}

function startAnimation(speed) {{
  if (anim) {{ cancelAnimationFrame(anim.raf); anim = null; }}
  const yt   = buildYearTraces(currentProduct);
  const full = yt.priorTraces.concat(yt.curTrace ? [yt.curTrace] : []);
  if (!full.length) {{ updateAnimButtons(); return; }}

  // Pin the y-range to the final extent so axes don't rescale mid-draw.
  let yMin = Infinity, yMax = -Infinity;
  full.forEach(t => t.y.forEach(v => {{
    if (v < yMin) yMin = v;
    if (v > yMax) yMax = v;
  }}));
  const pad = 0.06 * (yMax - yMin || 1);
  const lay = currentLayout();
  lay.yaxis.range = [yMin - pad, yMax + pad];
  lay.yaxis.autorange = false;
  yAxisFrozen = true;

  // 1x pace is calibrated so the FULL history takes ANIM_SECONDS; animating
  // a subset of decades finishes proportionally sooner at the same pace.
  const fullTotal = CHART_DATA[currentProduct].reduce((a, s) => a + s.x.length, 0);

  const empty = full.map(t => Object.assign({{}}, t, {{ x: [], y: [] }}));
  empty.push({{                        // the arrow head riding the drawing tip
    x: [], y: [], type: 'scatter', mode: 'markers',
    marker: {{ symbol: 'arrow', size: 14, angleref: 'previous',
              color: '#3a3a3a', opacity: [0, 1] }},
    hoverinfo: 'skip',
  }});
  Plotly.react('chart', empty, lay, config).then(() => {{
    if (anim) return;   // superseded by another start before this one drew
    anim = {{
      speed, full,
      counts: full.map(t => t.x.length),
      total:  full.reduce((a, t) => a + t.x.length, 0),
      shown:  full.map(() => 0),
      rate:   fullTotal / ANIM_SECONDS,   // points per second at 1x
      arrowIdx: full.length, curTrace: -1,
      prog0: 0, lastPts: 0, t0: performance.now(), raf: 0,
    }};
    updateAnimButtons();
    anim.raf = requestAnimationFrame(animStep);
  }});
}}

function setAnimSpeed(sp) {{
  if (anim) {{
    anim.prog0 = anim.lastPts;   // rebase so the speed change is seamless
    anim.t0    = performance.now();
    anim.speed = sp;
    updateAnimButtons();
  }} else {{
    startAnimation(sp);
  }}
}}

playBtn.addEventListener('click', () => {{
  if (anim) redraw();
  else      startAnimation(1);
}});
speedBtns.forEach(([b, sp]) => b.addEventListener('click', () => setAnimSpeed(sp)));

syncLegend();

let lastTier = tierFor(window.innerWidth);
let resizeTimer = null;
window.addEventListener('resize', () => {{
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {{
    const t = tierFor(window.innerWidth);
    if (t !== lastTier) {{
      lastTier = t;
      redraw();
    }}
  }}, 150);
}});

document.getElementById('product-sel').addEventListener('change', function() {{
  currentProduct = this.value;
  redraw();
  document.getElementById('source-note').textContent = SOURCE_NOTES[currentProduct];
  const inote = INTERP_NOTES[currentProduct];
  document.getElementById('interp-note-row').hidden = !inote;
  document.getElementById('interp-note').textContent = inote;
}});
</script>
</body>
</html>"""

# ── Write the HTML file ────────────────────────────────────────────────────────
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"Saved: {OUTPUT}  ({os.path.getsize(OUTPUT):,} bytes)")
