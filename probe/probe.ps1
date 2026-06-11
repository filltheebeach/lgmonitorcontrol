param(
  [string]$Export = "mine.txt",
  [string]$OutProfile = "server/monitor-profile.full.json",
  [string]$OutReport = "capability-report.md"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$venvPython = [System.IO.Path]::Combine($projectRoot, ".venv", "Scripts", "python.exe")

if (-not (Test-Path $venvPython)) {
  Write-Error "Virtual environment Python not found at $venvPython"
  exit 1
}

$Export = if ([System.IO.Path]::IsPathRooted($Export)) { $Export } else { Join-Path $projectRoot $Export }
$OutProfile = if ([System.IO.Path]::IsPathRooted($OutProfile)) { $OutProfile } else { Join-Path $projectRoot $OutProfile }
$OutReport = if ([System.IO.Path]::IsPathRooted($OutReport)) { $OutReport } else { Join-Path $projectRoot $OutReport }

Write-Host "Running probe: export=$Export -> profile=$OutProfile report=$OutReport"
& $venvPython (Join-Path $scriptDir "probe.py") --export "$Export" --out-profile "$OutProfile" --out-report "$OutReport"

if ($LASTEXITCODE -eq 0) {
  Write-Host "Done."
} else {
  Write-Error "Probe failed (exit $LASTEXITCODE)"
}
