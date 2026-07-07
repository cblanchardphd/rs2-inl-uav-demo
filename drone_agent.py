"""RS2 Drone Agent — runs on each Raspberry Pi

On startup:
  - Reads drone identity config from drone_config.json (or uses hostname)
  - Creates an RS2 Identity Object and writes it to the local audit log
  - Listens on TCP port 9200 for commands from the ground station

Commands (line-delimited, sent by ground_station.py):
  STATUS   — returns current identity + revocation status as JSON
  REVOKE   — issues an RS2 Revocation Event, returns it as JSON, marks drone revoked

Usage:
    python drone_agent.py

Configure identity before running:
    Edit drone_config.json with this drone's ID and governing authority.
"""

import json
import os
import socket
import sys
from datetime import datetime, timezone

# ---- Locate RS2 modules -----------------------------------------------------
# The RS2 identity/revocation constructors ship bundled in ./rs2.
_HERE = os.path.dirname(os.path.abspath(__file__))
_RS2_LOCAL = os.path.join(_HERE, "rs2")

if os.path.isdir(_RS2_LOCAL):
    sys.path.insert(0, _RS2_LOCAL)
else:
    sys.exit("RS2 modules not found — expected the bundled ./rs2 package next to this script.")

from identity.constructors import new_identity
from revocation.constructors import new_revocation_event, new_scope, new_temporal
from audit_log import AuditLog

# ---- Constants --------------------------------------------------------------
PORT = 9200
CONFIG_FILE = os.path.join(_HERE, "drone_config.json")
DEFAULT_AUTHORITY = "urn:liverion:authority:inl-uav-center"
DEFAULT_JURISDICTION = "US-ID"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    # Fall back to hostname
    import platform
    return {
        "drone_id": platform.node(),
        "governing_authority": DEFAULT_AUTHORITY,
        "jurisdiction": DEFAULT_JURISDICTION,
    }


def main():
    cfg = _load_config()
    drone_id = cfg["drone_id"]
    authority = cfg.get("governing_authority", DEFAULT_AUTHORITY)
    jurisdiction = cfg.get("jurisdiction", DEFAULT_JURISDICTION)

    log_path = os.path.join(_HERE, "logs", f"{drone_id}_audit.json")
    log = AuditLog(log_path)

    # Register this drone's identity on startup
    identity = new_identity(
        rs2_version="0.1",
        identity_id=drone_id,
        governing_authority=authority,
        lifecycle_state="active",
        jurisdiction=jurisdiction,
        metadata={"platform": "UAV", "operator": "INL-UAV-Center"},
    )
    identity_dict = json.loads(identity.to_canonical_json())
    log.record_identity_registered(identity_dict)

    revocation_dict = None  # set when REVOKE is received

    print(f"[RS2 Drone Agent] {drone_id} online")
    print(f"  Identity registered | Authority: {authority}")
    print(f"  Listening on port {PORT}")
    print(f"  Log: {log_path}")

    # TCP server — one connection at a time (demo-grade)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PORT))
    srv.listen(5)

    while True:
        conn, addr = srv.accept()
        with conn:
            data = conn.recv(1024).decode("utf-8").strip()
            cmd = data.upper()

            if cmd == "STATUS":
                resp = {
                    "drone_id": drone_id,
                    "status": "REVOKED" if revocation_dict else "ACTIVE",
                    "identity": identity_dict,
                    "revocation": revocation_dict,
                }
                conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))

            elif cmd == "REVOKE":
                if revocation_dict:
                    resp = {
                        "drone_id": drone_id,
                        "status": "ALREADY_REVOKED",
                        "revocation": revocation_dict,
                    }
                else:
                    now = _utc_now()
                    scope = new_scope(
                        jurisdictions=[jurisdiction],
                        object_types=["identity"],
                    )
                    temporal = new_temporal(effective_at=now)
                    rev = new_revocation_event(
                        rs2_version="0.1",
                        revocation_id=f"rev-{drone_id}-{now[:10]}",
                        issuing_authority=authority,
                        targets=[drone_id],
                        scope=scope,
                        temporal=temporal,
                        governance_envelope="urn:liverion:envelope:inl-uav-demo",
                        metadata={"reason": "ground station command", "issued_from": str(addr[0])},
                    )
                    revocation_dict = json.loads(rev.to_canonical_json())
                    log.record_revocation_issued(revocation_dict)
                    print(f"  [REVOKED] {drone_id} — command from {addr[0]}")
                    resp = {
                        "drone_id": drone_id,
                        "status": "REVOKED",
                        "revocation": revocation_dict,
                        "note": "fly but not lie — drone continues flight; RS2 identity is dead",
                    }
                conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))

            else:
                conn.sendall((json.dumps({"error": f"unknown command: {data}"}) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
