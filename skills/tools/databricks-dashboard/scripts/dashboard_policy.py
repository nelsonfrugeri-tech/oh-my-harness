"""Verify signed dashboard source-admission evidence."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import hmac
import json
import os

from dashboard_models import PolicyEvidence
from dashboard_parsing import objects, source_evidence, string, timestamp
from json_object import JsonObject


def policy_evidence_from_data(data: JsonObject) -> PolicyEvidence:
    verify_signature(data)
    sources = data.get("sources")
    if not isinstance(sources, tuple) or not sources:
        raise ValueError("policy evidence sources must be a non-empty list")
    return PolicyEvidence(
        policy=string(data.get("policy"), "policy"),
        issuer=string(data.get("issuer"), "issuer"),
        generated_at=timestamp(data.get("generated_at"), "generated_at"),
        expires_at=timestamp(data.get("expires_at"), "expires_at"),
        sources=tuple(source_evidence(item) for item in objects(sources, "sources")),
    )


def policy_payload(data: Mapping[object, object]) -> bytes:
    signed = {key: data.get(key) for key in _SIGNED_FIELDS}
    return json.dumps(
        JsonObject.from_mapping(signed).to_builtin(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


_SIGNED_FIELDS = ("policy", "issuer", "generated_at", "expires_at", "sources")


def verify_signature(data: JsonObject) -> None:
    issuer = string(data.get("issuer"), "issuer")
    if issuer not in _trusted_issuers():
        raise ValueError("policy evidence issuer is not trusted")
    key = os.environ.get("DATABRICKS_POLICY_EVIDENCE_KEY", "")
    if not key:
        raise ValueError("DATABRICKS_POLICY_EVIDENCE_KEY is required")
    signature = string(data.get("signature"), "signature")
    expected = hmac.new(key.encode(), policy_payload(data), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("policy evidence signature is invalid")


def _trusted_issuers() -> frozenset[str]:
    raw = os.environ.get("DATABRICKS_POLICY_TRUSTED_ISSUERS", "")
    return frozenset(item.strip() for item in raw.split(",") if item.strip())
