"""Machine-readable Lens capability and boundary report."""

from __future__ import annotations

from typing import Any

LENS_ROLE = "read-only-interpret-layer"

COMPATIBLE_READ_MODELS = (
    "knitweb-pulse-jsonld-export",
    "knitweb-web-like-object",
    "origintrail-dkg-ual-citation",
    "generic-jsonld-document",
    "graph-query-row",
    "vector-result-row",
    "local-text-json-markdown",
    "human-agent-interaction-log",
    "activitystreams-object-or-collection",
)

OWNED_CAPABILITIES = (
    "source-adapter-normalization",
    "deterministic-integer-retrieval",
    "ephemeral-interpret-session",
    "portable-context-bundle",
    "citation-rendering",
    "offline-deterministic-answer-synthesis",
    "integer-confidence-and-abstention",
    "offline-reliability-eval",
)

DELEGATED_TO_KNITWEB = (
    "content-addressed-fabric-storage",
    "canonical-cbor-cid-generation",
    "signed-record-attestation",
    "p2p-transport-and-replication",
    "pulse-accounting-and-ledger",
    "web-weaving-and-mutation",
    "authoritative-provenance-authoring",
)

DELEGATED_TO_ORIGINTRAIL = (
    "dkg-asset-publishing",
    "dkg-ual-resolution",
    "dkg-anchoring",
    "cross-network-knowledge-asset-discovery",
)

NON_GOALS = DELEGATED_TO_KNITWEB + DELEGATED_TO_ORIGINTRAIL + (
    "consensus",
    "durable-knowledge-graph-storage",
    "token-or-payment-settlement",
    "identity-wallet-management",
    "signature-key-management",
    "activitypub-inbox-outbox-delivery",
    "activitypub-federated-server",
    "social-graph-moderation",
)


def compatibility_report() -> dict[str, Any]:
    """Return the public Lens capability contract.

    The report is deliberately data-only so docs, tests, CLIs, and downstream
    systems can check the same boundary: Lens reads compatible exports and
    produces cited interpretations; Knitweb/Pulse and OriginTrail keep their own
    storage, anchoring, transport, signing, and provenance authority.
    """
    return {
        "role": LENS_ROLE,
        "compatible_read_models": list(COMPATIBLE_READ_MODELS),
        "owned_capabilities": list(OWNED_CAPABILITIES),
        "delegated_to_knitweb": list(DELEGATED_TO_KNITWEB),
        "delegated_to_origintrail": list(DELEGATED_TO_ORIGINTRAIL),
        "non_goals": list(NON_GOALS),
        "write_path": False,
        "mutates_source_graphs": False,
        "publishes_to_origintrail": False,
        "requires_knitweb_runtime": False,
        "requires_origintrail_runtime": False,
    }
