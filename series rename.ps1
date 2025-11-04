<#
.SYNOPSIS
  Generic Anime Series Season Fixer & Renamer
.DESCRIPTION
  Combines multiple mislabelled season folders into correct seasons.
  Example:
    Current: 5 folders (12 eps each)
    True: 3 seasons (24, 12, 24)
  Script merges and renumbers accordingly.
#>

# Ask for root folder and new season episode counts
$root = Read-Host "Enter root folder path (e.g. D:\Video\Bungo Stray Dogs)"
$newSeasons = Read-Host "Enter true episode counts per season, separated by commas (e.g. 24,12,24)"
$newSeasons = $newSeasons -split "," | ForEach-Object { [int]($_.Trim()) }

# Collect all MKV files from all subfolders
$allFiles = Get-ChildItem -Path $root -Filter "*.mkv" -Recurse | Sort-Object FullName

if (-not $allFiles) {
    Write-Host "No MKV files found in $root" -ForegroundColor Red
    exit
}

Write-Host "`nFound $($allFiles.Count) episodes total.`n"

# Prepare season logic
$seasonData = @()
$startIndex = 0
for ($i = 0; $i -lt $newSeasons.Count; $i++) {
    $season = $i + 1
    $count = $newSeasons[$i]
    $seasonData += [PSCustomObject]@{
        Season = $season
        StartIndex = $startIndex
        EndIndex   = $startIndex + $count - 1
    }
    $startIndex += $count
}

# Confirm mapping
Write-Host "Season breakdown:" -ForegroundColor Cyan
foreach ($s in $seasonData) {
    Write-Host (" Season {0}: Episodes {1}–{2}" -f $s.Season, $s.StartIndex + 1, $s.EndIndex + 1)
}
Write-Host ""

# Confirm with user
$confirm = Read-Host "Proceed with renaming? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit
}

# Rename logic
for ($i = 0; $i -lt $allFiles.Count; $i++) {
    $file = $allFiles[$i]
    $seasonInfo = $seasonData | Where-Object { $i -ge $_.StartIndex -and $i -le $_.EndIndex }
    if ($null -eq $seasonInfo) { continue }

    $season = $seasonInfo.Season
    $episode = $i - $seasonInfo.StartIndex + 1

    if ($file.BaseName -match '\[(.*?)\]$') {
        $hash = $matches[1]
    } else {
        $hash = ""
    }

    $newDir = Join-Path $root ("Season {0}" -f $season)
    if (!(Test-Path $newDir)) { New-Item -ItemType Directory -Path $newDir | Out-Null }

    $newName = "[INDEX] {0} - S{1:D2}E{2:D2} [{3}]{4}" -f ($root.Split('\')[-1]), $season, $episode, $hash, $file.Extension
    $dest = Join-Path $newDir $newName

    Move-Item -LiteralPath $file.FullName -Destination $dest -Force
    Write-Host ("Moved → Season {0} Episode {1:D2}: {2}" -f $season, $episode, $file.Name)
}

Write-Host "`nAll files renamed and reorganised successfully!" -ForegroundColor Green
