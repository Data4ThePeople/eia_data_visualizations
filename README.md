# U.S. Petroleum Inventories — Weekly Seasonality

Exploratory analysis of weekly U.S. petroleum stock data from the Energy Information Administration (EIA), with interactive seasonality charts published via [Data 4 The People](https://www.data4thepeople.com).

## Project layout

| Location | Contents |
|----------|----------|
| `*.html` (repo root) | The live visualizations — they stay in the root so existing links keep working |
| `scripts/` | Build, publishing, and automation scripts (Python + PowerShell) |
| `media/` | Animated GIF exports of the visualizations |
| `docs/` | The WordPress embed guide |
| `archive/` | The original notebook/`.xls` workflow and v1–v3 charts (superseded) |

## Data

Four EIA weekly ending-stocks series, all in thousand barrels, fetched live from the EIA API on each build (endpoint `https://api.eia.gov/v2/petroleum/stoc/wstk/data/`; the API key lives in `.env` as `EIA_API_KEY`):

| Series | Description | Start |
|--------|-------------|-------|
| WCRSTUS1 | Crude Oil (incl. SPR) | Aug 1982 |
| WGTSTUS1 | Total Gasoline | Jan 1990 |
| WDISTUS1 | Distillate Fuel Oil (Diesel) | Aug 1982 |
| WCSSTUS1 | Crude Oil in Strategic Petroleum Reserve (SPR) | Aug 1982 |

Week number is computed as `(day-of-year − 1) ÷ 7 + 1`, capped at 52.

## Visualizations

Two build scripts generate three HTML files, all in the repo root; each opens directly in a browser (Plotly CDN, no server needed):

| Output (root) | Built by | Description |
|---------------|----------|-------------|
| `petroleum_seasonality_v2_viz.html` | `scripts/petroleum_seasonality_v2.py` | Seasonality chart: one line per year (1982–present) on a week 1–52 axis, current year in bold red, prior years colored by decade; product pills and decade toggles. This is the file published to the embeds repo. |
| `petroleum_seasonality_animation.html` | `scripts/petroleum_seasonality_v2.py` | The same chart with a replay animation that draws each year's line in chronological order, with speed controls. |
| `inventory_dot_strip_viz.html` | `scripts/inventory_dot_strip.py` | Dot strip: for a selected week of the year, every year is one dot — see the next section. |

**Dependencies:** `pandas`, `requests`, `python-dotenv` (installed in the repo's `.venv`).

Run the scripts from the repo root so the HTML lands in the root and `.env` resolves:

```powershell
python scripts\petroleum_seasonality_v2.py
python scripts\inventory_dot_strip.py
```

Earlier iterations — the `eia_exploration.ipynb` notebook, manual `.xls` downloads, and `petroleum_seasonality_v1/v2/v3.html` — are preserved in `archive/`.

## Dot strip — where the current year stands

`scripts/inventory_dot_strip.py` fetches the same four series via the EIA API and generates `inventory_dot_strip_viz.html`, a standalone dot-strip visualization. For a selected week of the year, every year (1982–present) is one dot on a horizontal axis in thousand barrels, so the current year can be compared against the full history at the same point in the season. Prior-year median, mean, and IQR are overlaid, and the header shows the current year's delta to the prior-year median and mean. Decade chips in the legend highlight a decade Tableau-style (everything else dims; the stats never change), a play button animates through the current year's weeks, and the week selector is capped at the latest week with current-year data. In dark mode the 2000s and 2020s dots use a lighter step of the same decade ramps to keep 3:1 contrast against the dark background.

In both build scripts, EIA API calls retry automatically on timeouts, dropped connections, and 5xx errors — the API is known to stall around release time. This file is **not** published by `publish_embed.ps1`.

## Automated weekly update

`scripts/weekly_update.ps1` automates the weekly refresh of this repo. It:

1. Pulls the latest from `origin`
2. Runs `petroleum_seasonality_v2.py` (builds the seasonality viz and the animation page) and `inventory_dot_strip.py`
3. Reads the latest data date from the build output and computes the week number (`(day-of-year − 1) ÷ 7 + 1`, capped at 52)
4. Commits the three HTML files with the message `week NN, data up to YYYY-MM-DD` and pushes — **only if** that data date is newer than the last `data up to ...` commit. If the EIA hasn't released new data yet, it exits without committing, so it's safe to run any time.

A Windows Scheduled Task named **"D4TP EIA weekly viz update"** runs it every **Wednesday at 2:00 PM** (local time, well after the EIA weekly release at 10:30 AM ET), with a **Thursday 2:00 PM fallback** for holiday weeks when the EIA delays the report a day. On a normal week the Thursday run finds nothing new and exits quietly. The task runs only while you're logged on; if the machine was off at trigger time, the run starts as soon as it's back.

Every run appends to `weekly_update.log` in the repo root (gitignored). If a week's commit didn't appear, check there first.

To run it manually (from the repo root):

```powershell
.\scripts\weekly_update.ps1          # full run: pull, regenerate, commit + push if new data
.\scripts\weekly_update.ps1 -NoPush  # same, but commit locally without pushing (for testing)
```

Publishing to the embeds repo is **not** part of the automation — run `scripts\publish_embed.ps1` yourself (next section). To chain it automatically with the same commit message, uncomment the `publish_embed.ps1` line near the bottom of `scripts\weekly_update.ps1`.

To inspect, change, or remove the schedule: Task Scheduler → **Task Scheduler Library** (top-level node) → "D4TP EIA weekly viz update". Right-click → **Run** fires it immediately as a test.

## Publishing

`scripts/publish_embed.ps1` publishes `petroleum_seasonality_v2_viz.html` to the local clone of the `Data4ThePeople/embeds` repo (`C:\Users\amand\Workspace\D4TP\embeds`). It pulls the embeds repo first (a colleague uploads to it daily), copies the file over, then commits and pushes. If the file is unchanged, it exits without committing.

### How to run it, step by step

1. **Open PowerShell.** Click the Start button (or press the Windows key), type `powershell`, and click **Windows PowerShell** in the results. A blue window with a blinking cursor will open — this is the terminal where you'll type the commands below. (Type each command at the prompt and press **Enter** to run it.)

2. **Go to this project's folder.** Copy and paste this command into the PowerShell window, then press **Enter**:

   ```powershell
   cd C:\Users\amand\Workspace\D4TP\crude_oil\exploration
   ```

   The prompt should now end with `...\crude_oil\exploration>`, confirming you're in the right folder.

3. **Run the script.** Type this and press **Enter**:

   ```powershell
   .\scripts\publish_embed.ps1
   ```

   (The `.\` at the start is required — it tells PowerShell to run the script from the current folder; the script itself lives in the `scripts` subfolder.)

   This uses an automatic commit message like `petroleum seasonality viz update (2026-07-29)`. To write your own message instead, run it like this:

   ```powershell
   .\scripts\publish_embed.ps1 -Message "week 29, data up to 7/17/26"
   ```

4. **Check that it worked.** You should see a final line like:

   ```
   Published petroleum_seasonality_v2_viz.html to Data4ThePeople/embeds: <your message>
   ```

   If you instead see `Embeds repo already has this version ... nothing to publish`, that's fine — it means the published copy is already up to date and nothing needed to change.

### Troubleshooting

- **"running scripts is disabled on this system"** — PowerShell is blocking scripts. Run this once, press **Enter**, and answer `Y` when prompted, then try step 3 again:

  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```

- **"git pull failed"** or **"git push failed"** — there's a conflict or connection problem with the embeds repo. Nothing has been published; ask for help before rerunning.
