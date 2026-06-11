from __future__ import annotations
import argparse, csv, json, re, sys
from pathlib import Path

SAFE_CLASS_MAP = {
    "0B": "safe_read", "52": "safe_read", "AC": "safe_read",
    "B6": "safe_read", "C0": "safe_read", "C6": "safe_read",
    "C9": "safe_read", "DF": "safe_read",
    "FA": "blocked",
    "60": "safe_write_restore", "C8": "manual_only", "CA": "manual_only",
    "CC": "manual_only", "F4": "manual_only", "FB": "manual_only",
    "4D": "experimental", "4E": "experimental", "4F": "experimental",
    "6C": "experimental", "6E": "experimental", "70": "experimental",
    "E4": "experimental", "E7": "experimental", "E8": "experimental",
    "E9": "experimental", "EA": "experimental", "EF": "experimental",
    "F8": "experimental", "F9": "experimental",
}

MCCS_INPUT_VALUES = {
    "01": "VGA-1",
    "02": "VGA-2",
    "03": "DVI-1",
    "04": "DVI-2",
    "0F": "HDMI-1",
    "10": "HDMI-2",
    "11": "DisplayPort-1",
    "12": "USB-C",
}

def detect_type(access: str, notes: str) -> str:
    if access == "Read Only":
        return "readonly"
    if access == "Write Only":
        return "writeonly"
    if notes and "=" in notes:
        parts = [p.strip() for p in re.split(r"[,;]", notes)]
        if any("=" in p for p in parts):
            return "enum"
    return "range"

def parse_enum_values(notes: str) -> list[dict]:
    if not notes:
        return []
    result = []
    for p in re.split(r"[,;]", notes):
        p = p.strip()
        m = re.match(r"(\d+)\s*=\s*(.+)", p)
        if m:
            result.append({"value": int(m.group(1)), "label": m.group(2).strip()})
    return result

def parse_csv(path: Path) -> list[dict]:
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    controls = []
    for r in rows:
        code = r.get("VCP Code", "").strip()
        name = r.get("VCP Code Name", "").strip()
        access = r.get("Read-Write", "").strip()
        cur_raw = r.get("Current Value", "").strip()
        max_raw = r.get("Maximum Value", "").strip()
        notes = (r.get("Possible Values / Meaning") or "").strip()

        cur_val = int(cur_raw) if cur_raw and cur_raw.lstrip("-").isdigit() else None
        max_val = int(max_raw) if max_raw and max_raw.lstrip("-").isdigit() else None

        ctype = detect_type(access, notes)
        enum_vals = parse_enum_values(notes) if ctype == "enum" else []
        if code == "60":
            ctype = "enum"
            enum_vals = [{"value": int(k, 16), "label": v} for k, v in MCCS_INPUT_VALUES.items()]
        safe_class = SAFE_CLASS_MAP.get(code, "safe_write_restore")

        controls.append({
            "id": f"vcp.{code}",
            "source": "vcp",
            "source_key": code,
            "label": name,
            "access": access,
            "type": ctype,
            "current_value": cur_val,
            "maximum_value": max_val,
            "value_labels": enum_vals,
            "notes": notes,
            "safe_class": safe_class,
        })
    return controls

def generate_report(controls: list[dict], monitor_name: str) -> str:
    lines = [f"# Capability Report: {monitor_name}", ""]
    lines.append(f"Total controls: {len(controls)}")
    lines.append("")
    lines.append("| Code | Name | Access | Type | Max | Safe Class |")
    lines.append("|------|------|--------|------|-----|------------|")
    for c in controls:
        lines.append(
            f"| {c['source_key']} | {c['label']} | {c['access']} "
            f"| {c['type']} | {c['maximum_value'] or '-'} | {c['safe_class']} |"
        )
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(description="LG Monitor capability probe/mapper")
    ap.add_argument("--export", required=True, help="Path to CSV export from ControlMyMonitor")
    ap.add_argument("--out-profile", default="server/monitor-profile.full.json", help="Output profile JSON")
    ap.add_argument("--out-report", default="capability-report.md", help="Output capability report")
    args = ap.parse_args()

    csv_path = Path(args.export)
    if not csv_path.exists():
        print(f"Error: export file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    controls = parse_csv(csv_path)
    profile = {
        "monitor": "LG HDR WQHD",
        "version": "2",
        "controls": controls,
        "approved_first_controls": [
            "10", "12", "14", "16", "18", "1A",
            "60", "62", "E4", "EB", "F7"
        ],
    }

    out_profile = Path(args.out_profile)
    out_profile.parent.mkdir(parents=True, exist_ok=True)
    out_profile.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Profile written: {out_profile} ({len(controls)} controls)")

    report = generate_report(controls, profile["monitor"])
    out_report = Path(args.out_report)
    out_report.write_text(report, encoding="utf-8")
    print(f"Report written: {out_report}")

if __name__ == "__main__":
    main()
