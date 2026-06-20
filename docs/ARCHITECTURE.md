# Architecture

Lens v1 is an ephemeral interpret layer over content-addressed fabric data.

## Boundaries

- Pulse/Knitweb remains the fabric, transport, accounting, and provenance source.
- Lens reads exported Web data and source rows. It does not persist consensus
  state or mutate Pulse records.
- OriginTrail remains the DKG publishing, UAL resolution, anchoring, and
  cross-network discovery layer. Lens may cite resolved DKG data, but does not
  publish or anchor assets.
- Live LLMs, graph databases, and vector stores are optional wrappers around the
  adapter protocol, not base dependencies.

## Flow

1. Source adapters normalize data into `Chunk` values.
2. `Retriever` ranks chunks with integer-only scoring.
3. `RLMHarness` creates an `InterpretSession`.
4. An `LLMAdapter` turns selected chunks into an answer.
5. `InterpretAnswer` returns text plus citations back to each `ChunkRef`.

## Pulse Export Inspection

Lens includes a small Pulse JSON-LD export shape inspector. It checks whether an
export has object nodes, string ids, object records, list edges, string
relations/destinations, and integer edge weights, then reports deterministic
node, edge, UAL, and relation counts. This is consumer-side compatibility
inspection only. Pulse still owns canonical CID recomputation, signed
attestation, Web import/export round-trips, mutation, transport, and storage.

## OriginTrail Snapshots

Lens can read already-resolved OriginTrail Knowledge Asset snapshots and carry
their UALs in `ChunkRef.source_uri`. This makes DKG-sourced assertions usable as
grounding evidence without making Lens a DKG client. UAL resolution, SPARQL
querying, asset publishing, assertion anchoring, and node connectivity stay with
OriginTrail tooling.

## Human And Agent Interactions

Lens can consume exported human/agent interaction logs as read-only evidence.
Those logs are treated as source rows with actors, timestamps, reply links, and
target CIDs preserved in citations. Lens does not become a chat product, agent
runtime, event bus, or identity system.

Lens can also consume ActivityStreams objects and collections as exported social
interaction evidence. It preserves actor, object, reply, target, tag, audience,
and publication fields in chunk references and metadata. It does not implement
ActivityPub inbox/outbox delivery, follow side effects, federation, moderation,
or social graph storage.

## Context Bundles

Lens context bundles are portable JSON snapshots of the interpret context. They
store:

- the session id and query;
- budget settings and used context;
- ranked chunks and integer score breakdowns;
- every citation back to source id, URI, CID/node id, and relation path.

This makes retrieval reviewable and replayable. A user can export context on one
machine, inspect or sign it elsewhere, then ask an offline or live model adapter
to answer from exactly that selected evidence.

## Reliability

Every answer carries an integer-only reliability report. Confidence is derived
from lexical support, citation count, source diversity, provenance support, and
optional source trust. If confidence falls below the threshold, Lens returns an
abstention message instead of asking the model to fabricate an answer from weak
evidence.

## Lessons From Similar Systems

- Hyperon/MeTTa: represent knowledge as queryable atoms in a graph-like store,
  and let reasoning iterate over those atoms. Lens applies that pattern to
  Pulse chunks without embedding MeTTa as a storage dependency.
- LightRAG: graph relationships should be first-class retrieval signals, not
  an afterthought behind vector similarity.
- LlamaIndex and LangChain: connectors and retrievers need to be separable from
  generation so users can bring their own sources and models.
- IPFS/libp2p: content identity and provider discovery are separate concerns.
  Lens keeps source ids and CIDs explicit, then leaves p2p movement to Pulse.
- W3C DID/VC/Data Integrity: verifiable statements need identifiers, proofs,
  and tamper-evident representations. Lens keeps provenance and CIDs visible in
  every answer path.
- ClaudeClaw-style daemons: always-on agent systems should have clear isolation
  and auth boundaries. Lens core therefore stays library-first; the HTTP route
  is small, explicit, and stdlib-only.

## Non-Goals

- No base vector database.
- No base graph database.
- No required LLM API key.
- No durable writes to Pulse.
- No Knitweb/Pulse fabric storage, p2p replication, ledger/accounting,
  canonical CID generation, Web mutation, or signed-record attestation.
- No OriginTrail DKG publishing, UAL resolution, anchoring, or asset discovery.
- No ranking floats in returned metadata.
