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

## Publishing

`publish_embed.ps1` publishes `petroleum_seasonality_v2_viz.html` to the local clone of the `Data4ThePeople/embeds` repo (`C:\Users\amand\Workspace\D4TP\embeds`). It pulls the embeds repo first (a colleague uploads to it daily), copies the file over, then commits and pushes. If the file is unchanged, it exits without committing.

### How to run it, step by step

1. **Open PowerShell.** Click the Start button (or press the Windows key), type `powershell`, and click **Windows PowerShell** in the results. A blue window with a blinking cursor will open — this is the terminal where you'll type the commands below. (Type each command at the prompt and press **Enter** to run it.)

2. **Go to this project's folder.** Copy and paste this command into the PowerShell window, then press **Enter**:

   ```powershell
   cd C:\Users\amand\Workspace\D4TP\crude_oil\exploration
   ```

   The prompt should now end with `...\crude_oil\exploration>`, confirming you're in the right folder.

3. **Run the script.** Type this and press **Enter**:

   ```powershell
   .\publish_embed.ps1
   ```

   (The `.\` at the start is required — it tells PowerShell to run the script from the current folder.)

   This uses an automatic commit message like `petroleum seasonality viz update (2026-07-29)`. To write your own message instead, run it like this:

   ```powershell
   .\publish_embed.ps1 -Message "week 29, data up to 7/17/26"
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
