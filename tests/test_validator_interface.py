from __future__ import annotations

from pathlib import Path

import pytest

from src.core.constants import (
    METHOD_RULE_BASED,
)
from src.core.io import (
    load_json,
    prepare_case_for_method,
)
from src.core.models import (
    Prediction,
    PredictionError,
)
from src.core.validator_interface import (
    BaseValidator,
)


ROOT = Path(__file__).resolve().parents[1]

VALID_EXAMPLE_PATH = (
    ROOT / "data" / "toy" / "valid_example.json"
)

INVALID_EXAMPLE_PATH = (
    ROOT / "data" / "toy" / "invalid_example.json"
)


class DummyValidValidator(BaseValidator):
    method_name = METHOD_RULE_BASED

    def _validate_case(
        self,
        case: dict,
    ) -> Prediction:
        return Prediction(
            case_id="",
            method="",
            predicted_valid=True,
            errors=[],
            runtime_ms=0.0,
        )


class DummyInvalidValidator(BaseValidator):
    method_name = METHOD_RULE_BASED

    def _validate_case(
        self,
        case: dict,
    ) -> Prediction:
        return Prediction(
            case_id="",
            method="",
            predicted_valid=False,
            errors=[
                PredictionError(
                    error_type="FK_TARGET_NOT_KEY",
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
            runtime_ms=0.0,
        )


class InvalidMethodValidator(BaseValidator):
    method_name = "not_a_real_method"

    def _validate_case(
        self,
        case: dict,
    ) -> Prediction:
        return Prediction(
            case_id="",
            method="",
            predicted_valid=True,
            errors=[],
            runtime_ms=0.0,
        )


class BadOutputTypeValidator(BaseValidator):
    method_name = METHOD_RULE_BASED

    def _validate_case(
        self,
        case: dict,
    ):
        return {
            "predicted_valid": True
        }


class InvalidValidPredictionValidator(
    BaseValidator
):
    method_name = METHOD_RULE_BASED

    def _validate_case(
        self,
        case: dict,
    ) -> Prediction:
        return Prediction(
            case_id="",
            method="",
            predicted_valid=True,
            errors=[
                PredictionError(
                    error_type=(
                        "FK_TARGET_NOT_KEY"
                    ),
                    message="Unexpected error.",
                )
            ],
            runtime_ms=0.0,
        )


class InvalidEmptyErrorValidator(
    BaseValidator
):
    method_name = METHOD_RULE_BASED

    def _validate_case(
        self,
        case: dict,
    ) -> Prediction:
        return Prediction(
            case_id="",
            method="",
            predicted_valid=False,
            errors=[],
            runtime_ms=0.0,
        )


def test_validator_accepts_safe_case():
    full_case = load_json(
        VALID_EXAMPLE_PATH
    )

    safe_case = prepare_case_for_method(
        full_case
    )

    validator = DummyValidValidator()

    prediction = validator.validate(
        safe_case
    )

    assert isinstance(
        prediction,
        Prediction,
    )

    assert (
        prediction.case_id
        == "TOY_VALID_001"
    )

    assert (
        prediction.method
        == METHOD_RULE_BASED
    )

    assert (
        prediction.predicted_valid
        is True
    )

    assert prediction.errors == []

    assert prediction.runtime_ms >= 0


def test_invalid_case_can_return_errors():
    full_case = load_json(
        INVALID_EXAMPLE_PATH
    )

    safe_case = prepare_case_for_method(
        full_case
    )

    validator = DummyInvalidValidator()

    prediction = validator.validate(
        safe_case
    )

    assert (
        prediction.predicted_valid
        is False
    )

    assert len(
        prediction.errors
    ) == 1

    assert (
        prediction.errors[0].error_type
        == "FK_TARGET_NOT_KEY"
    )


def test_ground_truth_is_rejected():
    full_case = load_json(
        VALID_EXAMPLE_PATH
    )

    validator = DummyValidValidator()

    with pytest.raises(
        ValueError,
        match="Ground truth",
    ):
        validator.validate(
            full_case
        )


def test_missing_case_id_is_rejected():
    full_case = load_json(
        VALID_EXAMPLE_PATH
    )

    safe_case = prepare_case_for_method(
        full_case
    )

    safe_case.pop(
        "case_id"
    )

    validator = DummyValidValidator()

    with pytest.raises(
        ValueError,
        match="case_id",
    ):
        validator.validate(
            safe_case
        )


def test_missing_required_field_is_rejected():
    full_case = load_json(
        VALID_EXAMPLE_PATH
    )

    safe_case = prepare_case_for_method(
        full_case
    )

    safe_case.pop(
        "entities"
    )

    validator = DummyValidValidator()

    with pytest.raises(
        ValueError,
        match="required fields",
    ):
        validator.validate(
            safe_case
        )


def test_invalid_method_name_is_rejected():
    with pytest.raises(
        ValueError,
        match="Invalid method_name",
    ):
        InvalidMethodValidator()


def test_validator_requires_prediction_object():
    full_case = load_json(
        VALID_EXAMPLE_PATH
    )

    safe_case = prepare_case_for_method(
        full_case
    )

    validator = BadOutputTypeValidator()

    with pytest.raises(
        TypeError,
        match="Prediction object",
    ):
        validator.validate(
            safe_case
        )


def test_valid_prediction_cannot_contain_errors():
    full_case = load_json(
        VALID_EXAMPLE_PATH
    )

    safe_case = prepare_case_for_method(
        full_case
    )

    validator = (
        InvalidValidPredictionValidator()
    )

    with pytest.raises(
        ValueError,
        match="marked valid",
    ):
        validator.validate(
            safe_case
        )


def test_invalid_prediction_requires_error():
    full_case = load_json(
        INVALID_EXAMPLE_PATH
    )

    safe_case = prepare_case_for_method(
        full_case
    )

    validator = (
        InvalidEmptyErrorValidator()
    )

    with pytest.raises(
        ValueError,
        match="marked invalid",
    ):
        validator.validate(
            safe_case
        )


def test_validate_batch():
    valid_full = load_json(
        VALID_EXAMPLE_PATH
    )

    invalid_full = load_json(
        INVALID_EXAMPLE_PATH
    )

    cases = [
        prepare_case_for_method(
            valid_full
        ),
        prepare_case_for_method(
            invalid_full
        ),
    ]

    validator = DummyValidValidator()

    predictions = (
        validator.validate_batch(
            cases
        )
    )

    assert len(predictions) == 2

    assert (
        predictions[0].case_id
        == "TOY_VALID_001"
    )

    assert (
        predictions[1].case_id
        == "TOY_INVALID_001"
    )