import json

from knitweb_lens import compatibility_report
from knitweb_lens.cli import main


def test_compatibility_report_separates_lens_from_knitweb_and_origintrail():
    report = compatibility_report()

    assert report["role"] == "read-only-interpret-layer"
    assert report["write_path"] is False
    assert report["mutates_source_graphs"] is False
    assert report["publishes_to_origintrail"] is False
    assert "knitweb-pulse-jsonld-export" in report["compatible_read_models"]
    assert "origintrail-dkg-ual-citation" in report["compatible_read_models"]
    assert "human-agent-interaction-log" in report["compatible_read_models"]
    assert "ephemeral-interpret-session" in report["owned_capabilities"]
    assert "p2p-transport-and-replication" in report["delegated_to_knitweb"]
    assert "dkg-asset-publishing" in report["delegated_to_origintrail"]


def test_owned_capabilities_do_not_duplicate_delegated_system_features():
    report = compatibility_report()
    owned = set(report["owned_capabilities"])

    assert owned.isdisjoint(report["delegated_to_knitweb"])
    assert owned.isdisjoint(report["delegated_to_origintrail"])
    assert owned.isdisjoint(report["non_goals"])


def test_cli_capabilities_outputs_machine_readable_contract(capsys):
    code = main(["capabilities"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["requires_knitweb_runtime"] is False
    assert payload["requires_origintrail_runtime"] is False
    assert "canonical-cbor-cid-generation" in payload["non_goals"]

