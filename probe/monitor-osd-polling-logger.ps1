param(
  [string]$ControlMyMonitorPath = "ControlMyMonitor.exe",
  [string]$InputExport = "mine.txt",
  [string]$OutSession = "monitor-osd-session.json",
  [int]$PollMs = 300
)

# Resolve paths relative to project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$ControlMyMonitorPath = if ([System.IO.Path]::IsPathRooted($ControlMyMonitorPath)) { $ControlMyMonitorPath } else { Join-Path $projectRoot $ControlMyMonitorPath }
$OutSession = if ([System.IO.Path]::IsPathRooted($OutSession)) { $OutSession } else { Join-Path $projectRoot $OutSession }

if (-not (Test-Path $ControlMyMonitorPath)) {
  Write-Error "ControlMyMonitor not found at $ControlMyMonitorPath"
  exit 1
}

# Monitor string from config or default
$configPath = Join-Path $projectRoot "config" "config.json"
$monitorString = "Primary"
if (Test-Path $configPath) {
  $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
  if ($cfg.monitor) { $monitorString = $cfg.monitor }
}

# Watch list from CSV export if available, else default
$codes = @(
  "10","12","14","15","4D","4E","4F","60","62",
  "C8","CA","CC","D6","E4","EB","F5","F6","F7","F8","F9","FE"
)

$state = @{}
$events = @()

Write-Host "Monitoring $monitorString - Polling $($codes.Count) codes every ${PollMs}ms"
Write-Host "Press Q to quit, M to add a marker note."

while ($true) {
  foreach ($c in $codes) {
    $null = & $ControlMyMonitorPath "/GetValue" $monitorString $c 2>$null
    $v = $LASTEXITCODE
    if (-not $state.ContainsKey($c)) { $state[$c] = $v; continue }
    if ($state[$c] -ne $v) {
      $events += [PSCustomObject]@{
        ts   = (Get-Date).ToString("o")
        code = $c
        old  = $state[$c]
        new  = $v
      }
      Write-Host "[$(Get-Date -Format HH:mm:ss)] ${c}: $($state[$c]) -> $v"
      $state[$c] = $v
    }
  }
  if ([Console]::KeyAvailable) {
    $k = [Console]::ReadKey($true).Key
    if ($k -eq "Q") { break }
    if ($k -eq "M") {
      $note = Read-Host "Marker note"
      $events += [PSCustomObject]@{ ts = (Get-Date).ToString("o"); marker = $note }
      Write-Host "  -> marker saved"
    }
  }
  Start-Sleep -Milliseconds $PollMs
}

$events | ConvertTo-Json -Depth 5 | Set-Content $OutSession -Encoding UTF8
Write-Host "Session saved to $OutSession ($($events.Count) events)"
