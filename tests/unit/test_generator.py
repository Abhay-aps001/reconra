from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping
from datetime import date, datetime
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from typing import Any

from reconra.models.exception import BreakClass

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APPROVED_RAZORPAY_METHODS = {"upi", "card", "netbanking", "wallet", "emi"}
INVENTED_CARD_METHODS = {"credit_card", "debit_card"}
REQUIRED_MESSY_BREAK_CLASSES = {
    BreakClass.ROUNDING_VARIANCE,
    BreakClass.AMOUNT_MISMATCH,
    BreakClass.FEE_VARIANCE,
    BreakClass.TAX_VARIANCE,
    BreakClass.SETTLEMENT_CUTOFF,
    BreakClass.DELAYED_SETTLEMENT,
    BreakClass.INSTANT_SETTLEMENT_VARIANCE,
    BreakClass.REFUND_NETTED_LATER,
    BreakClass.PARTIAL_REFUND,
    BreakClass.MANGLED_UTR,
    BreakClass.MANGLED_NARRATION,
    BreakClass.DUPLICATE_LEDGER_ROW,
    BreakClass.DUPLICATE_BANK_CREDIT,
    BreakClass.DISPUTE_ADJUSTMENT,
    BreakClass.GENERAL_ADJUSTMENT,
    BreakClass.MISSING_ORDER,
    BreakClass.MISSING_PAYMENT,
    BreakClass.MISSING_SETTLEMENT,
    BreakClass.MISSING_BANK_CREDIT,
    BreakClass.UNRESOLVABLE,
}


def _load_generate_clean_dataset() -> Callable[[int], Any]:
    clean_module = REPOSITORY_ROOT / "generator" / "src" / "clean.py"
    assert clean_module.is_file(), "Task 6 must provide generator/src/clean.py"

    module = importlib.import_module("generator.src.clean")
    generate_clean_dataset = getattr(module, "generate_clean_dataset", None)
    assert callable(generate_clean_dataset), (
        "clean generator must expose generate_clean_dataset(seed)"
    )
    return generate_clean_dataset


def test_same_seed_produces_same_input_hash() -> None:
    generate_clean_dataset = _load_generate_clean_dataset()

    first = generate_clean_dataset(seed=1101)
    second = generate_clean_dataset(seed=1101)

    assert first.input_hash == second.input_hash


def _clean_dataset() -> Any:
    return _load_generate_clean_dataset()(seed=1101)


def _raw_inputs(dataset: Any) -> Mapping[str, Any]:
    raw_inputs = getattr(dataset, "raw_inputs", None)
    assert isinstance(raw_inputs, Mapping), "GeneratedDataset must expose raw_inputs"
    return raw_inputs


def _records(raw_inputs: Mapping[str, Any], source_name: str) -> list[Mapping[str, Any]]:
    records = raw_inputs.get(source_name)
    assert isinstance(records, list), f"raw_inputs[{source_name!r}] must be a list"
    assert records, f"raw_inputs[{source_name!r}] must not be empty"
    assert all(isinstance(record, Mapping) for record in records)
    return records


def _calendar_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return datetime.fromtimestamp(value).date()
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    raise AssertionError(f"expected a timestamp or date, got {value!r}")


def test_clean_dataset_contains_real_raw_source_collections() -> None:
    raw_inputs = _raw_inputs(_clean_dataset())

    assert {"orders", "payments", "reconciliation_rows", "bank_transactions"} <= raw_inputs.keys()
    for source_name in ("orders", "payments", "reconciliation_rows", "bank_transactions"):
        _records(raw_inputs, source_name)


def test_clean_dataset_contains_sixty_to_eighty_reconciliation_rows() -> None:
    reconciliation_rows = _records(_raw_inputs(_clean_dataset()), "reconciliation_rows")

    assert 60 <= len(reconciliation_rows) <= 80


def test_clean_raw_sources_preserve_order_payment_settlement_and_bank_relationships() -> None:
    raw_inputs = _raw_inputs(_clean_dataset())
    orders = _records(raw_inputs, "orders")
    payments = _records(raw_inputs, "payments")
    reconciliation_rows = _records(raw_inputs, "reconciliation_rows")
    bank_transactions = _records(raw_inputs, "bank_transactions")
    orders_by_id = {order["order_id"]: order for order in orders}
    payments_by_id = {payment["payment_id"]: payment for payment in payments}
    bank_by_utr = {
        bank_transaction["utr"]: bank_transaction for bank_transaction in bank_transactions
    }

    payment_rows = [row for row in reconciliation_rows if row["type"] == "payment"]
    assert payment_rows, "clean data must contain payment reconciliation rows"
    for row in payment_rows:
        payment = payments_by_id[row["payment_id"]]
        order = orders_by_id[row["order_id"]]
        assert payment["order_id"] == order["order_id"]
        assert row["order_receipt"] == order["receipt"]
        assert row["amount"] == payment["amount_paise"] == order["amount_paise"]
        assert _calendar_date(order["created_at"]) <= _calendar_date(payment["captured_at"])
        assert _calendar_date(payment["captured_at"]) <= _calendar_date(row["created_at"])
        assert _calendar_date(row["created_at"]) <= _calendar_date(row["settled_at"])

    for settlement_utr, bank_transaction in bank_by_utr.items():
        settlement_rows = [
            row for row in reconciliation_rows if row["settlement_utr"] == settlement_utr
        ]
        assert settlement_rows, f"bank UTR {settlement_utr!r} must identify settlement rows"
        assert bank_transaction["credit_paise"] == sum(
            row["credit"] - row["debit"] for row in settlement_rows
        )
        assert _calendar_date(settlement_rows[0]["settled_at"]) <= _calendar_date(
            bank_transaction["value_date"] or bank_transaction["transaction_date"]
        )


def test_clean_reconciliation_rows_follow_the_approved_razorpay_shape() -> None:
    required_fields = {
        "entity_id",
        "type",
        "debit",
        "credit",
        "amount",
        "currency",
        "fee",
        "tax",
        "on_hold",
        "settled",
        "created_at",
        "settled_at",
        "settlement_id",
        "description",
        "notes",
        "payment_id",
        "settlement_utr",
        "order_id",
        "order_receipt",
        "method",
        "card_network",
        "card_issuer",
        "card_type",
        "dispute_id",
    }
    reconciliation_rows = _records(_raw_inputs(_clean_dataset()), "reconciliation_rows")

    for row in reconciliation_rows:
        assert required_fields <= row.keys()
        assert row["type"] in {"payment", "refund", "transfer", "adjustment"}


def test_clean_raw_money_values_are_integer_paise() -> None:
    raw_inputs = _raw_inputs(_clean_dataset())
    monetary_fields_by_source = {
        "orders": {"amount_paise"},
        "payments": {"amount_paise"},
        "reconciliation_rows": {"debit", "credit", "amount", "fee", "tax"},
        "bank_transactions": {"credit_paise", "debit_paise"},
    }

    for source_name, monetary_fields in monetary_fields_by_source.items():
        for record in _records(raw_inputs, source_name):
            for field_name in monetary_fields:
                assert type(record[field_name]) is int


def test_clean_input_hash_is_the_hash_of_canonical_raw_input_content() -> None:
    dataset = _clean_dataset()
    raw_inputs = _raw_inputs(dataset)
    canonical_raw_input_content = dumps(
        raw_inputs, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")

    assert dataset.input_hash == sha256(canonical_raw_input_content).hexdigest()


def test_clean_raw_inputs_do_not_expose_ground_truth() -> None:
    raw_inputs = _raw_inputs(_clean_dataset())

    assert "ground_truth" not in raw_inputs
    assert not any("truth" in source_name.lower() for source_name in raw_inputs)


def test_clean_payment_and_reconciliation_methods_are_razorpay_compatible() -> None:
    raw_inputs = _raw_inputs(_clean_dataset())

    for source_name in ("payments", "reconciliation_rows"):
        for record in _records(raw_inputs, source_name):
            assert record["method"] in APPROVED_RAZORPAY_METHODS


def test_clean_records_do_not_use_invented_card_method_values() -> None:
    raw_inputs = _raw_inputs(_clean_dataset())

    for source_name in ("payments", "reconciliation_rows"):
        for record in _records(raw_inputs, source_name):
            assert record["method"] not in INVENTED_CARD_METHODS


def test_clean_card_reconciliation_rows_include_card_metadata() -> None:
    reconciliation_rows = _records(_raw_inputs(_clean_dataset()), "reconciliation_rows")
    card_rows = [row for row in reconciliation_rows if row["method"] == "card"]

    assert card_rows, "clean fixture must include card reconciliation rows"
    for row in card_rows:
        assert row["card_type"] in {"credit", "debit"}
        assert isinstance(row["card_network"], str) and row["card_network"]
        assert isinstance(row["card_issuer"], str) and row["card_issuer"]


def test_clean_non_card_reconciliation_rows_keep_card_metadata_null() -> None:
    reconciliation_rows = _records(_raw_inputs(_clean_dataset()), "reconciliation_rows")
    non_card_rows = [row for row in reconciliation_rows if row["method"] != "card"]

    assert non_card_rows
    for row in non_card_rows:
        assert row["card_type"] is None
        assert row["card_network"] is None
        assert row["card_issuer"] is None


def _load_messy_generator_interfaces() -> tuple[Callable[..., Any], type[Any]]:
    distribution_module = REPOSITORY_ROOT / "generator" / "scenarios" / "distribution.py"
    messy_module = REPOSITORY_ROOT / "generator" / "src" / "messy.py"
    assert distribution_module.is_file(), "Task 6 must provide generator/scenarios/distribution.py"
    assert messy_module.is_file(), "Task 6 must provide generator/src/messy.py"

    distribution = importlib.import_module("generator.scenarios.distribution")
    messy = importlib.import_module("generator.src.messy")
    scenario_distribution = getattr(distribution, "ScenarioDistribution", None)
    generate_messy_dataset = getattr(messy, "generate_messy_dataset", None)
    assert isinstance(scenario_distribution, type)
    assert callable(generate_messy_dataset)
    return generate_messy_dataset, scenario_distribution


def _coverage_profile() -> Any:
    _, scenario_distribution = _load_messy_generator_interfaces()
    return scenario_distribution(
        scenario_counts={break_class: 1 for break_class in REQUIRED_MESSY_BREAK_CLASSES}
    )


def _messy_dataset() -> Any:
    generate_messy_dataset, _ = _load_messy_generator_interfaces()
    return generate_messy_dataset(seed=2202, profile=_coverage_profile())


def _truth_cases(dataset: Any) -> list[dict[str, Any]]:
    ground_truth = getattr(dataset, "ground_truth", None)
    assert isinstance(ground_truth, Mapping), "GeneratedDataset must expose separate ground_truth"
    cases = ground_truth.get("cases")
    assert isinstance(cases, list) and cases
    assert all(isinstance(case, dict) for case in cases)
    return cases


def _truth_case_for(truth_cases: list[dict[str, Any]], break_class: BreakClass) -> dict[str, Any]:
    matching_cases = [case for case in truth_cases if case["break_class"] == break_class.value]
    assert matching_cases, f"missing ground-truth case for {break_class.value}"
    return matching_cases[0]


def _reconciliation_rows_by_entity_id(
    raw_inputs: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    return {row["entity_id"]: row for row in _records(raw_inputs, "reconciliation_rows")}


def test_scenario_distribution_can_request_every_required_messy_break_class() -> None:
    profile = _coverage_profile()

    assert profile.scenario_counts == {
        break_class: 1 for break_class in REQUIRED_MESSY_BREAK_CLASSES
    }


def test_messy_dataset_exposes_raw_inputs_separate_ground_truth_and_input_hash() -> None:
    dataset = _messy_dataset()

    assert isinstance(_raw_inputs(dataset), Mapping)
    assert isinstance(getattr(dataset, "ground_truth", None), Mapping)
    assert isinstance(dataset.input_hash, str) and dataset.input_hash


def test_messy_raw_inputs_exclude_truth_labels_and_hidden_answers() -> None:
    raw_inputs = _raw_inputs(_messy_dataset())
    prohibited_field_fragments = {
        "ground_truth",
        "expected_break_class",
        "expected_match",
        "resolvable",
        "truth",
        "expected",
        "answer",
    }

    def raw_field_names(value: Any) -> list[str]:
        if isinstance(value, Mapping):
            return [
                key
                for nested_key, nested_value in value.items()
                for key in [str(nested_key), *raw_field_names(nested_value)]
            ]
        if isinstance(value, list):
            return [key for item in value for key in raw_field_names(item)]
        return []

    assert "ground_truth" not in raw_inputs
    for field_name in raw_field_names(raw_inputs):
        assert not any(fragment in field_name.lower() for fragment in prohibited_field_fragments)


def test_messy_ground_truth_uses_canonical_break_classes_and_raw_case_identifiers() -> None:
    raw_inputs = _raw_inputs(_messy_dataset())
    truth_cases = _truth_cases(_messy_dataset())
    raw_entity_ids = set(_reconciliation_rows_by_entity_id(raw_inputs))
    canonical_break_class_values = {break_class.value for break_class in BreakClass}

    for truth_case in truth_cases:
        assert truth_case["break_class"] in canonical_break_class_values
        assert isinstance(truth_case["case_id"], str) and truth_case["case_id"]
        assert isinstance(truth_case["raw_entity_ids"], list) and truth_case["raw_entity_ids"]
        assert set(truth_case["raw_entity_ids"]) <= raw_entity_ids


def test_messy_coverage_profile_labels_every_required_break_class() -> None:
    truth_cases = _truth_cases(_messy_dataset())

    assert REQUIRED_MESSY_BREAK_CLASSES <= {
        BreakClass(truth_case["break_class"]) for truth_case in truth_cases
    }


def test_messy_representative_scenarios_mutate_raw_inputs() -> None:
    dataset = _messy_dataset()
    raw_inputs = _raw_inputs(dataset)
    truth_cases = _truth_cases(dataset)
    reconciliation_rows = _records(raw_inputs, "reconciliation_rows")
    reconciliation_rows_by_id = _reconciliation_rows_by_entity_id(raw_inputs)
    orders = _records(raw_inputs, "orders")
    payments = _records(raw_inputs, "payments")
    bank_transactions = _records(raw_inputs, "bank_transactions")
    order_ids = {order["order_id"] for order in orders}
    payment_ids = {payment["payment_id"] for payment in payments}
    bank_utrs = {bank_transaction["utr"] for bank_transaction in bank_transactions}

    mangled_utr_case = _truth_case_for(truth_cases, BreakClass.MANGLED_UTR)
    mangled_utr_row = reconciliation_rows_by_id[mangled_utr_case["raw_entity_ids"][0]]
    assert mangled_utr_row["settlement_utr"] not in bank_utrs

    assert len(order_ids) < len(orders), (
        "duplicate ledger scenario must duplicate an order input row"
    )
    bank_credit_signatures = [
        (
            bank_transaction["utr"],
            bank_transaction["credit_paise"],
            bank_transaction["debit_paise"],
            bank_transaction["transaction_date"],
        )
        for bank_transaction in bank_transactions
    ]
    assert len(set(bank_credit_signatures)) < len(bank_credit_signatures)

    missing_order_case = _truth_case_for(truth_cases, BreakClass.MISSING_ORDER)
    missing_order_row = reconciliation_rows_by_id[missing_order_case["raw_entity_ids"][0]]
    assert missing_order_row["order_id"] not in order_ids

    missing_payment_case = _truth_case_for(truth_cases, BreakClass.MISSING_PAYMENT)
    missing_payment_row = reconciliation_rows_by_id[missing_payment_case["raw_entity_ids"][0]]
    assert missing_payment_row["payment_id"] not in payment_ids

    missing_settlement_case = _truth_case_for(truth_cases, BreakClass.MISSING_SETTLEMENT)
    missing_settlement_row = reconciliation_rows_by_id[missing_settlement_case["raw_entity_ids"][0]]
    assert missing_settlement_row["settlement_id"] is None or not missing_settlement_row["settled"]

    missing_bank_credit_case = _truth_case_for(truth_cases, BreakClass.MISSING_BANK_CREDIT)
    missing_bank_credit_row = reconciliation_rows_by_id[
        missing_bank_credit_case["raw_entity_ids"][0]
    ]
    assert missing_bank_credit_row["settlement_utr"] not in bank_utrs

    unresolvable_case = _truth_case_for(truth_cases, BreakClass.UNRESOLVABLE)
    unresolvable_row = reconciliation_rows_by_id[unresolvable_case["raw_entity_ids"][0]]
    missing_evidence_count = sum(
        (
            unresolvable_row["order_id"] not in order_ids,
            unresolvable_row["payment_id"] not in payment_ids,
            unresolvable_row["settlement_utr"] not in bank_utrs,
        )
    )
    assert missing_evidence_count >= 2
    assert reconciliation_rows


def test_messy_generation_is_deterministic_for_equivalent_profiles() -> None:
    generate_messy_dataset, _ = _load_messy_generator_interfaces()

    first = generate_messy_dataset(seed=2202, profile=_coverage_profile())
    second = generate_messy_dataset(seed=2202, profile=_coverage_profile())

    assert first.raw_inputs == second.raw_inputs
    assert first.ground_truth == second.ground_truth
    assert first.input_hash == second.input_hash


def test_messy_input_hash_is_derived_only_from_canonical_raw_input_content() -> None:
    dataset = _messy_dataset()
    raw_inputs = _raw_inputs(dataset)
    truth_cases = _truth_cases(dataset)
    original_input_hash = dataset.input_hash
    canonical_raw_input_content = dumps(
        raw_inputs, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")

    assert original_input_hash == sha256(canonical_raw_input_content).hexdigest()
    dumps(dataset.ground_truth, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    truth_cases[0]["break_class"] = "TEST_ONLY_TRUTH_CHANGE"
    assert dataset.input_hash == original_input_hash


def test_messy_raw_money_values_are_integer_paise() -> None:
    raw_inputs = _raw_inputs(_messy_dataset())
    monetary_field_names = {
        "amount_paise",
        "debit_paise",
        "credit_paise",
        "debit",
        "credit",
        "amount",
        "fee",
        "tax",
    }

    def assert_integer_money(value: Any) -> None:
        if isinstance(value, Mapping):
            for field_name, nested_value in value.items():
                if field_name in monetary_field_names:
                    assert type(nested_value) is int
                assert_integer_money(nested_value)
        elif isinstance(value, list):
            for nested_value in value:
                assert_integer_money(nested_value)

    assert_integer_money(raw_inputs)


def test_added_refund_and_adjustment_scenarios_have_corresponding_bank_evidence() -> None:
    dataset = _messy_dataset()
    raw_inputs = _raw_inputs(dataset)
    truth_cases = _truth_cases(dataset)
    reconciliation_rows_by_id = _reconciliation_rows_by_entity_id(raw_inputs)
    bank_utrs = {
        bank_transaction["utr"] for bank_transaction in _records(raw_inputs, "bank_transactions")
    }

    for break_class in (
        BreakClass.REFUND_NETTED_LATER,
        BreakClass.PARTIAL_REFUND,
        BreakClass.DISPUTE_ADJUSTMENT,
        BreakClass.GENERAL_ADJUSTMENT,
    ):
        truth_case = _truth_case_for(truth_cases, break_class)
        row = reconciliation_rows_by_id[truth_case["raw_entity_ids"][0]]
        assert isinstance(row["settlement_id"], str) and row["settlement_id"]
        assert row["settlement_utr"] in bank_utrs


def test_missing_settlement_removes_all_settlement_identity_from_affected_raw_row() -> None:
    dataset = _messy_dataset()
    truth_case = _truth_case_for(_truth_cases(dataset), BreakClass.MISSING_SETTLEMENT)
    row = _reconciliation_rows_by_entity_id(_raw_inputs(dataset))[truth_case["raw_entity_ids"][0]]

    assert row["settlement_id"] is None
    assert row["settlement_utr"] is None
    assert row["settled"] is False


def test_unresolvable_case_has_no_original_identity_or_settlement_shortcut() -> None:
    dataset = _messy_dataset()
    raw_inputs = _raw_inputs(dataset)
    truth_case = _truth_case_for(_truth_cases(dataset), BreakClass.UNRESOLVABLE)
    row = _reconciliation_rows_by_entity_id(raw_inputs)[truth_case["raw_entity_ids"][0]]
    order_ids = {order["order_id"] for order in _records(raw_inputs, "orders")}
    payment_ids = {payment["payment_id"] for payment in _records(raw_inputs, "payments")}
    bank_utrs = {
        bank_transaction["utr"] for bank_transaction in _records(raw_inputs, "bank_transactions")
    }

    assert row["order_id"] not in order_ids
    assert row["order_receipt"] is None
    assert row["payment_id"] not in payment_ids
    assert row["settlement_id"] is None
    assert row["settlement_utr"] not in bank_utrs


def test_mangled_narration_case_has_no_untouched_exact_bank_reference() -> None:
    generate_messy_dataset, scenario_distribution = _load_messy_generator_interfaces()
    profile = scenario_distribution(scenario_counts={BreakClass.MANGLED_NARRATION: 1})
    dataset = generate_messy_dataset(seed=2202, profile=profile)
    raw_inputs = _raw_inputs(dataset)
    truth_case = _truth_case_for(_truth_cases(dataset), BreakClass.MANGLED_NARRATION)
    row = _reconciliation_rows_by_entity_id(raw_inputs)[truth_case["raw_entity_ids"][0]]
    exact_bank_references = {
        bank_transaction[field_name]
        for bank_transaction in _records(raw_inputs, "bank_transactions")
        for field_name in ("utr", "reference")
    }

    assert row["settlement_utr"] not in exact_bank_references


def test_multiple_messy_occurrences_receive_distinct_primary_raw_targets() -> None:
    generate_messy_dataset, scenario_distribution = _load_messy_generator_interfaces()
    profile = scenario_distribution(scenario_counts={BreakClass.ROUNDING_VARIANCE: 161})

    dataset = generate_messy_dataset(seed=2202, profile=profile)
    truth_cases = _truth_cases(dataset)
    primary_raw_entity_ids = [truth_case["raw_entity_ids"][0] for truth_case in truth_cases]

    assert len(primary_raw_entity_ids) == 161
    assert len(set(primary_raw_entity_ids)) == len(primary_raw_entity_ids)


def test_truth_cases_do_not_share_mutable_settlement_bank_evidence() -> None:
    dataset = _messy_dataset()
    raw_inputs = _raw_inputs(dataset)
    rows_by_entity_id = _reconciliation_rows_by_entity_id(raw_inputs)
    truth_cases = _truth_cases(dataset)
    settlement_owner_by_utr: dict[str, str] = {}

    for truth_case in truth_cases:
        row = rows_by_entity_id[truth_case["raw_entity_ids"][0]]
        settlement_utr = row["settlement_utr"]
        if not isinstance(settlement_utr, str):
            continue
        previous_owner = settlement_owner_by_utr.setdefault(settlement_utr, truth_case["case_id"])
        assert previous_owner == truth_case["case_id"], (
            f"{truth_case['case_id']} shares mutable settlement evidence with {previous_owner}"
        )

    duplicate_case = _truth_case_for(truth_cases, BreakClass.DUPLICATE_BANK_CREDIT)
    duplicate_row = rows_by_entity_id[duplicate_case["raw_entity_ids"][0]]
    duplicate_utr = duplicate_row["settlement_utr"]
    assert isinstance(duplicate_utr, str)
    other_truth_utrs = {
        rows_by_entity_id[case["raw_entity_ids"][0]]["settlement_utr"]
        for case in truth_cases
        if case["case_id"] != duplicate_case["case_id"]
    }
    assert duplicate_utr not in other_truth_utrs


def test_non_bank_break_scenarios_keep_settlement_net_equal_to_bank_evidence() -> None:
    generate_messy_dataset, scenario_distribution = _load_messy_generator_interfaces()
    bank_coherent_break_classes = (
        BreakClass.FEE_VARIANCE,
        BreakClass.TAX_VARIANCE,
        BreakClass.INSTANT_SETTLEMENT_VARIANCE,
        BreakClass.REFUND_NETTED_LATER,
        BreakClass.PARTIAL_REFUND,
        BreakClass.DISPUTE_ADJUSTMENT,
        BreakClass.GENERAL_ADJUSTMENT,
    )

    for break_class in bank_coherent_break_classes:
        dataset = generate_messy_dataset(
            seed=2202,
            profile=scenario_distribution(scenario_counts={break_class: 1}),
        )
        raw_inputs = _raw_inputs(dataset)
        truth_case = _truth_case_for(_truth_cases(dataset), break_class)
        row = _reconciliation_rows_by_entity_id(raw_inputs)[truth_case["raw_entity_ids"][0]]
        settlement_utr = row["settlement_utr"]
        assert isinstance(settlement_utr, str)
        settlement_rows = [
            candidate
            for candidate in _records(raw_inputs, "reconciliation_rows")
            if candidate["settlement_utr"] == settlement_utr
        ]
        matching_bank_transactions = [
            transaction
            for transaction in _records(raw_inputs, "bank_transactions")
            if transaction["utr"] == settlement_utr
        ]

        assert len(matching_bank_transactions) == 1
        expected_net_paise = sum(
            row["credit"] - row["debit"] - row["fee"] - row["tax"] for row in settlement_rows
        )
        bank_transaction = matching_bank_transactions[0]
        assert bank_transaction["credit_paise"] - bank_transaction["debit_paise"] == (
            expected_net_paise
        )


def _load_dataset_role_interfaces() -> tuple[type[Any], Mapping[Any, int], Callable[[Any], Any]]:
    config_module = REPOSITORY_ROOT / "generator" / "src" / "config.py"
    roles_module = REPOSITORY_ROOT / "generator" / "src" / "roles.py"
    assert config_module.is_file(), "Task 6 must provide generator/src/config.py"
    assert roles_module.is_file(), "Task 6 must provide generator/src/roles.py"

    config = importlib.import_module("generator.src.config")
    roles = importlib.import_module("generator.src.roles")
    dataset_role = getattr(config, "DatasetRole", None)
    dataset_seeds = getattr(config, "DATASET_SEEDS", None)
    generate_dataset = getattr(roles, "generate_dataset", None)
    assert isinstance(dataset_role, type)
    assert isinstance(dataset_seeds, Mapping)
    assert callable(generate_dataset)
    return dataset_role, dataset_seeds, generate_dataset


def test_task_six_uses_the_approved_fixed_dataset_seeds() -> None:
    dataset_role, dataset_seeds, _ = _load_dataset_role_interfaces()

    assert dataset_seeds == {
        dataset_role.CLEAN: 1101,
        dataset_role.MESSY_DEV: 2202,
        dataset_role.DEMO: 3303,
        dataset_role.HELDOUT: 4404,
        dataset_role.STRESS: 5505,
    }


def test_dataset_roles_produce_the_required_clean_messy_demo_and_heldout_scales() -> None:
    dataset_role, _, generate_dataset = _load_dataset_role_interfaces()

    clean = generate_dataset(dataset_role.CLEAN)
    messy = generate_dataset(dataset_role.MESSY_DEV)
    demo = generate_dataset(dataset_role.DEMO)
    heldout = generate_dataset(dataset_role.HELDOUT)

    assert 60 <= len(clean.raw_inputs["reconciliation_rows"]) <= 80
    assert 150 <= len(messy.raw_inputs["reconciliation_rows"]) <= 200
    assert 240 <= len(demo.raw_inputs["reconciliation_rows"]) <= 250
    assert REQUIRED_MESSY_BREAK_CLASSES <= {
        BreakClass(case["break_class"]) for case in heldout.ground_truth["cases"]
    }


def test_stress_role_is_configured_for_a_ten_thousand_record_fixture() -> None:
    dataset_role, _, generate_dataset = _load_dataset_role_interfaces()

    stress = generate_dataset(dataset_role.STRESS)

    assert len(stress.raw_inputs["reconciliation_rows"]) == 10_000
    assert stress.input_hash


def test_generated_artifacts_keep_raw_sources_and_ground_truth_separate(tmp_path: Path) -> None:
    artifacts_module = REPOSITORY_ROOT / "generator" / "src" / "artifacts.py"
    assert artifacts_module.is_file(), "Task 6 must provide generator/src/artifacts.py"
    artifacts = importlib.import_module("generator.src.artifacts")
    write_dataset_artifacts = getattr(artifacts, "write_dataset_artifacts", None)
    assert callable(write_dataset_artifacts)
    dataset_role, _, generate_dataset = _load_dataset_role_interfaces()

    output_paths = write_dataset_artifacts(generate_dataset(dataset_role.MESSY_DEV), tmp_path)

    assert set(output_paths) == {
        "orders",
        "payments",
        "reconciliation_rows",
        "bank_transactions",
        "ground_truth",
    }
    for source_name in ("orders", "payments", "reconciliation_rows", "bank_transactions"):
        raw_records = loads(output_paths[source_name].read_text(encoding="utf-8"))
        assert isinstance(raw_records, list)
        assert all("expected_break_class" not in record for record in raw_records)
        assert all("expected_match" not in record for record in raw_records)
        assert all("resolvable" not in record for record in raw_records)
    truth = loads(output_paths["ground_truth"].read_text(encoding="utf-8"))
    assert isinstance(truth["cases"], list) and truth["cases"]
