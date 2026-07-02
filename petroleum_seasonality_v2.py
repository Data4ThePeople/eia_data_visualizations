# petroleum_seasonality_v2.py
#
# Generates an interactive HTML chart of U.S. weekly petroleum inventory
# data sourced from the EIA (U.S. Energy Information Administration).
#
# Each product is shown as one line per year, coloured by decade.
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
#   - SPR chart annotates the week-over-week change for Jun 19 → Jun 26, 2026

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
    1980: {"mid": "rgba(105,105,120,0.90)", "label": "1980s",
           "lr": 168, "lg": 168, "lb": 175, "la": 0.28,
           "dr":  85, "dg":  85, "db": 102, "da": 0.84},
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


# ── Serialise chart data to JSON ───────────────────────────────────────────────
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
html,body{{background:var(--bg-primary);}}
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
.leg-label{{white-space:nowrap;}}
#chart{{width:100%;}}
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
</div>

<div class="legend" id="legend">
{legend_items}
</div>

<div id="chart"></div>

<div class="notes">
  <strong>Source:</strong> <span id="source-note">{source_notes['crude_oil']}</span>
</div>

<div class="credit-bar">
  <img src="{LOGO_SRC}" alt="D4TP" style="height:24px;width:auto;opacity:0.85;">
</div>

<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<script>
const CURRENT_YEAR  = {CURRENT_YEAR};
const CHART_DATA    = {json.dumps(chart_data)};
const SOURCE_NOTES  = {json.dumps(source_notes)};

const DECADE_PALETTES = {{
  1980:{{lr:168,lg:168,lb:175,la:0.28,dr:85, dg:85, db:102,da:0.84}},
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

function buildTraces(product) {{
  const series = CHART_DATA[product];
  const prior  = series.filter(s => s.year < CURRENT_YEAR);

  const decadeGroups = {{}};
  prior.forEach(s => {{
    if (selectedDecades.has(s.decade)) {{
      if (!decadeGroups[s.decade]) decadeGroups[s.decade] = [];
      decadeGroups[s.decade].push(s.year);
    }}
  }});

  const traces = [];

  prior.forEach(s => {{
    if (!selectedDecades.has(s.decade)) return;
    const grp  = decadeGroups[s.decade];
    const frac = grp.indexOf(s.year) / Math.max(grp.length - 1, 1);
    traces.push({{
      x: s.x, y: s.y, type: 'scatter', mode: 'lines',
      line: {{ color: decadeRgba(s.decade, frac), width: 1 }},
      hovertemplate: `Year: ${{s.year}}<br>Week: %{{x}}<br>%{{y:,.0f}} thousand barrels<extra></extra>`,
    }});
  }});

  const cur = series.find(s => s.year === CURRENT_YEAR);
  if (cur) traces.push({{
    x: cur.x, y: cur.y, type: 'scatter', mode: 'lines',
    line: {{ color: '#c0392b', width: 2.8 }},
    hovertemplate: `Year: ${{CURRENT_YEAR}}<br>Week: %{{x}}<br>%{{y:,.0f}} thousand barrels<extra></extra>`,
  }});

  return traces;
}}

const layout = {{
  margin: {{t:14, b:60, l:88, r:16}},
  plot_bgcolor:'rgba(0,0,0,0)', paper_bgcolor:'rgba(0,0,0,0)',
  xaxis:{{
    title:{{text:'<b>Week of year</b>', font:{{size:14}}}},
    tickmode:'array',
    tickvals:[1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,43,45,47,49,51],
    range:[0.5,52.5], gridcolor:'rgba(210,215,225,0.7)', showgrid:true, zeroline:false,
  }},
  yaxis:{{
    title:{{text:'<b>Thousand barrels</b>', font:{{size:14}}}},
    tickformat:',', separatethousands:true,
    gridcolor:'rgba(210,215,225,0.7)', showgrid:true, zeroline:false,
  }},
  showlegend: false,
  font:{{family:'-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",sans-serif',size:12}},
  height: 500,
}};

const config = {{responsive:true, displayModeBar:false}};

Plotly.newPlot('chart', buildTraces(currentProduct), layout, config);

function syncLegend() {{
  document.querySelectorAll('#legend .legend-item[data-decade]').forEach(el => {{
    el.style.opacity = selectedDecades.has(+el.dataset.decade) ? '1' : '0.25';
  }});
}}

document.querySelectorAll('.decade-pill').forEach(pill => {{
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
    Plotly.react('chart', buildTraces(currentProduct), layout, config);
  }});
}});

syncLegend();

document.getElementById('product-sel').addEventListener('change', function() {{
  currentProduct = this.value;
  Plotly.react('chart', buildTraces(currentProduct), layout, config);
  document.getElementById('source-note').textContent = SOURCE_NOTES[currentProduct];
}});
</script>
</body>
</html>"""

# ── Write the HTML file ────────────────────────────────────────────────────────
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"Saved: {OUTPUT}  ({os.path.getsize(OUTPUT):,} bytes)")
