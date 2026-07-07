"""RS2 Revocation Event — construction API.

Bundled, self-contained construction entry points for the INL UAV demo.
Faithful to the canonical reference implementation
(00-Canonical/RS2/10-revocation/RS2-Revocation_RI.py) and the structural schema
(Schemas/revocation.schema.json). Standard library only.

Representation and structural invariants only — no propagation, enforcement,
conflict resolution, or trust/reliance decisions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


def _parse_rfc3339(value: str) -> None:
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    datetime.fromisoformat(v)


@dataclass(frozen=True)
class RevocationScope:
    jurisdictions: List[str]
    object_types: Optional[List[str]] = None
    category: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"jurisdictions": list(self.jurisdictions)}
        if self.object_types is not None:
            d["object_types"] = list(self.object_types)
        if self.category is not None:
            d["category"] = self.category
        if self.constraints is not None:
            d["constraints"] = dict(self.constraints)
        return d


@dataclass(frozen=True)
class TemporalApplicability:
    effective_at: str
    issued_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"effective_at": self.effective_at}
        if self.issued_at is not None:
            d["issued_at"] = self.issued_at
        return d


@dataclass(frozen=True)
class RevocationEvent:
    rs2_version: str
    revocation_id: str
    issuing_authority: str
    targets: List[str]
    scope: RevocationScope
    temporal: TemporalApplicability
    governance_envelope: str
    supersedes: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "rs2_version": self.rs2_version,
            "revocation_id": self.revocation_id,
            "issuing_authority": self.issuing_authority,
            "targets": list(self.targets),
            "scope": self.scope.to_dict(),
            "temporal": self.temporal.to_dict(),
            "governance_envelope": self.governance_envelope,
        }
        if self.supersedes is not None:
            d["supersedes"] = list(self.supersedes)
        if self.metadata:
            d["metadata"] = dict(self.metadata)
        return d

    def to_canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )

    to_json = to_canonical_json


def new_scope(
    *,
    jurisdictions: List[str],
    object_types: Optional[List[str]] = None,
    category: Optional[str] = None,
    constraints: Optional[Dict[str, Any]] = None,
) -> RevocationScope:
    if not isinstance(jurisdictions, list) or len(jurisdictions) < 1:
        raise ValueError("scope.jurisdictions must be a non-empty list")
    for i, j in enumerate(jurisdictions):
        if not isinstance(j, str) or not j.strip():
            raise ValueError(f"scope.jurisdictions[{i}] must be a non-empty string")
    if object_types is not None:
        if not isinstance(object_types, list):
            raise ValueError("scope.object_types must be a list when provided")
        for i, ot in enumerate(object_types):
            if not isinstance(ot, str) or not ot.strip():
                raise ValueError(f"scope.object_types[{i}] must be a non-empty string")
    return RevocationScope(
        jurisdictions=list(jurisdictions),
        object_types=list(object_types) if object_types is not None else None,
        category=category,
        constraints=constraints,
    )


def new_temporal(*, effective_at: str, issued_at: Optional[str] = None) -> TemporalApplicability:
    if not isinstance(effective_at, str) or not effective_at.strip():
        raise ValueError("temporal.effective_at must be a non-empty string")
    _parse_rfc3339(effective_at)
    if issued_at is not None:
        _parse_rfc3339(issued_at)
    return TemporalApplicability(effective_at=effective_at, issued_at=issued_at)


def new_revocation_event(
    *,
    rs2_version: str,
    revocation_id: str,
    issuing_authority: str,
    targets: List[str],
    scope: RevocationScope,
    temporal: TemporalApplicability,
    governance_envelope: str,
    supersedes: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> RevocationEvent:
    for name, val in (
        ("rs2_version", rs2_version),
        ("revocation_id", revocation_id),
        ("issuing_authority", issuing_authority),
        ("governance_envelope", governance_envelope),
    ):
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"{name} is required and must be a non-empty string")

    if not isinstance(targets, list) or len(targets) < 1:
        raise ValueError("targets must be a non-empty list")
    for i, t in enumerate(targets):
        if not isinstance(t, str) or not t.strip():
            raise ValueError(f"targets[{i}] must be a non-empty string")

    if not isinstance(scope, RevocationScope):
        raise ValueError("scope must be a RevocationScope (use new_scope)")
    if not isinstance(temporal, TemporalApplicability):
        raise ValueError("temporal must be a TemporalApplicability (use new_temporal)")

    if supersedes is not None and not isinstance(supersedes, list):
        raise ValueError("supersedes must be a list when provided")

    meta = metadata or {}
    if not isinstance(meta, dict):
        raise ValueError("metadata must be a dict when provided")

    return RevocationEvent(
        rs2_version=rs2_version,
        revocation_id=revocation_id,
        issuing_authority=issuing_authority,
        targets=list(targets),
        scope=scope,
        temporal=temporal,
        governance_envelope=governance_envelope,
        supersedes=list(supersedes) if supersedes is not None else None,
        metadata=meta,
    )
