# Publishes petroleum_seasonality_v2_viz.html to the Data4ThePeople/embeds repo.
# Usage:
#   .\publish_embed.ps1
#   .\publish_embed.ps1 -Message "week 29, data up to 7/17/26"

param(
    [string]$Message
)

$ErrorActionPreference = "Stop"

$source = "C:\Users\amand\Workspace\D4TP\crude_oil\exploration\petroleum_seasonality_v2_viz.html"
$embeds = "C:\Users\amand\Workspace\D4TP\embeds"
$file   = "petroleum_seasonality_v2_viz.html"

if (-not $Message) {
    $Message = "petroleum seasonality viz update ($(Get-Date -Format yyyy-MM-dd))"
}

Write-Host "Pulling latest from embeds repo..."
git -C $embeds pull
if ($LASTEXITCODE -ne 0) { throw "git pull failed - resolve the issue in $embeds and rerun" }

Copy-Item $source (Join-Path $embeds $file) -Force

$changed = git -C $embeds status --porcelain -- $file
if (-not $changed) {
    Write-Host "Embeds repo already has this version of $file - nothing to publish."
    exit 0
}

git -C $embeds add $file
git -C $embeds commit -m $Message
if ($LASTEXITCODE -ne 0) { throw "git commit failed" }

git -C $embeds push
if ($LASTEXITCODE -ne 0) { throw "git push failed - run 'git -C $embeds pull' then 'git -C $embeds push'" }

Write-Host "Published $file to Data4ThePeople/embeds: $Message"
