# Hyperon/MeTTa Atom Export Examples

Lens can read static Hyperon/MeTTa-style atom exports as graph rows through
`MappingRowsAdapter` and `LocalFilesAdapter`. The base package does not import
Hyperon, run a MeTTa interpreter, store an Atomspace, or execute grounded atoms.

Runnable fixture:

```bash
lens query "Does Lens become a MeTTa runtime?" examples/metta_atom_rows.json --json
```

## Fixture Shape

Use a JSON object with `rows`. Each row can include:

- `id`: stable atom or export row id.
- `atom_type`, `type`, or `kind`: preserved as `row_type` metadata.
- `title`: short display label.
- `content` or `text`: human-readable grounding text.
- `expression`: optional raw MeTTa expression kept in the chunk record.
- `path` or `relationships`: relation rows converted into `ChunkRef.relation_path`.
- `source_uri`: export/session/source identifier preserved in citations.

`examples/metta_atom_rows.json` uses this shape to show two atoms: one
compatibility claim and one runtime-boundary claim.

## Boundary

Hyperon/MeTTa owns Atomspace storage, pattern matching, evaluation, grounded
atom execution, and runtime mutation. Lens only consumes exported atom rows as
read-only evidence for retrieval and cited answers.
