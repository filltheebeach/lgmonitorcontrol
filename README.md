# LG Monitor Control

A local API server and toolchain for controlling an LG HDR WQHD monitor over DDC/CI (via ControlMyMonitor) and LG OnScreen Control CLI (OSCCLI). Includes a capability probe, live OSD change logger, and a web UI.

**Key feature:** Switch between HDMI-1, HDMI-2, and DisplayPort inputs programmatically via the API or one-click buttons in the web UI.

## Architecture

```
probe/probe.py                    # CSV export → monitor profile JSON + capability report
probe/probe.ps1                   # PowerShell wrapper for probe.py
probe/monitor-osd-polling-logger.ps1  # Live OSD change polling logger

server/app.py                     # FastAPI server — REST API wrapping ControlMyMonitor + OSCCLI
server/monitor-profile.full.json  # Canonical capability model (57 VCP controls)

ui/index.html                     # Local web UI with dedicated input selector

windows-service/run-local.ps1     # Quick launcher for the API server

config/config.json                # Runtime config (tool paths, monitor string, OSC display ID)
config/config.example.json

capability-report.md              # Auto-generated markdown report from the probe
```

## Requirements

- Python 3.10+ (venv at `.venv/`)
- [ControlMyMonitor](https://www.nirsoft.net/utils/control_my_monitor.html) (NirSoft) — DDC/CI VCP read/write
- LG OnScreen Control (`OSCCLI.exe`) — LG-specific OSC commands
- Virtual environment with FastAPI + Uvicorn

## Setup

1. Clone the repo and create the venv:
   ```powershell
   git clone https://github.com/filltheebeach/lgmonitorcontrol.git
   cd lgmonitorcontrol
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

## Input Switching

The most frequently used feature. The web UI shows a dedicated **Input Source** card at the top with buttons for each available input:

- **HDMI-1** (VCP value 15)
- **HDMI-2** (VCP value 16)
- **DisplayPort** (VCP value 17)

To switch inputs programmatically:

```bash
curl -s -X POST http://127.0.0.1:8123/api/monitors/LG%20HDR%20WQHD/vcp \
  -H 'Content-Type: application/json' \
  -d '{"code": "60", "value": 15}'
```

The active input button is highlighted after a successful switch.

**Note:** Switching to an input that the controlling PC is not connected to will make the monitor temporarily unreachable via DDC/CI. The API call will still succeed (it sends the command before the switch takes effect), but subsequent reads/writes will fail until the PC's input is reselected.

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

Returns cached current values of all readable VCP controls. The cache is populated automatically during server startup (reads all 57 VCP codes before accepting requests). Add `?refresh=true` to force a fresh read from the physical monitor.

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

### `GET /api/monitors/{monitor_id}/vcp/{code}`

Read a single VCP control value.

```json
{
  "code": "10",
  "value": 100,
  "label": "Brightness"
}
```

### `POST /api/monitors/{monitor_id}/vcp`

Write a VCP code value. Returns `verified: true/false` if `verify_after_write` is enabled (reads back the value after a configurable delay).

```json
// Request
{ "code": "10", "value": 75 }

// Response
{ "success": true, "code": "10", "value": 75, "verified": true }
```

### `POST /api/monitors/{monitor_id}/osc`

Send an LG OSC CLI command.

```json
{
  "command": "brightness",
  "option": "set",
  "value": 70
}
```

## Web UI

The server serves `ui/index.html` directly at `http://127.0.0.1:8123/`.

- **Input selector** — prominent card at the top with HDMI-1, HDMI-2, DisplayPort buttons
- Sliders for range controls (brightness, contrast, volume) — with "Refresh" to read current value
- Dropdowns for enum controls (picture mode, gamma, input select, response time)
- Read buttons for read-only controls
- Advanced mode toggle to expose `manual_only` / `experimental` controls
- Colored pills for safe class visibility
- Inline toast notifications for write results (green for verified, orange for warning, red for errors)
- Automatically discovers the monitor ID from `/api/monitors`

## Probe

The probe converts a ControlMyMonitor CSV export into the canonical `monitor-profile.full.json`:

```powershell
.\probe\probe.ps1 -Export "LG HDR WQHD.csv" -OutProfile server/monitor-profile.full.json -OutReport capability-report.md
```

It auto-detects:
- **Range** controls (brightness, contrast, volume, etc.)
- **Enum** controls (picture mode, aspect ratio, response time, input select, etc.) — parses value labels from notes or uses hardcoded MCCS values for well-known codes (e.g., VCP 60 = Input Select)
- **Read-only** / **Write-only** controls
- Safe class per VCP code:
  - `safe_read` — read-only informational
  - `safe_write_restore` — standard writable controls (including input select)
  - `experimental` — vendor-specific (six-axis color, black stabilizer, local dimming)
  - `manual_only` — OSD, controller ID
  - `blocked` — factory settings lock

## Live OSD Logger

Poll a watch list of VCP codes and log changes while you navigate the monitor's OSD:

```powershell
.\probe\monitor-osd-polling-logger.ps1 -ControlMyMonitorPath "C:\path\to\ControlMyMonitor.exe"
```

- Press **M** to add a marker note (e.g., "entered picture menu")
- Press **Q** to quit and save session JSON
- Polling interval defaults to 300ms

## Startup Cache

On startup, the server automatically reads all readable VCP codes from the physical monitor (typically 50-53 out of 57) and caches them in memory. This means:

- The UI loads instantly with current values — no spinning or "?" placeholders
- The `/state` endpoint returns cached data without launching ControlMyMonitor per-request
- Subsequent reads (`GET /vcp/{code}`) and writes (`POST /vcp`) update the cache automatically
- Pass `?refresh=true` on `/state` to force a live re-read from the monitor

The warm-up takes ~10-20 seconds depending on how quickly ControlMyMonitor responds. The server logs progress: `"Warming cache: reading 53 VCP codes..."`.

## Important Notes

- **ControlMyMonitor** returns VCP values as the process exit code, not stdout. The driver reads `stdout.returncode` accordingly. Zero is a valid value (not an error).
- **Input switching** (VCP code 60): The write command is sent before the physical switch occurs. If you switch away from the PC's input, subsequent DDC/CI commands will fail until the PC's input is reselected (manually or via the last working API call).
- **OSD overlay**: DDC/CI changes generally do NOT trigger the monitor's normal on-screen display. Settings apply silently — behavior is model-specific.
- **OSCCLI** exposes only a subset of controls (brightness, contrast, picture mode, gamma, color temp, RGB gains, response time, FreeSync, black stabilizer). The rest are accessed via VCP through ControlMyMonitor.
- If the server fails to start with `address already in use`, kill the stale process:
  ```powershell
  Get-NetTCPConnection -LocalPort 8123 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
  ```
- The `run-local.ps1` launcher includes automatic port killing and a 5-attempt retry loop to handle Windows TIME_WAIT delays.
- Use `[System.IO.Path]::Combine()` for multi-segment paths in PowerShell scripts — `Join-Path` only accepts 2 arguments.
