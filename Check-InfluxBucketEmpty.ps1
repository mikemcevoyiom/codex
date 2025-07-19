# Check-InfluxBucketEmpty.ps1
# Confirms if the InfluxDB bucket is empty after a wipe

# Configuration
$InfluxHost = "http://192.168.1.28:8086"
$Org = "Waterfall"
$Bucket = "Video_Convert"
$Token = Read-Host "Enter your InfluxDB API token"

Write-Host "`nChecking if bucket '$Bucket' contains any remaining data..."

# Define the query as a single string
$query = @"
from(bucket: "$Bucket")
  |> range(start: -90d)
  |> limit(n:1)
"@

# Run query
influx query `
  --org $Org `
  --host $InfluxHost `
  --token $Token `
  $query
