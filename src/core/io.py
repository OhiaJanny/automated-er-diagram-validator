from __future__ import annotations

import copy
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from src.core.models import (
    Attribute,
    Entity,
    ERCase,
    GroundTruth,
    GroundTruthError,
    Prediction,
    PredictionError,
    Reference,
    Relationship,
    Requirement,
)


# Project paths

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ER_CASE_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "er_case.schema.json"
)

PREDICTION_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "prediction.schema.json"
)


# Basic JSON utilities

def load_json(path: str | Path) -> dict[str, Any]:
    """
    Load one JSON object from disk.
    """
    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(
    data: dict[str, Any],
    path: str | Path,
    indent: int = 2,
) -> None:
    """
    Save one dictionary as a formatted JSON file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=indent,
            ensure_ascii=False,
        )


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """
    Load a JSON Lines file.

    Each non-empty line must contain exactly one JSON object.
    """
    path = Path(path)
    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()

            if not stripped:
                continue

            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {path} at line "
                    f"{line_number}: {error}"
                ) from error

            if not isinstance(record, dict):
                raise ValueError(
                    f"Expected a JSON object in {path} at "
                    f"line {line_number}."
                )

            records.append(record)

    return records


def save_jsonl(
    records: Iterable[dict[str, Any]],
    path: str | Path,
) -> None:
    """
    Save dictionaries in JSON Lines format.

    One JSON object is written per line.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
            )
            file.write("\n")


# Schema loading and validation

def load_schema(path: str | Path) -> dict[str, Any]:
    """
    Load and verify a JSON Schema document.
    """
    schema = load_json(path)

    Draft202012Validator.check_schema(schema)

    return schema


def get_er_case_validator() -> Draft202012Validator:
    """
    Return a validator for ER benchmark cases.
    """
    schema = load_schema(ER_CASE_SCHEMA_PATH)

    return Draft202012Validator(schema)


def get_prediction_validator() -> Draft202012Validator:
    """
    Return a validator for method predictions.
    """
    schema = load_schema(PREDICTION_SCHEMA_PATH)

    return Draft202012Validator(schema)


def validate_case_dict(case: dict[str, Any]) -> None:
    """
    Validate one ER case dictionary.
    """
    validator = get_er_case_validator()
    validator.validate(case)


def validate_prediction_dict(
    prediction: dict[str, Any],
) -> None:
    """
    Validate one prediction dictionary.
    """
    validator = get_prediction_validator()
    validator.validate(prediction)


# Dictionary to dataclass conversion

def reference_from_dict(
    data: dict[str, Any],
) -> Reference:
    return Reference(
        entity=data["entity"],
        attribute=data["attribute"],
    )


def attribute_from_dict(
    data: dict[str, Any],
) -> Attribute:
    references = None

    if data.get("references") is not None:
        references = reference_from_dict(
            data["references"]
        )

    return Attribute(
        name=data["name"],
        type=data["type"],
        primary_key=data["primary_key"],
        nullable=data["nullable"],
        foreign_key=data.get(
            "foreign_key",
            False,
        ),
        unique=data.get(
            "unique",
            False,
        ),
        references=references,
    )


def entity_from_dict(
    data: dict[str, Any],
) -> Entity:
    return Entity(
        name=data["name"],
        attributes=[
            attribute_from_dict(attribute)
            for attribute in data["attributes"]
        ],
    )


def relationship_from_dict(
    data: dict[str, Any],
) -> Relationship:
    return Relationship(
        name=data["name"],
        parent=data["parent"],
        child=data["child"],
        parent_cardinality=data[
            "parent_cardinality"
        ],
        child_cardinality=data[
            "child_cardinality"
        ],
        identifying=data["identifying"],
    )


def requirement_from_dict(
    data: dict[str, Any],
) -> Requirement:
    return Requirement(
        requirement_id=data["requirement_id"],
        text=data["text"],
        type=data.get("type"),
        source=data.get("source"),
        target=data.get("target"),
        source_min=data.get("source_min"),
        source_max=data.get("source_max"),
        target_min=data.get("target_min"),
        target_max=data.get("target_max"),
    )


def ground_truth_error_from_dict(
    data: dict[str, Any],
) -> GroundTruthError:
    return GroundTruthError(
        error_type=data["error_type"],
        entity=data.get("entity"),
        attribute=data.get("attribute"),
        relationship=data.get("relationship"),
        details=data.get(
            "details",
            {},
        ),
    )


def ground_truth_from_dict(
    data: dict[str, Any],
) -> GroundTruth:
    return GroundTruth(
        valid=data["valid"],
        errors=[
            ground_truth_error_from_dict(error)
            for error in data["errors"]
        ],
    )


def case_from_dict(
    data: dict[str, Any],
    validate: bool = True,
) -> ERCase:
    """
    Convert a complete ER case dictionary into an ERCase object.
    """
    if validate:
        validate_case_dict(data)

    return ERCase(
        case_id=data["case_id"],
        domain=data["domain"],
        description=data.get(
            "description",
            "",
        ),
        entities=[
            entity_from_dict(entity)
            for entity in data["entities"]
        ],
        relationships=[
            relationship_from_dict(relationship)
            for relationship in data["relationships"]
        ],
        requirements=[
            requirement_from_dict(requirement)
            for requirement in data["requirements"]
        ],
        metadata=data["metadata"],
        ground_truth=ground_truth_from_dict(
            data["ground_truth"]
        ),
    )


# Prediction conversion

def prediction_error_from_dict(
    data: dict[str, Any],
) -> PredictionError:
    return PredictionError(
        error_type=data["error_type"],
        message=data["message"],
        entity=data.get("entity"),
        attribute=data.get("attribute"),
        relationship=data.get("relationship"),
        details=data.get(
            "details",
            {},
        ),
    )


def prediction_from_dict(
    data: dict[str, Any],
    validate: bool = True,
) -> Prediction:
    """
    Convert a prediction dictionary into a Prediction object.
    """
    if validate:
        validate_prediction_dict(data)

    return Prediction(
        case_id=data["case_id"],
        method=data["method"],
        predicted_valid=data["predicted_valid"],
        errors=[
            prediction_error_from_dict(error)
            for error in data["errors"]
        ],
        runtime_ms=data["runtime_ms"],
    )


# Dataclass to dictionary conversion

def remove_none_values(data: Any) -> Any:
    """
    Recursively remove dictionary fields whose value is None.
    """
    if isinstance(data, dict):
        return {
            key: remove_none_values(value)
            for key, value in data.items()
            if value is not None
        }

    if isinstance(data, list):
        return [
            remove_none_values(value)
            for value in data
        ]

    return data


def case_to_dict(case: ERCase) -> dict[str, Any]:
    """
    Convert an ERCase object to a schema-compatible dictionary.
    """
    return remove_none_values(
        asdict(case)
    )


def prediction_to_dict(
    prediction: Prediction,
) -> dict[str, Any]:
    """
    Convert a Prediction object to a schema-compatible dictionary.
    """
    return remove_none_values(
        asdict(prediction)
    )


# Safe method input

def strip_ground_truth(
    case: dict[str, Any],
) -> dict[str, Any]:
    """
    Return a deep copy of an ER case without ground truth.
    """
    safe_case = copy.deepcopy(case)

    safe_case.pop(
        "ground_truth",
        None,
    )

    return safe_case


def prepare_case_for_method(
    case: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate a complete benchmark case and return a
    prediction-safe copy with ground truth removed.
    """
    validate_case_dict(case)

    return strip_ground_truth(case)


# Dataset loading

def load_case_file(
    path: str | Path,
) -> ERCase:
    """
    Load and validate one JSON ER case file.
    """
    data = load_json(path)

    return case_from_dict(
        data,
        validate=True,
    )


def load_case_jsonl(
    path: str | Path,
) -> list[ERCase]:
    """
    Load and validate all ER cases in one JSONL file.
    """
    records = load_jsonl(path)

    return [
        case_from_dict(
            record,
            validate=True,
        )
        for record in records
    ]


def load_method_inputs(
    path: str | Path,
) -> list[dict[str, Any]]:
    """
    Load a JSONL dataset and return copies without
    ground-truth labels.
    """
    records = load_jsonl(path)

    method_inputs = []

    for record in records:
        method_inputs.append(
            prepare_case_for_method(record)
        )

    return method_inputs


# Prediction loading and writing

def load_predictions(
    path: str | Path,
) -> list[Prediction]:
    """
    Load prediction JSONL and validate every prediction.
    """
    records = load_jsonl(path)

    return [
        prediction_from_dict(
            record,
            validate=True,
        )
        for record in records
    ]


def write_predictions(
    predictions: Iterable[
        Prediction | dict[str, Any]
    ],
    path: str | Path,
) -> None:
    """
    Validate and write predictions to JSONL.
    """
    output_records = []

    for prediction in predictions:

        if isinstance(
            prediction,
            Prediction,
        ):
            record = prediction_to_dict(
                prediction
            )
        else:
            record = prediction

        validate_prediction_dict(record)

        output_records.append(record)

    save_jsonl(
        output_records,
        path,
    )