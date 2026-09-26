import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("phase108_prepare_semantic_review.py")


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n")
    return path


def test_prepare_uses_case_provenance_fixture_id(tmp_path):
    source_path = write_json(tmp_path / "source.json", [{
        "fixture_id": "source-bank-new-prefix-001",
        "category": "code_review",
        "scenario_family": "review",
        "artifact_kind": "patch",
        "decision_focus": "validate-fix",
        "independence_rationale": "Independent fixture.",
        "evidence_boundary": "Only the supplied patch is evidence.",
    }])
    case_path = write_json(tmp_path / "cases.json", [{
        "id": "p108v17-code_review-001",
        "category": "code_review",
        "messages": [{"role": "user", "content": "Review the supplied patch."}],
        "provenance": {"fixture_id": "source-bank-new-prefix-001"},
    }])
    keys_path = write_json(tmp_path / "keys.json", [{
        "id": "p108v17-code_review-001",
        "evidence_boundary": "Do not infer beyond the patch.",
    }])
    neardup_path = write_json(tmp_path / "neardup.json", {"pairs": []})
    output_dir = tmp_path / "review-bundle"

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--source", str(source_path),
         "--cases", str(case_path), "--keys", str(keys_path),
         "--neardup", str(neardup_path), "--output-dir", str(output_dir)],
        check=True, capture_output=True, text=True,
    )

    assert '"items": 1' in result.stdout
    manifest = json.loads((output_dir / "manifest.json").read_text())
    item = json.loads((output_dir / "items.json").read_text())[0]
    assert manifest["model_outputs_included"] is False
    assert item["case_id"] == "p108v17-code_review-001"
    assert item["scenario_family"] == "review"
    assert item["evidence_boundary"] == "Do not infer beyond the patch."


def test_prepare_rejects_case_without_fixture_provenance(tmp_path):
    source_path = write_json(tmp_path / "source.json", [])
    case_path = write_json(tmp_path / "cases.json", [{
        "id": "p108v17-code_review-001",
        "category": "code_review",
        "messages": [{"role": "user", "content": "Review the supplied patch."}],
    }])
    keys_path = write_json(tmp_path / "keys.json", [{"id": "p108v17-code_review-001"}])
    neardup_path = write_json(tmp_path / "neardup.json", {"pairs": []})
    output_dir = tmp_path / "review-bundle"

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--source", str(source_path),
         "--cases", str(case_path), "--keys", str(keys_path),
         "--neardup", str(neardup_path), "--output-dir", str(output_dir)],
        capture_output=True, text=True,
    )

    assert result.returncode != 0
    assert "lacks a source fixture reference" in result.stderr
    assert not output_dir.exists()
