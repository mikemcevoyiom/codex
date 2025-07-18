# Wipe-InfluxBucket.ps1
# This script deletes all data from a specified InfluxDB bucket but leaves the bucket and API tokens intact.

# ------------------------
# CONFIGURATION SECTION
# ------------------------

# InfluxDB connection details
$InfluxHost = "http://192.168.1.28:8086"
$Org = "Waterfall"
$Bucket = "Video_Convert"

# Optional: securely prompt for API token at runtime
$Token = Read-Host "Enter your InfluxDB API token"

# ------------------------
# DELETE CONFIRMATION
# ------------------------

Write-Host "`nWARNING: You are about to DELETE ALL DATA from bucket '$Bucket' in organization '$Org' at $InfluxHost."
$confirm = Read-Host "Type 'WIPE' to confirm"

if ($confirm -ne "WIPE") {
    Write-Host "Aborted. No data was deleted."
    exit
}

# ------------------------
# GET CURRENT UTC TIME
# ------------------------

$StopTime = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$StartTime = "1970-01-01T00:00:00Z"

# ------------------------
# EXECUTE DELETE
# ------------------------

Write-Host "`nDeleting data from $StartTime to $StopTime..."

influx delete `
  --host $InfluxHost `
  --org $Org `
  --bucket $Bucket `
  --start $StartTime `
  --stop $StopTime `
  --token $Token

Write-Host "`n✔ Bucket data wipe complete (bucket '$Bucket' remains intact)."
