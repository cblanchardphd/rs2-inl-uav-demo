"""RS2 Audit Log — INL UAV Demo

Thin append-only JSON log. Records Identity Object registrations and
Revocation Events in sequence with timestamps.

This is the "it ran and we have a JSON file" layer — not CH2.
CH2 is the cryptographically immutable version of this same concept.
"""

import json
import os
from datetime import datetime, timezone


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class AuditLog:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.events: list = []
        if os.path.exists(filepath):
            with open(filepath) as f:
                self.events = json.load(f).get("events", [])

    def record_identity_registered(self, identity_dict: dict) -> dict:
        return self._append("identity_registered", identity_dict)

    def record_revocation_issued(self, revocation_dict: dict) -> dict:
        return self._append("revocation_issued", revocation_dict)

    def _append(self, event_type: str, payload: dict) -> dict:
        entry = {
            "seq": len(self.events) + 1,
            "timestamp": _utc_now(),
            "event": event_type,
            "data": payload,
        }
        self.events.append(entry)
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump({"rs2_audit_log": True, "events": self.events}, f, indent=2)
        return entry

    def dump(self) -> str:
        return json.dumps({"rs2_audit_log": True, "events": self.events}, indent=2)
