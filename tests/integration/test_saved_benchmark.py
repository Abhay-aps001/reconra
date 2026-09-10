import importlib.util
from json import loads
from pathlib import Path


def _saved_benchmark_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "saved_benchmark.py"
    specification = importlib.util.spec_from_file_location("saved_benchmark", path)
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_saved_benchmark_is_an_honest_unscored_fallback() -> None:
    module = _saved_benchmark_module()
    artifact = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "saved-benchmark.json"

    payload = module.load_saved_benchmark(artifact)

    assert payload is not None
    assert payload["artifact_type"] == "SAVED_BENCHMARK_RESULT"
    assert payload["scoring_available"] is False
    assert payload["dataset"] == "heldout"
    assert payload["total_records"] == 184
    assert payload["total_bank_credit_paise"] == (
        payload["explained_bank_credit_paise"] + payload["unexplained_residual_paise"]
    )
    assert not {
        "accuracy",
        "precision",
        "recall",
        "f1",
        "false_match_rate",
        "auto_resolution_rate",
    }.intersection(payload)


def test_saved_benchmark_loader_rejects_missing_or_malformed_artifacts(tmp_path) -> None:
    module = _saved_benchmark_module()

    assert module.load_saved_benchmark(tmp_path / "missing.json") is None
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{not json", encoding="utf-8")
    assert module.load_saved_benchmark(malformed) is None


def test_saved_benchmark_publisher_supports_the_existing_deterministic_artifact() -> None:
    module = _saved_benchmark_module()
    source = loads(
        (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "evaluation"
            / "heldout-deterministic"
            / "benchmark.json"
        ).read_text(encoding="utf-8")
    )

    payload = module.build_saved_benchmark(source)

    assert payload["agent_provider_status"] == "NOT_APPLICABLE"


def test_saved_benchmark_file_is_valid_json() -> None:
    artifact = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "saved-benchmark.json"
    assert loads(artifact.read_text(encoding="utf-8"))["artifact_type"] == "SAVED_BENCHMARK_RESULT"
