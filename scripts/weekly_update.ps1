# Weekly EIA visualization update.
#
# Regenerates the three HTML visualizations, and if the EIA data is newer than
# the last published week, commits them with "week NN, data up to YYYY-MM-DD"
# and pushes to origin. Safe to run any time: when no new data has been
# released yet (e.g. a holiday-delayed report), it logs and exits without
# committing, so the Thursday fallback trigger is a no-op after a successful
# Wednesday run.
#
# Usage (from the repo root):
#   .\scripts\weekly_update.ps1           # normal (commit + push)
#   .\scripts\weekly_update.ps1 -NoPush   # commit locally but don't push (for testing)
#
# Scheduled via Task Scheduler task "D4TP EIA weekly viz update".
# Log: weekly_update.log in the repo root (gitignored).

param(
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"

# This script lives in scripts\; the repo root is one level up.
$repo = Split-Path $PSScriptRoot -Parent
$py   = Join-Path $repo ".venv\Scripts\python.exe"
$log  = Join-Path $repo "weekly_update.log"

$htmlFiles = @(
    "petroleum_seasonality_v2_viz.html",
    "petroleum_seasonality_animation.html",
    "inventory_dot_strip_viz.html"
)

function Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $msg"
    Write-Host $line
    Add-Content -Path $log -Value $line -Encoding utf8
}

# GitHub over SSH occasionally drops connections; retry network git commands.
function GitNet {
    param([string[]]$GitArgs)
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        git -C $repo @GitArgs
        if ($LASTEXITCODE -eq 0) { return }
        if ($attempt -lt 3) {
            Log "git $($GitArgs -join ' ') failed (exit $LASTEXITCODE), retrying in 30s (attempt $attempt/3)"
            Start-Sleep -Seconds 30
        }
    }
    throw "git $($GitArgs -join ' ') failed after 3 attempts (exit $LASTEXITCODE)"
}

try {
    Set-Location $repo
    Log "=== weekly update started ==="

    # Pull first — the repo gets pushes from elsewhere (see the merge commits).
    GitNet @("pull", "--no-rebase")

    # Regenerate the visualizations.
    Log "running petroleum_seasonality_v2.py"
    & $py (Join-Path $repo "scripts\petroleum_seasonality_v2.py")
    if ($LASTEXITCODE -ne 0) { throw "petroleum_seasonality_v2.py failed (exit $LASTEXITCODE)" }

    Log "running inventory_dot_strip.py"
    $dotOut = & $py (Join-Path $repo "scripts\inventory_dot_strip.py")
    if ($LASTEXITCODE -ne 0) { throw "inventory_dot_strip.py failed (exit $LASTEXITCODE)" }
    $dotOut | ForEach-Object { Log "  $_" }

    # Latest data date, from the script's own sanity-check line.
    $m = ($dotOut | Select-String "Last available week of data: (\d{4}-\d{2}-\d{2})")
    if (-not $m) { throw "could not find the data date in inventory_dot_strip.py output" }
    $dataDate = $m.Matches[0].Groups[1].Value
    $d = [datetime]::ParseExact($dataDate, "yyyy-MM-dd", $null)

    # Week number, same formula as the Python scripts: (day-of-year - 1) / 7 + 1, capped at 52.
    $week = [math]::Min(52, [math]::Floor(($d.DayOfYear - 1) / 7) + 1)

    # Only publish when the data is newer than the last "data up to ..." commit.
    $lastMsg = git -C $repo log --grep="data up to" -1 --format=%s
    if ($lastMsg -match "data up to (\d{4}-\d{2}-\d{2})") {
        $lastDate = [datetime]::ParseExact($Matches[1], "yyyy-MM-dd", $null)
        if ($d -le $lastDate) {
            Log "no new data yet (latest is $dataDate, already published) - nothing to do"
            exit 0
        }
    }

    $changed = git -C $repo status --porcelain -- $htmlFiles
    if (-not $changed) {
        Log "data date $dataDate is new but no HTML changed - nothing to commit"
        exit 0
    }

    $message = "week $week, data up to $dataDate"
    git -C $repo add -- $htmlFiles
    git -C $repo commit -m $message
    if ($LASTEXITCODE -ne 0) { throw "git commit failed (exit $LASTEXITCODE)" }
    Log "committed: $message"

    if ($NoPush) {
        Log "-NoPush set: skipping push"
    } else {
        GitNet @("push")
        Log "pushed to origin"
    }

    # Optional: also publish the seasonality viz to the embeds repo.
    # & (Join-Path $repo "scripts\publish_embed.ps1") -Message $message

    Log "=== weekly update finished ==="
    exit 0
}
catch {
    Log "FAILED: $_"
    exit 1
}
