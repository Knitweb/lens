# Evals

Lens has a small offline eval harness for reliability work. It is intentionally
plain JSON and pure Python: no model service, vector database, or graph database
is required.

## Run

```bash
lens eval path/to/eval.json --base-dir .
```

## Fixture Shape

```json
{
  "cases": [
    {
      "name": "grounded provenance query",
      "query": "What preserves provenance citations?",
      "paths": ["tests/fixtures/example.md"],
      "source_trust": {"local-files": 80},
      "should_abstain": false,
      "must_cite": ["example.md"]
    },
    {
      "name": "unsupported query",
      "query": "quantum weather banana",
      "paths": ["tests/fixtures/example.md"],
      "should_abstain": true
    }
  ]
}
```

`must_cite` entries are substring checks over citation source ids, source URIs,
CIDs, and node ids. The result report is integer-only and includes:

- total / passed / failed;
- true, false, and missed abstentions;
- citation failure count;
- citation-faithfulness failure count;
- integer average confidence on the 0-1000 milli-unit scale;
- per-case confidence, missing citation fragments, and `citation_faithful`.

Use this before changing confidence thresholds, retriever scoring, or source
trust weighting.

A non-abstained case only passes when its answer is grounded in its cited chunks.
This catches live or custom model adapters that return plausible text while
ignoring the retrieved context.

`source_trust` is optional. Values are integers from 0 to 100 keyed by Lens
source id, with 50 as the neutral default.
