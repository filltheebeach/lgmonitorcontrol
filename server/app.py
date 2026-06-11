from __future__ import annotations
import json, subprocess, time, logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "config.json"
PROFILE_PATH = ROOT / "server" / "monitor-profile.full.json"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("lgmonitor")

config: dict = {}
profile: dict = {}
controls: dict[str, dict] = {}
state_cache: dict[str, int | None] = {}

def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))

def reload_config():
    global config, profile, controls
    config = load_json(CONFIG_PATH)
    profile = load_json(PROFILE_PATH)
    controls = {c["source_key"]: c for c in profile.get("controls", [])}
    log.info("Config+profile loaded (%d controls)", len(controls))

def _warm_cache():
    cmm = _cmm()
    if not Path(cmm).exists():
        log.warning("ControlMyMonitor not found at %s — skipping cache warm", cmm)
        return
    readable = [c for c in profile.get("controls", []) if c["access"] in ("Read Only", "Read+Write")]
    log.info("Warming cache: reading %d VCP codes from monitor...", len(readable))
    ok = 0
    for c in readable:
        code = c["source_key"]
        val = _driver_get_vcp(code)
        state_cache[code] = val
        if val is not None:
            ok += 1
    log.info("Cache warm complete: %d/%d codes read successfully", ok, len(readable))

reload_config()

app = FastAPI(title="LG Monitor Control")

@app.get("/")
def index():
    return HTMLResponse((ROOT / "ui" / "index.html").read_text(encoding="utf-8"))

class VcpWrite(BaseModel):
    code: str
    value: int

class OscWrite(BaseModel):
    command: str
    option: str | None = None
    value: str | int | None = None

def _cmm() -> str:
    return config.get("control_my_monitor", "ControlMyMonitor.exe")

def _osc() -> str:
    return config.get("osc_cli", "OSCCLI.exe")

def _monitor() -> str:
    return config.get("monitor", "Primary")

def _osc_id() -> str:
    return str(config.get("osc_display_id", "2"))

def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)

@app.on_event("startup")
async def startup():
    reload_config()
    _warm_cache()

@app.get("/api/monitors")
def get_monitors():
    return {
        "monitors": [
            {
                "id": profile.get("monitor", "unknown"),
                "name": profile.get("monitor", "unknown"),
                "version": profile.get("version", ""),
                "transport": {
                    "controlmymonitor": _monitor(),
                    "osc_display_id": _osc_id(),
                },
            }
        ]
    }

@app.get("/api/monitors/{monitor_id}/capabilities")
def get_capabilities(monitor_id: str):
    return {"monitor": monitor_id, "controls": profile.get("controls", [])}

@app.get("/api/monitors/{monitor_id}/state")
def get_state(monitor_id: str, refresh: bool = False):
    if refresh:
        results = {}
        for c in profile.get("controls", []):
            code = c["source_key"]
            if c["access"] in ("Read Only", "Read+Write"):
                val = _driver_get_vcp(code)
                if val is not None:
                    state_cache[code] = val
                    results[code] = val
        return {"monitor": monitor_id, "state": results}
    return {"monitor": monitor_id, "state": {k: v for k, v in state_cache.items() if v is not None}}

@app.get("/api/monitors/{monitor_id}/vcp/{code}")
def read_vcp(monitor_id: str, code: str):
    code = code.upper()
    ctrl = controls.get(code)
    if not ctrl:
        raise HTTPException(404, f"Unknown VCP code: {code}")
    if ctrl["access"] not in ("Read Only", "Read+Write"):
        raise HTTPException(400, f"VCP code {code} is not readable ({ctrl['access']})")
    val = _driver_get_vcp(code)
    if val is None:
        raise HTTPException(502, f"Failed to read VCP code {code}")
    state_cache[code] = val
    return {"code": code, "value": val, "label": ctrl["label"]}

@app.post("/api/monitors/{monitor_id}/vcp")
def write_vcp(monitor_id: str, body: VcpWrite):
    code = body.code.upper()
    ctrl = controls.get(code)
    if not ctrl:
        raise HTTPException(404, f"Unknown VCP code: {code}")
    if ctrl["access"] not in ("Read+Write", "Write Only"):
        raise HTTPException(400, f"VCP code {code} is not writable ({ctrl['access']})")
    _validate(ctrl, body.value)
    _driver_set_vcp(code, body.value)
    state_cache[code] = body.value
    verified = None
    if config.get("verify_after_write", False):
        import time as _time
        _time.sleep(config.get("verify_delay_ms", 300) / 1000.0)
        readback = _driver_get_vcp(code)
        verified = readback == body.value if readback is not None else None
    return {"success": True, "code": code, "value": body.value, "verified": verified}

@app.post("/api/monitors/{monitor_id}/osc")
def write_osc(monitor_id: str, body: OscWrite):
    osc = _osc()
    if not Path(osc).exists():
        raise HTTPException(500, f"OSCCLI not found at {osc}")
    cmd = [osc, "-c", body.command, "-t", _osc_id(), "-o", body.option or "get"]
    if body.value is not None:
        cmd.append(str(body.value))
    r = _run(cmd)
    if r.returncode != 0:
        log.warning("OSC command failed: %s", r.stderr)
        return {"success": False, "error": r.stderr.strip() or "OSC command failed"}
    return {"success": True, "output": r.stdout.strip()}

def _validate(ctrl: dict, value: int):
    labels = ctrl.get("value_labels") or []
    if labels:
        allowed = {v["value"] for v in labels if "value" in v}
        if value not in allowed:
            raise HTTPException(400, f"Value {value} not allowed for {ctrl['id']}")
        return
    mn = ctrl.get("minimum_value")
    mx = ctrl.get("maximum_value")
    if mn is not None and value < mn:
        raise HTTPException(400, f"Value below minimum ({mn})")
    if mx is not None and value > mx:
        raise HTTPException(400, f"Value above maximum ({mx})")

def _driver_get_vcp(code: str) -> int | None:
    cmm = _cmm()
    if not Path(cmm).exists():
        return None
    r = _run([cmm, "/GetValue", _monitor(), code])
    # ControlMyMonitor returns the VCP value as the process exit code.
    # If stderr has content, assume it was an error.
    if r.stderr and r.returncode != 0:
        log.warning("ControlMyMonitor read error for %s: %s", code, r.stderr.strip())
        return None
    return r.returncode

def _driver_set_vcp(code: str, value: int):
    cmm = _cmm()
    if not Path(cmm).exists():
        raise HTTPException(500, f"ControlMyMonitor not found at {cmm}")
    r = _run([cmm, "/SetValue", _monitor(), code, str(value)])
    if r.returncode != 0:
        log.warning("SetValue failed: %s", r.stderr)
        raise HTTPException(500, f"SetValue failed: {r.stderr.strip()}")
