import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]

SCHEMA_PATH = ROOT / "schemas" / "er_case.schema.json"
VALID_EXAMPLE_PATH = ROOT / "data" / "toy" / "valid_example.json"
INVALID_EXAMPLE_PATH = ROOT / "data" / "toy" / "invalid_example.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(scope="module")
def schema() -> dict:
    return load_json(SCHEMA_PATH)


@pytest.fixture(scope="module")
def validator(schema: dict) -> Draft202012Validator:
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_schema_itself_is_valid(schema):
    """
    Confirm that er_case.schema.json is itself a valid
    JSON Schema Draft 2020-12 document.
    """
    Draft202012Validator.check_schema(schema)


def test_valid_example_matches_schema(validator):
    """
    A logically valid ER case should also be structurally
    valid according to er_case.schema.json.
    """
    case = load_json(VALID_EXAMPLE_PATH)

    errors = sorted(
        validator.iter_errors(case),
        key=lambda error: list(error.path),
    )

    assert errors == [], "\n".join(
        f"{list(error.path)}: {error.message}"
        for error in errors
    )


def test_invalid_er_example_still_matches_schema(validator):
    """
    An ER design may be logically invalid while still being a
    correctly formatted benchmark case.

    The JSON Schema validates structure, not ER correctness.
    """
    case = load_json(INVALID_EXAMPLE_PATH)

    errors = sorted(
        validator.iter_errors(case),
        key=lambda error: list(error.path),
    )

    assert errors == [], "\n".join(
        f"{list(error.path)}: {error.message}"
        for error in errors
    )


def test_missing_required_fields_fails(validator):
    """
    A malformed benchmark case with required fields missing
    must fail schema validation.
    """
    malformed_case = {
        "case_id": "BROKEN_001"
    }

    with pytest.raises(ValidationError):
        validator.validate(malformed_case)


def test_valid_case_cannot_have_ground_truth_errors(validator):
    """
    If ground_truth.valid is true, the errors list must be empty.
    """
    case = load_json(VALID_EXAMPLE_PATH)

    case["ground_truth"] = {
        "valid": True,
        "errors": [
            {
                "error_type": "FK_TARGET_NOT_KEY"
            }
        ]
    }

    with pytest.raises(ValidationError):
        validator.validate(case)


def test_invalid_case_requires_ground_truth_error(validator):
    """
    If ground_truth.valid is false, at least one error label
    must be provided.
    """
    case = load_json(INVALID_EXAMPLE_PATH)

    case["ground_truth"] = {
        "valid": False,
        "errors": []
    }

    with pytest.raises(ValidationError):
        validator.validate(case)


def test_foreign_key_requires_reference_target(validator):
    """
    A foreign-key attribute must include a references object.
    """
    case = load_json(VALID_EXAMPLE_PATH)

    order_entity = next(
        entity
        for entity in case["entities"]
        if entity["name"] == "ORDER"
    )

    customer_id = next(
        attribute
        for attribute in order_entity["attributes"]
        if attribute["name"] == "customer_id"
    )

    customer_id.pop("references")

    with pytest.raises(ValidationError):
        validator.validate(case)