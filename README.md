# Lens

Lens is the pure-Python interpret layer for Knitweb. It reads a Pulse/Knitweb
fabric, focuses the relevant records, and returns provenance-cited answers. It
does not write durable facts, run consensus, or require a live LLM/vector
service for v1.

- Repository: `github.com/knitweb/lens`
- Distribution: `knitweb-lens`
- Import: `knitweb_lens`
- CLI: `lens`
- HTTP route: `POST /interpret`

## Why Lens

Pulse moves the signal through the fabric. Lens focuses that fabric into a
task-specific interpretation. A Lens session is ephemeral: it loads chunks from
adapters, ranks them deterministically, prunes to a context budget, and emits an
answer with citations back to original source ids and CIDs when available.

The v1 design borrows the useful patterns from graph RAG, MeTTa/Hyperon, and
p2p/crypto systems without inheriting their heavy runtime dependencies:

- adapter-first ingestion, like mature RAG frameworks;
- graph and provenance paths, like LightRAG-style graph retrieval;
- symbolic atom/chunk iteration, inspired by MeTTa over Atomspace;
- content-derived identity and tamper visibility, aligned with CID/DID/VC
  practice;
- read-only ActivityStreams ingestion for social/human-agent traces without
  ActivityPub server behavior;
- no background daemon or channel bridge in the core, keeping the ClaudeClaw
  lesson of isolation and explicit boundaries.

Lens is compatible with Knitweb/Pulse and OriginTrail as a read-only interpret
layer. It does not replace their fabric storage, p2p replication, canonical CID
generation, attestation, accounting, DKG publishing, or anchoring.
For OriginTrail, Lens consumes already-resolved Knowledge Asset snapshots and
preserves UALs as citations; it does not resolve UALs or connect to DKG nodes.

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
lens query "What is Lens for?" README.md --json
lens export-context "What is Lens for?" README.md --out context.json
lens render-context context.json --answer
lens query "How do graph rows work?" examples/neo4j_rows.json --json
lens query "How are vector scores handled?" examples/vector_results.json --json
lens capabilities
lens inspect-pulse tests/fixtures/pulse_web_export.json
python tools/generate_pulse_fixture.py --pulse-src ../pulse/src
python -m pytest
```

Run the standard-library HTTP endpoint:

```bash
lens serve README.md --host 127.0.0.1 --port 8765
curl -s http://127.0.0.1:8765/interpret \
  -H 'content-type: application/json' \
  -d '{"query":"What does Lens preserve?","include_context":true}'
```

## Core API

```python
from knitweb_lens import LocalFilesAdapter, RLMHarness

harness = RLMHarness()
answer = harness.query(
    "How does Lens cite sources?",
    adapters=[LocalFilesAdapter(["README.md"])],
)
print(answer.text)
```

Adapters normalize source systems into `Chunk` objects. `Retriever` ranks chunks
with integer-only scores and deterministic tie breaks. `RLMHarness` supplies an
offline deterministic model adapter by default, so all tests run without API
keys, embeddings, network access, or vector databases.

`lens inspect-pulse` performs a read-only Pulse JSON-LD export shape check. It
reports node, edge, UAL, and relation counts; it does not recompute canonical
CIDs, verify signatures, import/export a Web, or mutate source graphs.

`tools/generate_pulse_fixture.py` can refresh
`tests/fixtures/pulse_real_web_export.json` from a local Pulse checkout. The
generated fixture is committed as data so Lens remains dependency-free in CI.

## Context Bundles

`lens export-context` writes a portable JSON bundle containing the selected
ranked chunks, scores, query, and citations. The bundle can be reviewed,
rendered, replayed, or sent back to `POST /interpret` without re-reading the
original adapters.

```bash
lens export-context "How does Lens cite sources?" README.md --out context.json
lens answer-context context.json --markdown
```

HTTP replay shape:

```json
{
  "context": {
    "format": "knitweb-lens-context",
    "version": 1,
    "session": {}
  }
}
```

## Reliability

Every `InterpretAnswer` includes deterministic reliability metadata:

- `confidence`: integer milli-unit score from 0 to 1000;
- `status`: `answered` or `abstained`;
- `abstained`: true when cited support is too weak;
- `reason`: short machine-readable explanation;
- citation/source/support counts used to derive the score.
- `trust_support`: integer source-trust support, defaulting to neutral 50.

The default harness abstains below the confidence threshold rather than forcing
an answer from weak evidence.
When provided, source trust also contributes an integer `trust_score` to
retrieval ranking so low-trust sources can be down-weighted before answer
synthesis.

## Adapters

Implemented in v1:

- `FabricWebAdapter` for in-memory Knitweb `Web`-like objects.
- `JsonLdAdapter` for Pulse/Knitweb JSON-LD exports.
- `RdfJsonLdAdapter` for generic JSON-LD graph documents.
- `OriginTrailUALAdapter` for already-resolved OriginTrail Knowledge Asset snapshots.
- `LocalFilesAdapter` for Markdown, text, JSON, and JSON-LD files.
- `InteractionLogAdapter` for exported human/agent interaction logs.
- `ActivityStreamsAdapter` for exported ActivityStreams objects and collections.
- `MappingRowsAdapter` for Neo4j/LightRAG-style row dictionaries.
- `VectorResultsAdapter` for vector-store result dictionaries.

Optional live integrations should wrap these adapters instead of making Lens
depend on a service SDK.
For the model side, use `render_model_prompt` and the `LLMAdapter` protocol
described in [Optional live model adapters](docs/LIVE_ADAPTERS.md).

## Project Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Compatibility boundary](docs/COMPATIBILITY.md)
- [Pulse backlog extraction](docs/PULSE_BACKLOG.md)
- [Project 2 sync instructions](docs/PROJECT2_SYNC.md)
- [Evals](docs/EVALS.md)
- [Roadmap](docs/ROADMAP.md)
- [Optional live model adapters](docs/LIVE_ADAPTERS.md)
- [Review policy](docs/REVIEW_POLICY.md)
- [Research references](docs/REFERENCES.md)
- [Developer outreach](docs/OUTREACH.md)
- [Top 10 feedback targets](docs/FEEDBACK_TARGETS.md)
- [GitHub Pages landing page](docs/index.html)

## Development

```bash
python -m pytest
python -m build
```

Lens is Apache-2.0 and designed for small, reviewable contributions.
