"""RS2 Identity Object — construction API.

Bundled, self-contained construction entry point for the INL UAV demo.
Faithful to the canonical reference implementation
(00-Canonical/RS2/01-identity/RS2-Identity_RI.py) and the structural schema
(Schemas/identity.schema.json). Standard library only.

W3C alignment note:
  RS2 emits the W3C DID Core-aligned field name `controller` — the entity
  authorized to govern the identity. The demo's `governing_authority` argument
  populates that field.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, FrozenSet, Optional

# Metadata keys are forbidden from embedding permissions, attestations, or key
# material — the RS2 separability invariant. An Identity Object conveys existence
# and referential continuity only.
_FORBIDDEN_METADATA_FRAGMENTS: FrozenSet[str] = frozenset({
    "permission", "permissions", "authorize", "authorization",
    "privilege", "grant", "allow", "deny", "role", "policy", "decision",
    "attestation", "credential",
    "public_key", "private_key", "key_material", "certificate", "x509",
    "provenance", "claim", "assertion", "fact", "truth",
})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_rfc3339(value: str) -> None:
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    datetime.fromisoformat(v)


@dataclass(frozen=True)
class IdentityObject:
    """Immutable RS2 Identity Object — establishes existence and referential
    continuity. Conveys no permissions and asserts no facts beyond existence."""

    rs2_version: str
    identity_id: str
    controller: str          # W3C DID Core: controller (formerly governing_authority)
    created_at: str
    lifecycle_state: str
    jurisdiction: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "rs2_version": self.rs2_version,
            "identity_id": self.identity_id,
            "controller": self.controller,
            "created_at": self.created_at,
            "lifecycle_state": self.lifecycle_state,
        }
        if self.jurisdiction is not None:
            d["jurisdiction"] = self.jurisdiction
        if self.metadata:
            d["metadata"] = dict(self.metadata)
        return d

    def to_canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )

    # Back-compat alias with the reference implementation's serializer name.
    to_json = to_canonical_json


def new_identity(
    *,
    rs2_version: str,
    identity_id: str,
    governing_authority: str,
    lifecycle_state: str,
    jurisdiction: Optional[str] = None,
    created_at: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> IdentityObject:
    """Construct a validated RS2 Identity Object.

    `governing_authority` populates the schema's `controller` field.
    `created_at` defaults to the current UTC time if not supplied.
    """
    ts = created_at or _utc_now_iso()

    for name, val in (
        ("rs2_version", rs2_version),
        ("identity_id", identity_id),
        ("governing_authority", governing_authority),
        ("lifecycle_state", lifecycle_state),
        ("created_at", ts),
    ):
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"{name} must be a non-empty string")

    _parse_rfc3339(ts)

    if jurisdiction is not None and (not isinstance(jurisdiction, str) or not jurisdiction.strip()):
        raise ValueError("jurisdiction must be a non-empty string when provided")

    meta = metadata or {}
    if not isinstance(meta, dict):
        raise ValueError("metadata must be a dict when provided")
    for k in meta:
        lk = str(k).lower()
        for frag in _FORBIDDEN_METADATA_FRAGMENTS:
            if frag in lk:
                raise ValueError(
                    f"metadata key '{k}' violates RS2 separability invariant (matched '{frag}')"
                )

    return IdentityObject(
        rs2_version=rs2_version,
        identity_id=identity_id,
        controller=governing_authority,
        created_at=ts,
        lifecycle_state=lifecycle_state,
        jurisdiction=jurisdiction,
        metadata=meta,
    )
