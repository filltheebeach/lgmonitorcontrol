$venvPython = [System.IO.Path]::Combine($PSScriptRoot, '..', '.venv', 'Scripts', 'python.exe')
if (-not (Test-Path $venvPython)) {
  Write-Error "Virtual environment Python not found at $venvPython"
  exit 1
}

$port = 8123
$owner = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
if ($owner) {
  Write-Warning "Port $port is in use by PID $owner - stopping it"
  Stop-Process -Id $owner -Force
  Start-Sleep 2
}

& $venvPython -m pip install fastapi uvicorn > $null

# Retry loop in case Windows keeps the port in TIME_WAIT
$maxRetries = 5
for ($i = 0; $i -lt $maxRetries; $i++) {
  $proc = Start-Process -FilePath $venvPython -WindowStyle Hidden -PassThru -ArgumentList @(
    "-m", "uvicorn", "server.app:app",
    "--host", "127.0.0.1",
    "--port", $port,
    "--app-dir", (Split-Path -Parent $PSScriptRoot)
  )
  Start-Sleep 2
  $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
  if ($conn) {
    Write-Host "Server started on port $port"
    exit 0
  }
  if ($proc.HasExited) {
    Write-Warning "Server exited (attempt $($i+1)/$maxRetries) - retrying..."
    Start-Sleep 2
  }
}

Write-Error "Failed to start server after $maxRetries attempts"
exit 1
