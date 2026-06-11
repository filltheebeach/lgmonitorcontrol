# LG Monitor Control

A local API server and toolchain for controlling an LG HDR WQHD monitor over DDC/CI (via ControlMyMonitor) and LG OnScreen Control CLI (OSCCLI). Includes a capability probe, live OSD change logger, and a web UI.

## Architecture

```
probe/probe.py          # CSV export → monitor profile JSON + capability report
probe/probe.ps1         # PowerShell wrapper for probe.py
probe/monitor-osd-polling-logger.ps1  # Live OSD change polling logger

server/app.py           # FastAPI server — REST API wrapping ControlMyMonitor + OSCCLI
server/monitor-profile.full.json  # Canonical capability model (57 VCP controls)

ui/index.html           # Local web UI for testing controls

windows-service/run-local.ps1  # Quick launcher for the API server

config/config.json      # Runtime config (tool paths, monitor string, OSC display ID)
config/config.example.json
```

## Requirements

- Python 3.10+ (venv at `.venv/`)
- [ControlMyMonitor](https://www.nirsoft.net/utils/control_my_monitor.html) (NirSoft) — DDC/CI VCP read/write
- LG OnScreen Control (`OSCCLI.exe`) — LG-specific OSC commands
- Virtual environment with FastAPI + Uvicorn (auto-installed by `run-local.ps1`)

## Setup

1. Clone the repo and create the venv:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Edit `config/config.json` with your paths:
   ```json
   {
     "control_my_monitor": "C:\\path\\to\\ControlMyMonitor.exe",
     "osc_cli": "C:\\Program Files (x86)\\LG Electronics\\OnScreen Control\\bin\\OSCCLI.exe",
     "monitor": "\\\\.\\DISPLAY2\\Monitor0",
     "osc_display_id": 2,
     "verify_after_write": true,
     "verify_delay_ms": 300,
     "host": "127.0.0.1",
     "port": 8123
   }
   ```

   The `monitor` string must match what ControlMyMonitor shows in its dropdown. The `osc_display_id` is the ID from `OSCCLI.exe -c list`.

3. Generate the capability profile from your ControlMyMonitor CSV export:
   ```powershell
   .\probe\probe.ps1 -Export "LG HDR WQHD.csv"
   ```

4. Start the server:
   ```powershell
   .\windows-service\run-local.ps1
   ```

5. Open `http://127.0.0.1:8123/` — the server serves the UI directly.

## API Reference

Base URL: `http://127.0.0.1:8123`

### `GET /api/monitors`

List detected monitors and transport info.

```json
{
  "monitors": [{
    "id": "LG HDR WQHD",
    "name": "LG HDR WQHD",
    "version": "2",
    "transport": {
      "controlmymonitor": "\\\\.\\DISPLAY2\\Monitor0",
      "osc_display_id": "2"
    }
  }]
}
```

### `GET /api/monitors/{monitor_id}/capabilities`

Full capability profile — all 57 VCP controls with type, range/enum values, safe class, and labels.

### `GET /api/monitors/{monitor_id}/state`

Read current values of all readable VCP controls from the physical monitor.

```json
{
  "monitor": "LG HDR WQHD",
  "state": {
    "10": 100,
    "12": 70,
    "60": 0,
    ...
  }
}
```

### `POST /api/monitors/{monitor_id}/vcp`

Write a VCP code value.

```json
{
  "code": "10",
  "value": 75
}
```

Response includes `verified: true/false` if `verify_after_write` is enabled (reads back the value after a configurable delay).

### `POST /api/monitors/{monitor_id}/osc`

Send an LG OSC CLI command.

```json
{
  "command": "brightness",
  "option": "set",
  "value": 70
}
```

## Probe

The probe converts a ControlMyMonitor CSV export into the canonical `monitor-profile.full.json`:

```powershell
.\probe\probe.ps1 -Export "LG HDR WQHD.csv" -OutProfile server/monitor-profile.full.json -OutReport capability-report.md
```

It auto-detects:
- **Range** controls (brightness, contrast, volume, etc.)
- **Enum** controls (picture mode, aspect ratio, response time, etc.) — parses value labels from notes
- **Read-only** / **Write-only** controls
- Safe class per VCP code:
  - `safe_read` — read-only informational
  - `safe_write_restore` — standard writable controls
  - `experimental` — vendor-specific (six-axis color, black stabilizer, local dimming)
  - `manual_only` — input select, OSD, controller ID
  - `blocked` — factory settings lock

## Live OSD Logger

Poll a watch list of VCP codes and log changes while you navigate the monitor's OSD:

```powershell
.\probe\monitor-osd-polling-logger.ps1 -ControlMyMonitorPath "C:\path\to\ControlMyMonitor.exe"
```

- Press **M** to add a marker note (e.g., "entered picture menu")
- Press **Q** to quit and save session JSON
- Polling interval defaults to 300ms

## Web UI

The server serves `ui/index.html` directly at `http://127.0.0.1:8123/`.

- Sliders for range controls (brightness, contrast, etc.)
- Dropdowns for enum controls (picture mode, gamma, etc.)
- Read buttons for read-only controls
- Advanced mode toggle to expose `manual_only` / `experimental` controls
- Colored pills for safe class visibility
- Inline toast notifications for write results
- Automatically discovers the monitor ID from `/api/monitors`

## Important Notes

- **ControlMyMonitor** returns VCP values as the process exit code, not stdout. The driver reads `$LASTEXITCODE` / `returncode` accordingly.
- **Input switching** (VCP code 60) can make the controlling PC temporarily unable to address the monitor if it switches to a different source. Marked `manual_only` by default.
- **OSD overlay**: DDC/CI changes generally do NOT trigger the monitor's normal on-screen display. Settings apply silently — the behavior is model-specific.
- **OSCCLI** exposes only a subset of controls (brightness, contrast, picture mode, gamma, color temp, RGB gains, response time, FreeSync, black stabilizer). The rest are accessed via VCP through ControlMyMonitor.
- If the server fails to start with `address already in use`, kill the stale process:
  ```powershell
  Get-NetTCPConnection -LocalPort 8123 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
  ```
