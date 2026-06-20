# Compatibility Boundary

Lens must be compatible with Knitweb/Pulse and OriginTrail, but it must not
duplicate their core features.

## Lens Owns

- Normalizing read models into chunks.
- Ranking chunks deterministically with integer scores.
- Creating ephemeral interpret sessions.
- Exporting and replaying portable context bundles.
- Rendering cited answers.
- Offline deterministic answer synthesis for tests.
- Integer confidence, abstention, source trust, and eval reports.

## Knitweb/Pulse Owns

- Content-addressed fabric storage.
- Canonical CBOR and authoritative CID generation.
- Signed record attestation.
- P2P transport and replication.
- Pulse accounting, ledger, settlement, and useful-work economics.
- Web weaving, mutation, and authoritative provenance authoring.

Lens should consume Knitweb/Pulse exports and preserve their identifiers. It
should not become another fabric runtime.

## OriginTrail Owns

- DKG asset publishing.
- DKG UAL resolution.
- DKG anchoring.
- Cross-network knowledge asset discovery.

Lens may cite OriginTrail UALs and interpret resolved JSON-LD data. It should
not publish assets, anchor state, or present itself as a DKG implementation.

## Compatible Inputs

- Knitweb/Pulse JSON-LD exports.
- Knitweb `Web`-like objects.
- OriginTrail DKG UAL citations and resolved JSON-LD documents.
- Generic JSON-LD documents.
- Graph-query rows from LightRAG, Neo4j, or similar stores.
- Vector result rows.
- Local text, Markdown, and JSON files.
- Human/agent interaction logs represented as read-only rows or JSON.

Interaction logs are compatibility inputs only. Lens may interpret them and cite
their event ids, actors, timestamps, reply links, and target CIDs. Lens must not
become the durable interaction store, agent orchestrator, or identity authority.

## Guardrail

Run:

```bash
lens capabilities
```

The output is a machine-readable contract. New features should extend Lens only
inside `owned_capabilities`. If a proposed feature belongs under
`delegated_to_knitweb` or `delegated_to_origintrail`, Lens should integrate with
that system instead of reimplementing it.
