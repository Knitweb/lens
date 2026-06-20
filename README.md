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
- no background daemon or channel bridge in the core, keeping the ClaudeClaw
  lesson of isolation and explicit boundaries.

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
lens query "What is Lens for?" README.md --json
lens export-context "What is Lens for?" README.md --out context.json
lens render-context context.json --answer
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

- `confidence`: integer from 0 to 100;
- `abstained`: true when cited support is too weak;
- `reason`: short machine-readable explanation;
- citation/source/support counts used to derive the score.
- `trust_support`: integer source-trust support, defaulting to neutral 50.

The default harness abstains below the confidence threshold rather than forcing
an answer from weak evidence.

## Adapters

Implemented in v1:

- `FabricWebAdapter` for in-memory Knitweb `Web`-like objects.
- `JsonLdAdapter` for Pulse/Knitweb JSON-LD exports.
- `RdfJsonLdAdapter` for generic JSON-LD graph documents.
- `LocalFilesAdapter` for Markdown, text, JSON, and JSON-LD files.
- `MappingRowsAdapter` for Neo4j/LightRAG-style row dictionaries.
- `VectorResultsAdapter` for vector-store result dictionaries.

Optional live integrations should wrap these adapters instead of making Lens
depend on a service SDK.

## Project Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Pulse backlog extraction](docs/PULSE_BACKLOG.md)
- [Project 2 sync instructions](docs/PROJECT2_SYNC.md)
- [Evals](docs/EVALS.md)
- [Roadmap](docs/ROADMAP.md)
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
