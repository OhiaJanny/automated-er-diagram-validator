import json
from pathlib import Path

import pytest

from src.core.io import (
    case_from_dict,
    case_to_dict,
    load_case_file,
    load_json,
    load_jsonl,
    load_predictions,
    prepare_case_for_method,
    save_json,
    save_jsonl,
    validate_case_dict,
    validate_prediction_dict,
    write_predictions,
)
from src.core.models import (
    ERCase,
    Prediction,
    PredictionError,
)


ROOT = Path(__file__).resolve().parents[1]

VALID_EXAMPLE_PATH = (
    ROOT / "data" / "toy" / "valid_example.json"
)

INVALID_EXAMPLE_PATH = (
    ROOT / "data" / "toy" / "invalid_example.json"
)


def test_load_json():
    case = load_json(VALID_EXAMPLE_PATH)

    assert isinstance(case, dict)
    assert case["case_id"] == "TOY_VALID_001"
    assert case["domain"] == "ecommerce"


def test_load_valid_case_as_dataclass():
    case = load_case_file(VALID_EXAMPLE_PATH)

    assert isinstance(case, ERCase)
    assert case.case_id == "TOY_VALID_001"
    assert case.domain == "ecommerce"
    assert case.ground_truth.valid is True


def test_load_invalid_case_as_dataclass():
    case = load_case_file(INVALID_EXAMPLE_PATH)

    assert isinstance(case, ERCase)
    assert case.case_id == "TOY_INVALID_001"
    assert case.ground_truth.valid is False
    assert len(case.ground_truth.errors) == 1

    assert (
        case.ground_truth.errors[0].error_type
        == "FK_TARGET_NOT_KEY"
    )


def test_entity_lookup():
    case = load_case_file(VALID_EXAMPLE_PATH)

    order = case.get_entity("ORDER")

    assert order is not None
    assert order.name == "ORDER"


def test_attribute_lookup():
    case = load_case_file(VALID_EXAMPLE_PATH)

    order = case.get_entity("ORDER")

    assert order is not None

    customer_id = order.get_attribute(
        "customer_id"
    )

    assert customer_id is not None
    assert customer_id.foreign_key is True
    assert customer_id.references is not None
    assert (
        customer_id.references.entity
        == "CUSTOMER"
    )


def test_prepare_case_removes_ground_truth():
    original = load_json(
        INVALID_EXAMPLE_PATH
    )

    safe_case = prepare_case_for_method(
        original
    )

    assert "ground_truth" not in safe_case
    assert "ground_truth" in original

    assert (
        safe_case["case_id"]
        == original["case_id"]
    )


def test_prepare_case_does_not_modify_original():
    original = load_json(
        INVALID_EXAMPLE_PATH
    )

    original_ground_truth = (
        original["ground_truth"].copy()
    )

    prepare_case_for_method(original)

    assert "ground_truth" in original

    assert (
        original["ground_truth"]
        == original_ground_truth
    )


def test_case_dict_round_trip():
    original = load_json(
        VALID_EXAMPLE_PATH
    )

    case = case_from_dict(original)

    converted = case_to_dict(case)

    validate_case_dict(converted)

    assert (
        converted["case_id"]
        == original["case_id"]
    )

    assert (
        converted["ground_truth"]["valid"]
        is True
    )


def test_save_and_load_json(tmp_path):
    case = load_json(
        VALID_EXAMPLE_PATH
    )

    output_path = (
        tmp_path / "saved_case.json"
    )

    save_json(
        case,
        output_path,
    )

    loaded = load_json(
        output_path
    )

    assert loaded == case


def test_save_and_load_jsonl(tmp_path):
    valid_case = load_json(
        VALID_EXAMPLE_PATH
    )

    invalid_case = load_json(
        INVALID_EXAMPLE_PATH
    )

    output_path = (
        tmp_path / "cases.jsonl"
    )

    save_jsonl(
        [
            valid_case,
            invalid_case,
        ],
        output_path,
    )

    records = load_jsonl(
        output_path
    )

    assert len(records) == 2

    assert (
        records[0]["case_id"]
        == "TOY_VALID_001"
    )

    assert (
        records[1]["case_id"]
        == "TOY_INVALID_001"
    )


def test_invalid_jsonl_raises_error(
    tmp_path,
):
    output_path = (
        tmp_path / "broken.jsonl"
    )

    output_path.write_text(
        '{"case_id": "GOOD"}\n'
        '{"case_id": BAD}\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_jsonl(output_path)


def test_prediction_schema_accepts_valid_prediction():
    prediction = {
        "case_id": "TOY_INVALID_001",
        "method": "rule_based",
        "predicted_valid": False,
        "errors": [
            {
                "error_type": "FK_TARGET_NOT_KEY",
                "entity": "ORDER",
                "attribute": "customer_id",
                "relationship": (
                    "customer_places_order"
                ),
                "message": (
                    "Foreign key references "
                    "a non-key attribute."
                )
            }
        ],
        "runtime_ms": 1.5
    }

    validate_prediction_dict(
        prediction
    )


def test_prediction_write_and_load(
    tmp_path,
):
    prediction = Prediction(
        case_id="TOY_INVALID_001",
        method="rule_based",
        predicted_valid=False,
        errors=[
            PredictionError(
                error_type=(
                    "FK_TARGET_NOT_KEY"
                ),
                entity="ORDER",
                attribute="customer_id",
                relationship=(
                    "customer_places_order"
                ),
                message=(
                    "Foreign key references "
                    "a non-key attribute."
                ),
            )
        ],
        runtime_ms=1.5,
    )

    output_path = (
        tmp_path / "predictions.jsonl"
    )

    write_predictions(
        [prediction],
        output_path,
    )

    loaded = load_predictions(
        output_path
    )

    assert len(loaded) == 1

    assert (
        loaded[0].case_id
        == "TOY_INVALID_001"
    )

    assert (
        loaded[0].method
        == "rule_based"
    )

    assert (
        loaded[0].predicted_valid
        is False
    )

    assert len(
        loaded[0].errors
    ) == 1