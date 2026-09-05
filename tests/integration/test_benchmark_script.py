import importlib.util
import sys
from json import loads
from pathlib import Path

from reconra.metrics.evaluator import EvaluationReport
from reconra.models.exception import BreakClass, ReconciliationException, ResolutionStatus
from reconra.models.result import DeterministicMatch, ReconciliationResult


def _benchmark_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_benchmark.py"
    specification = importlib.util.spec_from_file_location("task10_benchmark", path)
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _export_results_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "export_results.py"
    specification = importlib.util.spec_from_file_location("export_results", path)
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_benchmark_accepts_direct_selected_dataset_artifacts(tmp_path) -> None:
    benchmark = _benchmark_module()
    for source_name in ("orders", "payments", "reconciliation_rows", "bank_transactions"):
        (tmp_path / f"{source_name}.json").write_text("[]", encoding="utf-8")

    assert benchmark._dataset_directory(tmp_path, "heldout") == tmp_path


def test_unscored_benchmark_payload_omits_truth_derived_rates() -> None:
    benchmark = _benchmark_module()

    payload = benchmark._benchmark_payload(
        dataset="heldout",
        mode="deterministic",
        output_directory=Path("artifact-output"),
        result=_ResultStub(),
        metrics=EvaluationReport.empty(total_records=4),
    )

    assert payload["scoring_available"] is False
    assert payload["agent_provider_status"] == "NOT_APPLICABLE"
    assert {
        "coverage",
        "auto_resolution_precision",
        "false_match_rate",
        "resolvable_record_recall",
        "correct_abstention_rate",
        "per_break_class_accuracy",
    }.isdisjoint(payload)


def test_unscored_benchmark_payload_includes_result_derived_operational_counts() -> None:
    benchmark = _benchmark_module()
    result = ReconciliationResult(
        run_id="run-benchmark",
        total_bank_credit_paise=500,
        explained_bank_credit_paise=400,
        unexplained_residual_paise=100,
        payment_matches=[
            DeterministicMatch(
                source_id="payment-1",
                candidate_id="settlement-1",
                evidence=["payment_id"],
            )
        ],
        settlement_bank_matches=[
            DeterministicMatch(
                source_id="settlement-1",
                candidate_id="bank-1",
                evidence=["settlement_utr"],
                financial_impact_paise=400,
            )
        ],
        exceptions=[
            ReconciliationException(
                exception_id="review-1",
                break_class=BreakClass.UNRESOLVABLE,
                resolution_status=ResolutionStatus.REVIEW_REQUIRED,
                financial_impact_paise=0,
            ),
            ReconciliationException(
                exception_id="escalated-1",
                break_class=BreakClass.MISSING_BANK_CREDIT,
                resolution_status=ResolutionStatus.ESCALATED,
                financial_impact_paise=100,
            ),
        ],
        completed=True,
    )
    metrics = EvaluationReport.empty(total_records=3).with_result(result)

    payload = benchmark._benchmark_payload(
        dataset="heldout",
        mode="deterministic",
        output_directory=Path("artifact-output"),
        result=result,
        metrics=metrics,
    )

    assert payload["total_records"] == 3
    assert payload["resolved_records"] == 1
    assert payload["deterministic_resolved"] == 1
    assert payload["review_required"] == 1
    assert payload["escalated"] == 1
    assert payload["operational_outcome_count"] == 4


def test_agent_assisted_benchmark_runs_honestly_in_disabled_provider_mode(
    monkeypatch, tmp_path, capsys
) -> None:
    """Fails if agent-assisted evaluation needs a credential instead of safely degrading."""
    from generator.src.artifacts import write_dataset_artifacts
    from generator.src.config import DatasetRole
    from generator.src.roles import generate_dataset

    benchmark = _benchmark_module()
    write_dataset_artifacts(generate_dataset(DatasetRole.HELDOUT), tmp_path / "inputs")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_benchmark.py",
            "--dataset",
            "heldout",
            "--mode",
            "agent-assisted",
            "--input-root",
            str(tmp_path / "inputs"),
            "--output",
            str(tmp_path / "output"),
        ],
    )

    from agent import orchestrator

    calls: list[object] = []
    original = orchestrator.reason_residuals

    async def capture(*args, **kwargs):
        calls.append(kwargs["audit_events"])
        return await original(*args, **kwargs)

    monkeypatch.setattr(orchestrator, "reason_residuals", capture)

    benchmark.main()

    output = loads(capsys.readouterr().out)
    persisted = loads((tmp_path / "output" / "benchmark.json").read_text(encoding="utf-8"))
    assert calls
    assert output["mode"] == "agent-assisted"
    assert output["agent_provider_status"] == "DISABLED_NO_CREDENTIAL"
    assert persisted["agent_provider_status"] == "DISABLED_NO_CREDENTIAL"
    assert output["agent_assisted"] == sum(
        event.action == "SYSTEM_AUTO_APPLY" for event in calls[0]
    )
    assert output["scoring_available"] is False


def test_agent_assisted_benchmark_persists_no_residual_provider_status(
    monkeypatch, tmp_path, capsys
) -> None:
    """An empty residual set must be persisted as no provider invocation."""
    benchmark = _benchmark_module()
    for source_name in ("orders", "payments", "reconciliation_rows", "bank_transactions"):
        (tmp_path / "inputs" / f"{source_name}.json").parent.mkdir(
            parents=True, exist_ok=True
        )
        (tmp_path / "inputs" / f"{source_name}.json").write_text("[]", encoding="utf-8")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_benchmark.py",
            "--dataset",
            "heldout",
            "--mode",
            "agent-assisted",
            "--input-root",
            str(tmp_path / "inputs"),
            "--output",
            str(tmp_path / "output"),
        ],
    )

    benchmark.main()

    output = loads(capsys.readouterr().out)
    persisted = loads((tmp_path / "output" / "benchmark.json").read_text(encoding="utf-8"))
    assert output["agent_provider_status"] == "NO_RESIDUALS"
    assert persisted["agent_provider_status"] == "NO_RESIDUALS"


def test_agent_assisted_benchmark_reports_mocked_live_provider_execution(
    monkeypatch, tmp_path, capsys
) -> None:
    """A configured provider path is reported only after the reasoner actually runs."""
    from agent.providers import gemini
    from generator.src.artifacts import write_dataset_artifacts
    from generator.src.config import DatasetRole
    from generator.src.roles import generate_dataset

    class _LiveReasoner:
        def __init__(self) -> None:
            self.execution_status = "NOT_REQUIRED"

        async def reason(self, cases):
            assert cases
            self.execution_status = "LIVE_PROVIDER_INVOKED"
            return []

    benchmark = _benchmark_module()
    write_dataset_artifacts(generate_dataset(DatasetRole.HELDOUT), tmp_path / "inputs")
    monkeypatch.setattr(gemini, "GeminiReasoner", _LiveReasoner)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_benchmark.py", "--dataset", "heldout", "--mode", "agent-assisted",
            "--input-root", str(tmp_path / "inputs"), "--output", str(tmp_path / "output"),
        ],
    )

    benchmark.main()

    output = loads(capsys.readouterr().out)
    persisted = loads((tmp_path / "output" / "benchmark.json").read_text(encoding="utf-8"))
    assert output["agent_provider_status"] == "LIVE_PROVIDER_INVOKED"
    assert persisted["agent_provider_status"] == "LIVE_PROVIDER_INVOKED"


def test_agent_assisted_benchmark_persists_mocked_provider_failure(
    monkeypatch, tmp_path, capsys
) -> None:
    """A provider failure must not be persisted as a successful invocation."""
    from agent.providers import gemini
    from generator.src.artifacts import write_dataset_artifacts
    from generator.src.config import DatasetRole
    from generator.src.roles import generate_dataset

    class _UnavailableReasoner:
        def __init__(self) -> None:
            self.execution_status = "NOT_REQUIRED"

        async def reason(self, cases):
            assert cases
            self.execution_status = "PROVIDER_UNAVAILABLE"
            return []

    benchmark = _benchmark_module()
    write_dataset_artifacts(generate_dataset(DatasetRole.HELDOUT), tmp_path / "inputs")
    monkeypatch.setattr(gemini, "GeminiReasoner", _UnavailableReasoner)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_benchmark.py",
            "--dataset",
            "heldout",
            "--mode",
            "agent-assisted",
            "--input-root",
            str(tmp_path / "inputs"),
            "--output",
            str(tmp_path / "output"),
        ],
    )

    benchmark.main()

    output = loads(capsys.readouterr().out)
    persisted = loads((tmp_path / "output" / "benchmark.json").read_text(encoding="utf-8"))
    assert output["agent_provider_status"] == "PROVIDER_UNAVAILABLE"
    assert persisted["agent_provider_status"] == "PROVIDER_UNAVAILABLE"


def test_deterministic_benchmark_persists_not_applicable_provider_status(
    tmp_path, monkeypatch, capsys
) -> None:
    """Deterministic runs must persist that no provider path applies."""
    benchmark = _benchmark_module()
    for source_name in ("orders", "payments", "reconciliation_rows", "bank_transactions"):
        (tmp_path / "inputs" / f"{source_name}.json").parent.mkdir(
            parents=True, exist_ok=True
        )
        (tmp_path / "inputs" / f"{source_name}.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_benchmark.py",
            "--dataset",
            "heldout",
            "--mode",
            "deterministic",
            "--input-root",
            str(tmp_path / "inputs"),
            "--output",
            str(tmp_path / "output"),
        ],
    )

    benchmark.main()

    output = loads(capsys.readouterr().out)
    persisted = loads((tmp_path / "output" / "benchmark.json").read_text(encoding="utf-8"))
    assert output["agent_provider_status"] == "NOT_APPLICABLE"
    assert persisted["agent_provider_status"] == "NOT_APPLICABLE"


def test_export_results_persists_not_applicable_provider_status(
    tmp_path, monkeypatch, capsys
) -> None:
    """The deterministic export entry point must satisfy the shared output contract."""
    script_directory = Path(__file__).resolve().parents[2] / "scripts"
    monkeypatch.syspath_prepend(str(script_directory))
    for source_name in ("orders", "payments", "reconciliation_rows", "bank_transactions"):
        (tmp_path / "inputs" / f"{source_name}.json").parent.mkdir(
            parents=True, exist_ok=True
        )
        (tmp_path / "inputs" / f"{source_name}.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "export_results.py",
            "--input-directory",
            str(tmp_path / "inputs"),
            "--output",
            str(tmp_path / "output"),
        ],
    )

    _export_results_module().main()

    persisted = loads((tmp_path / "output" / "benchmark.json").read_text(encoding="utf-8"))
    assert persisted["agent_provider_status"] == "NOT_APPLICABLE"


class _ResultStub:
    total_bank_credit_paise = 300
    explained_bank_credit_paise = 200
    unexplained_residual_paise = 100
