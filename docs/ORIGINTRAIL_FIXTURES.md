# OriginTrail Fixture Examples

Lens consumes OriginTrail data only after another tool has resolved a Knowledge
Asset snapshot. The fixture format is plain JSON:

- `ual`: the resolved Knowledge Asset UAL;
- `assetId`: external asset identifier;
- `assertionId`: external assertion identifier;
- `publicAssertion.@graph`: records Lens can normalize into cited chunks.

Lens also accepts a top-level `@id` as the UAL when it starts with `did:dkg:`.
That keeps simple JSON-LD exports readable, but explicit `ual`, `assetId`, and
`assertionId` fields are preferred for test fixtures and review.

`examples/origintrail_resolved_asset.json` is a minimal example. It can be
queried without any DKG node or SDK:

```bash
lens query "What did OriginTrail resolve?" examples/origintrail_resolved_asset.json --json
```

## Producing A Fixture

Use an external OriginTrail DKG client or node to resolve the asset and write the
result to JSON before handing it to Lens. Keep that producer outside this
repository unless it is an optional wrapper.

The producer should export a shape equivalent to:

```json
{
  "ual": "did:dkg:...",
  "assetId": "...",
  "assertionId": "...",
  "publicAssertion": {
    "@graph": [
      {
        "@id": "urn:example",
        "title": "Resolved assertion",
        "description": "Text Lens may cite."
      }
    ]
  }
}
```

## Boundary

Do not add these to the Lens base package:

- UAL resolution;
- DKG querying or node connectivity;
- asset publishing;
- assertion anchoring;
- token operations;
- OriginTrail SDK dependencies.

Lens owns only read-only normalization, ranking, reliability, context bundles,
and citations.
