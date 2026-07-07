"""RS2 INL UAV Demo — Local (single machine, no hardware required)

Demonstrates the full RS2 scenario on one machine:
  1. Register three drone identities
  2. Issue a revocation against drone-002
  3. Print the complete audit log as JSON

Run:
    python demo_local.py

No network, no Raspberry Pi, no dependencies beyond Python 3.8+.
"""

import json
import os
import sys

# ---- Locate RS2 modules -----------------------------------------------------
# The RS2 identity/revocation constructors ship bundled in ./rs2. Prefer them so
# the demo runs from a clean clone with zero setup.
_HERE = os.path.dirname(os.path.abspath(__file__))
_RS2_LOCAL = os.path.join(_HERE, "rs2")

if os.path.isdir(_RS2_LOCAL):
    sys.path.insert(0, _RS2_LOCAL)
else:
    sys.exit("RS2 modules not found — expected the bundled ./rs2 package next to this script.")

from identity.constructors import new_identity          # noqa: E402
from revocation.constructors import (                   # noqa: E402
    new_revocation_event, new_scope, new_temporal,
)
from audit_log import AuditLog                          # noqa: E402

# ---- Config -----------------------------------------------------------------
AUTHORITY = "urn:liverion:authority:inl-uav-center"
JURISDICTION = "US-ID"
LOG_PATH = os.path.join(_HERE, "logs", "demo_local_audit.json")

DRONES = ["drone-001", "drone-002", "drone-003"]
REVOKE_TARGET = "drone-002"

# ---- Run --------------------------------------------------------------------

def main():
    log = AuditLog(LOG_PATH)

    print("=" * 60)
    print("RS2 INL UAV Demo — Local Simulation")
    print("Liverion Corp. | Risk-Surface Reduction Substrate (RS2)")
    print("=" * 60)

    # Step 1: Register drone identities
    print(f"\n[STEP 1] Registering {len(DRONES)} drone identities...\n")
    identities = {}
    for drone_id in DRONES:
        identity = new_identity(
            rs2_version="0.1",
            identity_id=drone_id,
            governing_authority=AUTHORITY,
            lifecycle_state="active",
            jurisdiction=JURISDICTION,
            metadata={"platform": "UAV", "operator": "INL-UAV-Center"},
        )
        identities[drone_id] = identity
        entry = log.record_identity_registered(json.loads(identity.to_canonical_json()))
        print(f"  REGISTERED  {drone_id}")
        print(f"  {identity.to_canonical_json()}\n")

    # Step 2: Issue revocation against target drone
    print(f"\n[STEP 2] Issuing revocation against {REVOKE_TARGET}...")
    print(f"  Drone {REVOKE_TARGET} will continue to fly but its RS2 identity")
    print(f"  is now revoked. It cannot authenticate. It cannot be trusted.")
    print(f"  Fly — but not lie.\n")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    scope = new_scope(jurisdictions=[JURISDICTION], object_types=["identity"])
    temporal = new_temporal(effective_at=now)
    revocation = new_revocation_event(
        rs2_version="0.1",
        revocation_id="rev-inl-demo-001",
        issuing_authority=AUTHORITY,
        targets=[REVOKE_TARGET],
        scope=scope,
        temporal=temporal,
        governance_envelope="urn:liverion:envelope:inl-uav-demo",
        metadata={"reason": "INL RS2 demonstration revocation"},
    )
    log.record_revocation_issued(json.loads(revocation.to_canonical_json()))
    print(f"  REVOKED  {REVOKE_TARGET}")
    print(f"  {revocation.to_canonical_json()}\n")

    # Step 3: Print complete audit log
    print("\n[STEP 3] Complete RS2 Audit Log\n")
    print(log.dump())
    print(f"\n  Log written to: {LOG_PATH}")

    print("\n" + "=" * 60)
    print("Demo complete.")
    print(f"  {len(DRONES)} drones registered | 1 revoked | {len(log.events)} log entries")
    print("=" * 60)


if __name__ == "__main__":
    main()
