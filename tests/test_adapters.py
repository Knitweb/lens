import json
from pathlib import Path

import pytest

from knitweb_lens import (
    ActivityStreamsAdapter,
    InteractionLogAdapter,
    JsonLdAdapter,
    LocalFilesAdapter,
    MappingRowsAdapter,
    OriginTrailUALAdapter,
    RLMHarness,
    VectorResultsAdapter,
)


def test_jsonld_adapter_preserves_cid_and_edges():
    doc = {
        "@graph": [
            {
                "id": "cid:b",
                "record": {"kind": "knowledge", "title": "Beta", "body": "Pulse fabric export"},
                "edges": [{"rel": "derived-from", "dst": "cid:a", "weight": 1}],
            }
        ]
    }

    chunks = tuple(JsonLdAdapter(doc).iter_chunks())

    assert len(chunks) == 1
    assert chunks[0].ref.cid == "cid:b"
    assert chunks[0].ref.relation_path == ("derived-from->cid:a",)
    assert chunks[0].text == "Beta\n\nPulse fabric export"


def test_local_files_adapter_chunks_markdown(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("Lens reads Knitweb fabric and preserves citations.", encoding="utf-8")

    chunks = tuple(LocalFilesAdapter([path]).iter_chunks())

    assert len(chunks) == 1
    assert chunks[0].title == "note.md"
    assert chunks[0].ref.source_uri == str(path)
    assert chunks[0].ref.cid.startswith("local-chunk:")


def test_mapping_rows_adapter_accepts_graph_rows():
    rows = [
        {
            "id": "n1",
            "type": "Claim",
            "title": "Light graph",
            "text": "Graph rows can come from Neo4j or LightRAG.",
            "path": [{"rel": "supports", "dst": "n0"}],
        }
    ]

    chunk = tuple(MappingRowsAdapter(rows).iter_chunks())[0]

    assert chunk.ref.node_id == "n1"
    assert chunk.ref.relation_path == ("supports->n0",)
    assert dict(chunk.metadata)["row_type"] == "Claim"


def test_vector_results_quantize_float_scores_to_integer_weight():
    chunks = tuple(
        VectorResultsAdapter(
            [{"id": "v1", "score": 0.812, "payload": {"text": "Vector hit", "cid": "cid:v"}}]
        ).iter_chunks()
    )

    assert chunks[0].weight == 812
    assert isinstance(chunks[0].weight, int)


def test_pulse_web_export_fixture_round_trips_into_cited_answer():
    fixture = Path(__file__).parent / "fixtures" / "pulse_web_export.json"
    doc = json.loads(fixture.read_text(encoding="utf-8"))

    adapter = JsonLdAdapter(doc, source_id="pulse-fixture", source_uri=str(fixture))
    answer = RLMHarness().query("What derives from recycled fiber?", adapters=[adapter])

    assert "recycled fiber" in answer.text.casefold()
    refs_by_cid = {ref.cid: ref for ref in answer.citations}
    assert "bafyfinisheditem" in refs_by_cid
    assert "bafyrootmaterial" in refs_by_cid
    assert refs_by_cid["bafyfinisheditem"].relation_path == ("derived-from->bafyrootmaterial",)


def test_jsonld_adapter_rejects_non_list_graph():
    with pytest.raises(ValueError, match="@graph must be a list"):
        tuple(JsonLdAdapter({"@graph": {"id": "bad"}}).iter_chunks())


def test_jsonld_adapter_rejects_non_object_graph_entries():
    with pytest.raises(ValueError, match="@graph entries must be objects"):
        tuple(JsonLdAdapter({"@graph": ["bad"]}).iter_chunks())


def test_origintrail_ual_adapter_preserves_resolved_asset_citation():
    ual = "did:dkg:hardhat:31337/0xabc/42"
    asset = {
        "ual": ual,
        "assetId": "ka:42",
        "assertionId": "assertion:1",
        "publicAssertion": {
            "@graph": [
                {
                    "@id": "urn:batch:1",
                    "title": "Verified batch",
                    "description": "OriginTrail resolved assertions can ground Lens answers.",
                    "sameAs": "bafyfabric",
                    "edges": [{"type": "derived-from", "target": "urn:raw:1"}],
                }
            ]
        },
    }

    chunks = tuple(OriginTrailUALAdapter([asset]).iter_chunks())

    assert len(chunks) == 1
    assert chunks[0].ref.source_uri == ual
    assert chunks[0].ref.node_id == "urn:batch:1"
    assert chunks[0].ref.relation_path == ("derived-from->urn:raw:1", "same-as->bafyfabric")
    assert "ground Lens answers" in chunks[0].text
    assert chunks[0].metadata == (
        ("adapter", "origintrail-ual"),
        ("assertion_id", "assertion:1"),
        ("asset_id", "ka:42"),
        ("asset_index", 0),
        ("record_index", 0),
        ("ual", ual),
    )


def test_local_files_adapter_loads_origintrail_snapshot_before_generic_jsonld(tmp_path):
    ual = "did:dkg:otp:2043/0xdef/7"
    path = tmp_path / "origintrail.json"
    path.write_text(
        json.dumps(
            {
                "ual": ual,
                "@graph": [
                    {
                        "@id": "urn:asset:7",
                        "name": "Resolved Knowledge Asset",
                        "description": "Lens cites the UAL instead of becoming a DKG client.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    chunks = tuple(LocalFilesAdapter([path]).iter_chunks())

    assert len(chunks) == 1
    assert chunks[0].ref.source_id == "local-files:origintrail.json"
    assert chunks[0].ref.source_uri == ual
    assert chunks[0].metadata[0] == ("adapter", "origintrail-ual")


def test_origintrail_example_fixture_preserves_ual_and_relations():
    path = Path(__file__).parent.parent / "examples" / "origintrail_resolved_asset.json"
    ual = "did:dkg:otp:2043/0x5afe000000000000000000000000000000000123/17"

    chunks = tuple(LocalFilesAdapter([path]).iter_chunks())

    assert len(chunks) == 2
    by_node = {chunk.ref.node_id: chunk for chunk in chunks}
    assert by_node["urn:ot:batch:17"].ref.source_uri == ual
    assert by_node["urn:ot:batch:17"].ref.relation_path == (
        "derived-from->urn:ot:material:7",
        "same-as->did:dkg:knitweb/bafyreif36ujtcnzic4kozl35sq7qonidacfdxhipgpnlm7spkvssjd6ktm",
    )
    assert by_node["urn:ot:attestation:17"].ref.relation_path == (
        "subject->urn:ot:batch:17",
        "predicate->reviewed-by",
        "object->urn:ot:reviewer:lens",
    )
    assert dict(by_node["urn:ot:attestation:17"].metadata)["assertion_id"] == "assertion:origintrail:17:public"


def test_origintrail_ual_adapter_rejects_non_object_assets():
    with pytest.raises(ValueError, match="OriginTrail assets must be objects"):
        OriginTrailUALAdapter(["bad"])


def test_local_files_adapter_reports_missing_source(tmp_path):
    missing = tmp_path / "missing.md"

    with pytest.raises(FileNotFoundError, match="source path not found"):
        tuple(LocalFilesAdapter([missing]).iter_chunks())


def test_local_files_adapter_reports_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid JSON"):
        tuple(LocalFilesAdapter([path]).iter_chunks())


def test_interaction_log_adapter_preserves_human_agent_context():
    events = [
        {
            "id": "m1",
            "actor": "Ada",
            "actor_type": "human",
            "message": "Please make Lens compatible with Knitweb without duplicating OriginTrail.",
            "timestamp": "2026-06-20T12:00:00Z",
        },
        {
            "id": "m2",
            "actor": "agent",
            "actor_type": "agent",
            "in_reply_to": "m1",
            "target_cid": "bafyfabric",
            "message": "Lens should interpret exported fabric data and preserve citations.",
        },
    ]

    chunks = tuple(InteractionLogAdapter(events, source_uri="chat.json").iter_chunks())

    assert len(chunks) == 2
    assert chunks[0].title == "human Ada"
    assert chunks[0].ref.node_id == "m1"
    assert chunks[0].metadata == (
        ("actor", "Ada"),
        ("actor_type", "human"),
        ("adapter", "interaction-log"),
        ("index", 0),
        ("timestamp", "2026-06-20T12:00:00Z"),
    )
    assert chunks[1].ref.relation_path == ("reply-to->m1", "targets->bafyfabric")


def test_local_files_adapter_loads_interaction_json(tmp_path):
    path = tmp_path / "chat.json"
    path.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "id": "e1",
                        "role": "human",
                        "content": "Human feedback should be cited in Lens interpretation.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    chunks = tuple(LocalFilesAdapter([path]).iter_chunks())

    assert len(chunks) == 1
    assert chunks[0].ref.source_id == "local-files:chat.json"
    assert chunks[0].ref.node_id == "e1"
    assert "Human feedback" in chunks[0].text


def test_local_files_adapter_loads_mapping_rows_json(tmp_path):
    path = tmp_path / "neo4j_rows.json"
    path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "id": "row:1",
                        "title": "Neo4j path row",
                        "text": "Graph rows can ground Lens interpretation.",
                        "path": [{"rel": "supports", "dst": "row:0"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    chunks = tuple(LocalFilesAdapter([path]).iter_chunks())

    assert len(chunks) == 1
    assert chunks[0].ref.source_id == "local-files:neo4j_rows.json"
    assert chunks[0].ref.relation_path == ("supports->row:0",)


def test_metta_atom_rows_fixture_maps_exported_atoms_to_chunks():
    path = Path(__file__).parent.parent / "examples" / "metta_atom_rows.json"

    chunks = tuple(LocalFilesAdapter([path]).iter_chunks())

    assert len(chunks) == 2
    by_node = {chunk.ref.node_id: chunk for chunk in chunks}
    compatibility = by_node["metta:atom:lens-compatibility"]
    boundary = by_node["metta:atom:runtime-boundary"]
    assert compatibility.ref.source_uri == "metta-export://lens/examples/session-1"
    assert compatibility.record["atom_type"] == "Expression"
    assert compatibility.record["expression"] == "(compatible Lens Knitweb OriginTrail)"
    assert compatibility.ref.relation_path == (
        "uses-symbol->metta:symbol:Lens",
        "compatible-with->metta:symbol:Knitweb",
        "compatible-with->metta:symbol:OriginTrail",
    )
    assert dict(compatibility.metadata)["row_type"] == "Expression"
    assert boundary.ref.relation_path == (
        "constrains->metta:atom:lens-compatibility",
        "delegates-runtime-to->hyperon:metta",
    )
    assert "does not store atoms" in boundary.text


def test_local_files_adapter_loads_vector_results_json(tmp_path):
    path = tmp_path / "vector_results.json"
    path.write_text(
        json.dumps(
            {
                "vector_results": [
                    {
                        "id": "hit:1",
                        "score": 0.91,
                        "payload": {
                            "cid": "cid:hit",
                            "title": "Vector hit",
                            "text": "Vector results remain optional read models.",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    chunks = tuple(LocalFilesAdapter([path]).iter_chunks())

    assert len(chunks) == 1
    assert chunks[0].ref.source_id == "local-files:vector_results.json"
    assert chunks[0].ref.cid == "cid:hit"
    assert chunks[0].weight == 910


def test_interaction_log_adapter_rejects_non_object_events():
    with pytest.raises(ValueError, match="interaction log events must be objects"):
        tuple(InteractionLogAdapter(["bad"]).iter_chunks())


def test_activitystreams_adapter_preserves_social_graph_context():
    doc = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Create",
        "id": "https://social.example/activities/1",
        "actor": "https://social.example/users/ada",
        "published": "2026-06-20T12:30:00Z",
        "to": ["https://www.w3.org/ns/activitystreams#Public"],
        "object": {
            "type": "Note",
            "id": "https://social.example/notes/1",
            "content": "<p>Lens should read ActivityStreams as evidence, not federate delivery.</p>",
            "inReplyTo": "https://social.example/notes/root",
            "tag": [{"type": "Mention", "href": "https://social.example/users/agent", "name": "@agent"}],
        },
    }

    chunks = tuple(ActivityStreamsAdapter(doc, source_uri="activity.json").iter_chunks())

    assert len(chunks) == 1
    assert chunks[0].title == "Create Note"
    assert chunks[0].text == "Lens should read ActivityStreams as evidence, not federate delivery."
    assert chunks[0].ref.node_id == "https://social.example/activities/1"
    assert chunks[0].ref.relation_path == (
        "actor->https://social.example/users/ada",
        "object->https://social.example/notes/1",
        "reply-to->https://social.example/notes/root",
        "audience-to->https://www.w3.org/ns/activitystreams#Public",
        "tag->https://social.example/users/agent",
    )
    assert chunks[0].metadata == (
        ("activity_type", "Create"),
        ("actor", "https://social.example/users/ada"),
        ("adapter", "activitystreams"),
        ("index", 0),
        ("published", "2026-06-20T12:30:00Z"),
    )


def test_local_files_adapter_loads_activitystreams_collection(tmp_path):
    path = tmp_path / "outbox.json"
    path.write_text(
        json.dumps(
            {
                "@context": "https://www.w3.org/ns/activitystreams",
                "type": "OrderedCollection",
                "orderedItems": [
                    {
                        "type": "Announce",
                        "id": "https://social.example/activities/2",
                        "actor": "https://social.example/users/agent",
                        "object": {
                            "type": "Note",
                            "id": "https://social.example/notes/2",
                            "summary": "Agent shared a cited Lens interpretation.",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    chunks = tuple(LocalFilesAdapter([path]).iter_chunks())

    assert len(chunks) == 1
    assert chunks[0].ref.source_id == "local-files:outbox.json"
    assert chunks[0].title == "Announce Note"
    assert "cited Lens interpretation" in chunks[0].text


def test_activitystreams_adapter_rejects_non_object_items():
    with pytest.raises(ValueError, match="ActivityStreams items must be objects"):
        tuple(ActivityStreamsAdapter({"orderedItems": ["bad"]}).iter_chunks())


def test_activitystreams_single_fixture_preserves_social_evidence():
    path = Path(__file__).parent.parent / "examples" / "activitystreams_single.json"

    chunks = tuple(LocalFilesAdapter([path]).iter_chunks())

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.ref.source_id == "local-files:activitystreams_single.json"
    assert chunk.ref.node_id == "https://social.example/activities/lens-1"
    assert chunk.ref.relation_path == (
        "actor->https://social.example/users/ada",
        "object->https://social.example/notes/lens-1",
        "attributed-to->https://social.example/users/ada",
        "reply-to->https://social.example/notes/root",
        "audience-to->https://www.w3.org/ns/activitystreams#Public",
        "audience-cc->https://social.example/users/agent",
        "tag->https://social.example/users/agent",
    )
    assert "leaving ActivityPub delivery to the source system" in chunk.text
    assert chunk.metadata == (
        ("activity_type", "Create"),
        ("actor", "https://social.example/users/ada"),
        ("adapter", "activitystreams"),
        ("index", 0),
        ("published", "2026-06-20T13:15:00Z"),
    )


def test_activitystreams_collection_fixture_preserves_human_agent_context():
    path = Path(__file__).parent.parent / "examples" / "activitystreams_collection.json"

    chunks = tuple(LocalFilesAdapter([path]).iter_chunks())

    assert len(chunks) == 2
    refs_by_node = {chunk.ref.node_id: chunk.ref for chunk in chunks}
    assert refs_by_node["https://social.example/activities/human-request"].relation_path == (
        "actor->https://social.example/users/operator",
        "object->https://social.example/notes/human-request",
        "audience-to->https://www.w3.org/ns/activitystreams#Public",
        "tag->https://social.example/users/lens-agent",
    )
    assert refs_by_node["https://social.example/activities/agent-response"].relation_path == (
        "actor->https://social.example/users/lens-agent",
        "object->https://social.example/notes/agent-response",
        "reply-to->https://social.example/notes/human-request",
        "audience-cc->https://social.example/groups/reviewers",
        "tag->https://social.example/users/operator",
    )
    assert all(dict(chunk.metadata)["adapter"] == "activitystreams" for chunk in chunks)
