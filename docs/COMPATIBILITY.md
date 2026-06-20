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
- Pulse export shape inspection for consumer-side compatibility checks.

## Knitweb/Pulse Owns

- Content-addressed fabric storage.
- Canonical CBOR and authoritative CID generation.
- Signed record attestation.
- Authoritative Pulse export verification and Web import/export round-trips.
- P2P transport and replication.
- Pulse accounting, ledger, settlement, and useful-work economics.
- Web weaving, mutation, and authoritative provenance authoring.

Lens should consume Knitweb/Pulse exports and preserve their identifiers. It
should not become another fabric runtime.

## OriginTrail Owns

- DKG asset publishing.
- DKG UAL resolution.
- DKG querying and node connectivity.
- DKG anchoring.
- Cross-network knowledge asset discovery.

Lens may cite OriginTrail UALs and interpret resolved JSON-LD data. It should
not publish assets, anchor state, or present itself as a DKG implementation.

## Compatible Inputs

- Knitweb/Pulse JSON-LD exports.
- Knitweb `Web`-like objects.
- OriginTrail DKG UAL citations and resolved JSON-LD documents.
- OriginTrail Knowledge Asset snapshots that have already been resolved by
  OriginTrail tooling.
- Generic JSON-LD documents.
- Graph-query rows from LightRAG, Neo4j, or similar stores.
- Vector result rows.
- Local text, Markdown, and JSON files.
- Human/agent interaction logs represented as read-only rows or JSON.
- ActivityStreams objects and collections exported from social or agent systems.
- Hyperon/MeTTa-style atom exports represented as read-only graph rows.

Interaction logs are compatibility inputs only. Lens may interpret them and cite
their event ids, actors, timestamps, reply links, and target CIDs. Lens must not
become the durable interaction store, agent orchestrator, or identity authority.

ActivityStreams is a compatibility input only. Lens may normalize objects and
collections into cited chunks. It must not implement ActivityPub inbox/outbox
delivery, federation, follow side effects, moderation, or durable social graph
storage.

OriginTrail snapshots are compatibility inputs only. Lens may preserve UALs,
assertion ids, asset ids, and graph records in citations. Lens must not perform
UAL resolution, DKG querying, publishing, anchoring, token operations, or node
connectivity.

Hyperon/MeTTa atom exports are compatibility inputs only. Lens may preserve atom
ids, atom types, source URIs, expressions, and relation paths. Lens must not
store an Atomspace, evaluate MeTTa programs, execute grounded atoms, or mutate a
Hyperon runtime.

## Guardrail

Run:

```bash
lens capabilities
```

The output is a machine-readable contract. New features should extend Lens only
inside `owned_capabilities`. If a proposed feature belongs under
`delegated_to_knitweb` or `delegated_to_origintrail`, Lens should integrate with
that system instead of reimplementing it.
