import copy
import json
from pathlib import Path

import pytest

from knitweb_lens import inspect_pulse_export, pulse_export_issues, validate_pulse_export_shape


def _fixture() -> dict:
    path = Path(__file__).parent / "fixtures" / "pulse_web_export.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_pulse_export_shape_inspection_accepts_fixture():
    report = inspect_pulse_export(_fixture())

    assert report == {
        "format": "pulse-jsonld-export-shape",
        "ok": True,
        "issues": [],
        "node_count": 2,
        "edge_count": 1,
        "ual_count": 2,
        "relation_counts": {"derived-from": 1},
        "authoritative_verification": False,
        "mutates_source_graphs": False,
    }


def test_pulse_export_shape_validation_rejects_float_edge_weight():
    doc = copy.deepcopy(_fixture())
    doc["@graph"][1]["edges"][0]["weight"] = 1.5

    issues = pulse_export_issues(doc)

    assert "@graph[1].edges[0].weight must be an integer" in issues
    with pytest.raises(ValueError, match="weight must be an integer"):
        validate_pulse_export_shape(doc)


def test_pulse_export_shape_validation_rejects_missing_record_object():
    doc = copy.deepcopy(_fixture())
    doc["@graph"][0].pop("record")

    assert "@graph[0].record must be an object" in pulse_export_issues(doc)
