"""RS2 Ground Station — runs on operator's laptop

Connects to drone agents over WiFi, displays status, issues revocations.

Usage:
    python ground_station.py <drone_ip_1> <drone_ip_2> ...

Example:
    python ground_station.py 192.168.1.101 192.168.1.102 192.168.1.103

Interactive commands:
    status          — poll all drones and print status table
    revoke <id>     — revoke a drone by its drone_id (e.g. revoke drone-002)
    log             — print the ground station audit log
    quit            — exit
"""

import json
import os
import socket
import sys
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(_HERE, "logs", "ground_station_audit.json")

# ---- Locate audit_log -------------------------------------------------------
sys.path.insert(0, _HERE)
from audit_log import AuditLog


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _send_command(ip: str, port: int, cmd: str, timeout: float = 5.0) -> dict:
    try:
        with socket.create_connection((ip, port), timeout=timeout) as s:
            s.sendall((cmd + "\n").encode("utf-8"))
            data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if data.endswith(b"\n"):
                    break
        return json.loads(data.decode("utf-8").strip())
    except Exception as e:
        return {"error": str(e), "ip": ip}


def _status_table(drones: dict) -> str:
    lines = ["\n  Drone Status"]
    lines.append("  " + "-" * 52)
    for drone_id, info in drones.items():
        ip = info["ip"]
        status = info.get("status", "UNREACHABLE")
        marker = "*** REVOKED ***" if status == "REVOKED" else status
        lines.append(f"  {drone_id:<20} {ip:<18} {marker}")
    lines.append("")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python ground_station.py <drone_ip_1> <drone_ip_2> ...")
        sys.exit(1)

    drone_ips = sys.argv[1:]
    port = 9200
    log = AuditLog(LOG_PATH)

    # Initial status poll — discover drone IDs
    print("\n" + "=" * 60)
    print("RS2 Ground Station — INL UAV Demo")
    print("Liverion Corp. | Risk-Surface Reduction Substrate (RS2)")
    print("=" * 60)
    print(f"\nPolling {len(drone_ips)} drone(s)...\n")

    drones: dict = {}  # drone_id -> {ip, status, ...}
    for ip in drone_ips:
        resp = _send_command(ip, port, "STATUS")
        if "error" in resp:
            print(f"  {ip}  UNREACHABLE — {resp['error']}")
            drones[ip] = {"ip": ip, "status": "UNREACHABLE"}
        else:
            drone_id = resp.get("drone_id", ip)
            drones[drone_id] = {"ip": ip, "status": resp.get("status", "UNKNOWN"), "last": resp}
            print(f"  {drone_id}  ({ip})  {resp.get('status')}")

    print(_status_table(drones))

    # Interactive loop
    while True:
        try:
            raw = input("ground> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "quit":
            print("Exiting.")
            break

        elif cmd == "status":
            for drone_id, info in drones.items():
                if info["status"] == "UNREACHABLE":
                    continue
                resp = _send_command(info["ip"], port, "STATUS")
                if "error" not in resp:
                    drones[drone_id]["status"] = resp.get("status", "UNKNOWN")
                    drones[drone_id]["last"] = resp
            print(_status_table(drones))

        elif cmd == "revoke":
            if len(parts) < 2:
                print("  Usage: revoke <drone_id>")
                continue
            target_id = parts[1]
            if target_id not in drones:
                print(f"  Unknown drone: {target_id}")
                print(f"  Known drones: {', '.join(drones.keys())}")
                continue
            info = drones[target_id]
            if info["status"] == "REVOKED":
                print(f"  {target_id} is already revoked.")
                continue

            print(f"\n  Sending REVOKE to {target_id} ({info['ip']})...")
            resp = _send_command(info["ip"], port, "REVOKE")
            if "error" in resp:
                print(f"  ERROR: {resp['error']}")
            else:
                drones[target_id]["status"] = resp.get("status", "REVOKED")
                drones[target_id]["last"] = resp
                rev = resp.get("revocation", {})
                log.record_revocation_issued(rev)
                print(f"\n  REVOKED: {target_id}")
                print(f"  {resp.get('note', '')}")
                print(f"\n  Revocation Event JSON:")
                print("  " + json.dumps(rev, indent=2).replace("\n", "\n  "))
                print(_status_table(drones))

        elif cmd == "log":
            print(log.dump())

        else:
            print(f"  Unknown command: {raw}")
            print("  Commands: status | revoke <drone_id> | log | quit")


if __name__ == "__main__":
    main()
