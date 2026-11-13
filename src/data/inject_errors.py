from __future__ import annotations

import copy
import random
from typing import Any

from src.core.constants import (
    ERROR_CARDINALITY_UNIQUENESS_CONFLICT,
    ERROR_COMPOSITE_FK_INCOMPLETE,
    ERROR_FK_TARGET_NOT_KEY,
    ERROR_FK_WRONG_ENTITY,
    ERROR_IDENTIFYING_RELATIONSHIP_KEY_ERROR,
    ERROR_MISSING_REQUIRED_RELATIONSHIP,
    ERROR_PARTICIPATION_OPTIONALITY_CONFLICT,
)
from src.core.io import (
    validate_case_dict,
)


MUTATION_VERSION = "2.0"


ERROR_ORDER = (
    ERROR_FK_TARGET_NOT_KEY,
    ERROR_FK_WRONG_ENTITY,
    ERROR_COMPOSITE_FK_INCOMPLETE,
    ERROR_CARDINALITY_UNIQUENESS_CONFLICT,
    ERROR_PARTICIPATION_OPTIONALITY_CONFLICT,
    ERROR_IDENTIFYING_RELATIONSHIP_KEY_ERROR,
    ERROR_MISSING_REQUIRED_RELATIONSHIP,
)


def get_entity(
    case: dict[str, Any],
    entity_name: str,
) -> dict[str, Any]:
    for entity in case["entities"]:
        if entity["name"] == entity_name:
            return entity

    raise ValueError(
        f"Entity not found: {entity_name}"
    )


def get_attribute(
    entity: dict[str, Any],
    attribute_name: str,
) -> dict[str, Any]:
    for attribute in entity["attributes"]:
        if attribute["name"] == attribute_name:
            return attribute

    raise ValueError(
        f"Attribute not found: "
        f"{entity['name']}."
        f"{attribute_name}"
    )


def primary_key_attributes(
    entity: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        attribute
        for attribute in entity["attributes"]
        if attribute.get(
            "primary_key",
            False,
        )
    ]


def foreign_keys_to_parent(
    case: dict[str, Any],
    relationship: dict[str, Any],
) -> list[dict[str, Any]]:
    child = get_entity(
        case,
        relationship["child"],
    )

    parent_name = (
        relationship["parent"]
    )

    result = []

    for attribute in child["attributes"]:

        if not attribute.get(
            "foreign_key",
            False,
        ):
            continue

        reference = attribute.get(
            "references"
        )

        if reference is None:
            continue

        if (
            reference["entity"]
            == parent_name
        ):
            result.append(attribute)

    return result


def choose_candidate(
    candidates: list[Any],
    seed: int,
) -> Any:
    if not candidates:
        raise ValueError(
            "No eligible mutation candidate."
        )

    rng = random.Random(seed)

    return rng.choice(candidates)


def candidates_fk_target_not_key(
    case: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates = []

    for relationship in case[
        "relationships"
    ]:

        parent = get_entity(
            case,
            relationship["parent"],
        )

        parent_pk = (
            primary_key_attributes(
                parent
            )
        )

        if len(parent_pk) != 1:
            continue

        child_fks = (
            foreign_keys_to_parent(
                case,
                relationship,
            )
        )

        for child_fk in child_fks:

            for target in parent[
                "attributes"
            ]:

                if target.get(
                    "primary_key",
                    False,
                ):
                    continue

                if target.get(
                    "unique",
                    False,
                ):
                    continue

                if (
                    target["type"]
                    != child_fk["type"]
                ):
                    continue

                candidates.append(
                    {
                        "relationship": (
                            relationship
                        ),
                        "child_fk": (
                            child_fk
                        ),
                        "target": target,
                    }
                )

    return candidates


def candidates_fk_wrong_entity(
    case: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates = []

    for relationship in case[
        "relationships"
    ]:

        parent = get_entity(
            case,
            relationship["parent"],
        )

        parent_pk = (
            primary_key_attributes(
                parent
            )
        )

        if len(parent_pk) != 1:
            continue

        child_fks = (
            foreign_keys_to_parent(
                case,
                relationship,
            )
        )

        for child_fk in child_fks:

            for alternative in case[
                "entities"
            ]:

                if (
                    alternative["name"]
                    == parent["name"]
                ):
                    continue

                alternative_pk = (
                    primary_key_attributes(
                        alternative
                    )
                )

                if (
                    len(alternative_pk)
                    != 1
                ):
                    continue

                alternative_key = (
                    alternative_pk[0]
                )

                if (
                    alternative_key["type"]
                    != child_fk["type"]
                ):
                    continue

                candidates.append(
                    {
                        "relationship": (
                            relationship
                        ),
                        "child_fk": (
                            child_fk
                        ),
                        "alternative_entity": (
                            alternative
                        ),
                        "alternative_key": (
                            alternative_key
                        ),
                    }
                )

    return candidates


def candidates_composite_fk_incomplete(
    case: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates = []

    for relationship in case[
        "relationships"
    ]:

        parent = get_entity(
            case,
            relationship["parent"],
        )

        parent_pk = (
            primary_key_attributes(
                parent
            )
        )

        if len(parent_pk) < 2:
            continue

        child_fks = (
            foreign_keys_to_parent(
                case,
                relationship,
            )
        )

        referenced_parent_attributes = {
            attribute["references"][
                "attribute"
            ]
            for attribute in child_fks
            if attribute.get(
                "references"
            )
        }

        required_parent_attributes = {
            attribute["name"]
            for attribute in parent_pk
        }

        if (
            referenced_parent_attributes
            != required_parent_attributes
        ):
            continue

        candidates.append(
            {
                "relationship": (
                    relationship
                ),
                "parent_pk": parent_pk,
                "child_fks": child_fks,
            }
        )

    return candidates


def candidates_cardinality_uniqueness(
    case: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates = []

    for relationship in case[
        "relationships"
    ]:

        if (
            relationship[
                "child_cardinality"
            ]
            not in {
                "0..1",
                "1",
            }
        ):
            continue

        child_fks = (
            foreign_keys_to_parent(
                case,
                relationship,
            )
        )

        if len(child_fks) != 1:
            continue

        child_fk = child_fks[0]

        if not child_fk.get(
            "unique",
            False,
        ):
            continue

        candidates.append(
            {
                "relationship": (
                    relationship
                ),
                "child_fk": (
                    child_fk
                ),
            }
        )

    return candidates


def candidates_participation_optionality(
    case: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates = []

    for relationship in case[
        "relationships"
    ]:

        if (
            relationship[
                "parent_cardinality"
            ]
            != "1"
        ):
            continue

        child_fks = (
            foreign_keys_to_parent(
                case,
                relationship,
            )
        )

        if len(child_fks) != 1:
            continue

        child_fk = child_fks[0]

        if child_fk.get(
            "nullable",
            False,
        ):
            continue

        candidates.append(
            {
                "relationship": (
                    relationship
                ),
                "child_fk": (
                    child_fk
                ),
            }
        )

    return candidates


def candidates_identifying_key_error(
    case: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates = []

    for relationship in case[
        "relationships"
    ]:

        if not relationship.get(
            "identifying",
            False,
        ):
            continue

        child_fks = (
            foreign_keys_to_parent(
                case,
                relationship,
            )
        )

        primary_fks = [
            attribute
            for attribute in child_fks
            if attribute.get(
                "primary_key",
                False,
            )
        ]

        if not primary_fks:
            continue

        candidates.append(
            {
                "relationship": (
                    relationship
                ),
                "child_fks": (
                    primary_fks
                ),
            }
        )

    return candidates


def candidates_missing_relationship(
    case: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates = []

    for relationship in case[
        "relationships"
    ]:

        child_fks = (
            foreign_keys_to_parent(
                case,
                relationship,
            )
        )

        if not child_fks:
            continue

        candidates.append(
            {
                "relationship": (
                    relationship
                ),
                "child_fks": (
                    child_fks
                ),
            }
        )

    return candidates


CANDIDATE_FUNCTIONS = {
    ERROR_FK_TARGET_NOT_KEY: (
        candidates_fk_target_not_key
    ),
    ERROR_FK_WRONG_ENTITY: (
        candidates_fk_wrong_entity
    ),
    ERROR_COMPOSITE_FK_INCOMPLETE: (
        candidates_composite_fk_incomplete
    ),
    ERROR_CARDINALITY_UNIQUENESS_CONFLICT: (
        candidates_cardinality_uniqueness
    ),
    ERROR_PARTICIPATION_OPTIONALITY_CONFLICT: (
        candidates_participation_optionality
    ),
    ERROR_IDENTIFYING_RELATIONSHIP_KEY_ERROR: (
        candidates_identifying_key_error
    ),
    ERROR_MISSING_REQUIRED_RELATIONSHIP: (
        candidates_missing_relationship
    ),
}


def eligible_error_types(
    case: dict[str, Any],
) -> list[str]:
    """
    Return all error types that can be injected
    into this valid case without relying on
    dataset-specific entity names.
    """
    result = []

    for error_type in ERROR_ORDER:

        candidate_function = (
            CANDIDATE_FUNCTIONS[
                error_type
            ]
        )

        if candidate_function(case):
            result.append(error_type)

    return result


def finalize_invalid_case(
    case: dict[str, Any],
    *,
    original_case_id: str,
    case_id: str,
    error_type: str,
    entity: str | None,
    attribute: str | None,
    relationship: str | None,
    details: dict[str, Any],
    seed: int,
) -> dict[str, Any]:

    case["case_id"] = case_id

    case["metadata"] = copy.deepcopy(
        case["metadata"]
    )

    case["metadata"][
        "parent_case_id"
    ] = original_case_id

    case["metadata"][
        "mutation"
    ] = error_type

    case["metadata"][
        "mutation_version"
    ] = MUTATION_VERSION

    case["metadata"][
        "mutation_seed"
    ] = seed

    case["metadata"][
        "error_count"
    ] = 1

    error: dict[str, Any] = {
        "error_type": error_type,
        "details": details,
    }

    if entity is not None:
        error["entity"] = entity

    if attribute is not None:
        error["attribute"] = (
            attribute
        )

    if relationship is not None:
        error["relationship"] = (
            relationship
        )

    case["ground_truth"] = {
        "valid": False,
        "errors": [error],
    }

    validate_case_dict(case)

    return case


def inject_fk_target_not_key(
    base_case: dict[str, Any],
    *,
    case_id: str,
    seed: int,
) -> dict[str, Any]:

    case = copy.deepcopy(
        base_case
    )

    candidate = choose_candidate(
        candidates_fk_target_not_key(
            case
        ),
        seed,
    )

    relationship = (
        candidate["relationship"]
    )

    child_fk = (
        candidate["child_fk"]
    )

    target = candidate["target"]

    old_reference = copy.deepcopy(
        child_fk["references"]
    )

    child_fk["references"] = {
        "entity": (
            relationship["parent"]
        ),
        "attribute": target["name"],
    }

    return finalize_invalid_case(
        case,
        original_case_id=(
            base_case["case_id"]
        ),
        case_id=case_id,
        error_type=(
            ERROR_FK_TARGET_NOT_KEY
        ),
        entity=relationship["child"],
        attribute=child_fk["name"],
        relationship=(
            relationship["name"]
        ),
        details={
            "original_reference": (
                old_reference
            ),
            "mutated_reference": (
                child_fk["references"]
            ),
            "reason": (
                "Foreign key references "
                "a non-key attribute."
            ),
        },
        seed=seed,
    )


def inject_fk_wrong_entity(
    base_case: dict[str, Any],
    *,
    case_id: str,
    seed: int,
) -> dict[str, Any]:

    case = copy.deepcopy(
        base_case
    )

    candidate = choose_candidate(
        candidates_fk_wrong_entity(
            case
        ),
        seed,
    )

    relationship = (
        candidate["relationship"]
    )

    child_fk = (
        candidate["child_fk"]
    )

    alternative_entity = (
        candidate[
            "alternative_entity"
        ]
    )

    alternative_key = (
        candidate["alternative_key"]
    )

    expected_parent = (
        relationship["parent"]
    )

    old_reference = copy.deepcopy(
        child_fk["references"]
    )

    child_fk["references"] = {
        "entity": (
            alternative_entity["name"]
        ),
        "attribute": (
            alternative_key["name"]
        ),
    }

    return finalize_invalid_case(
        case,
        original_case_id=(
            base_case["case_id"]
        ),
        case_id=case_id,
        error_type=(
            ERROR_FK_WRONG_ENTITY
        ),
        entity=relationship["child"],
        attribute=child_fk["name"],
        relationship=(
            relationship["name"]
        ),
        details={
            "expected_parent": (
                expected_parent
            ),
            "original_reference": (
                old_reference
            ),
            "mutated_reference": (
                child_fk["references"]
            ),
        },
        seed=seed,
    )


def inject_composite_fk_incomplete(
    base_case: dict[str, Any],
    *,
    case_id: str,
    seed: int,
) -> dict[str, Any]:

    case = copy.deepcopy(
        base_case
    )

    candidate = choose_candidate(
        candidates_composite_fk_incomplete(
            case
        ),
        seed,
    )

    relationship = (
        candidate["relationship"]
    )

    child_fks = (
        candidate["child_fks"]
    )

    rng = random.Random(seed)

    removed_component = rng.choice(
        child_fks
    )

    removed_reference = copy.deepcopy(
        removed_component[
            "references"
        ]
    )

    removed_component[
        "foreign_key"
    ] = False

    removed_component.pop(
        "references",
        None,
    )

    remaining_components = [
        attribute["name"]
        for attribute in child_fks
        if attribute is not removed_component
    ]

    return finalize_invalid_case(
        case,
        original_case_id=(
            base_case["case_id"]
        ),
        case_id=case_id,
        error_type=(
            ERROR_COMPOSITE_FK_INCOMPLETE
        ),
        entity=relationship["child"],
        attribute=(
            removed_component["name"]
        ),
        relationship=(
            relationship["name"]
        ),
        details={
            "removed_component": (
                removed_component["name"]
            ),
            "removed_reference": (
                removed_reference
            ),
            "remaining_components": (
                remaining_components
            ),
        },
        seed=seed,
    )


def inject_cardinality_uniqueness_conflict(
    base_case: dict[str, Any],
    *,
    case_id: str,
    seed: int,
) -> dict[str, Any]:

    case = copy.deepcopy(
        base_case
    )

    candidate = choose_candidate(
        candidates_cardinality_uniqueness(
            case
        ),
        seed,
    )

    relationship = (
        candidate["relationship"]
    )

    child_fk = (
        candidate["child_fk"]
    )

    child_fk["unique"] = False

    return finalize_invalid_case(
        case,
        original_case_id=(
            base_case["case_id"]
        ),
        case_id=case_id,
        error_type=(
            ERROR_CARDINALITY_UNIQUENESS_CONFLICT
        ),
        entity=relationship["child"],
        attribute=child_fk["name"],
        relationship=(
            relationship["name"]
        ),
        details={
            "declared_child_cardinality": (
                relationship[
                    "child_cardinality"
                ]
            ),
            "foreign_key_unique": False,
        },
        seed=seed,
    )


def inject_participation_optionality_conflict(
    base_case: dict[str, Any],
    *,
    case_id: str,
    seed: int,
) -> dict[str, Any]:

    case = copy.deepcopy(
        base_case
    )

    candidate = choose_candidate(
        candidates_participation_optionality(
            case
        ),
        seed,
    )

    relationship = (
        candidate["relationship"]
    )

    child_fk = (
        candidate["child_fk"]
    )

    child_fk["nullable"] = True

    return finalize_invalid_case(
        case,
        original_case_id=(
            base_case["case_id"]
        ),
        case_id=case_id,
        error_type=(
            ERROR_PARTICIPATION_OPTIONALITY_CONFLICT
        ),
        entity=relationship["child"],
        attribute=child_fk["name"],
        relationship=(
            relationship["name"]
        ),
        details={
            "required_parent_cardinality": (
                relationship[
                    "parent_cardinality"
                ]
            ),
            "foreign_key_nullable": True,
        },
        seed=seed,
    )


def inject_identifying_relationship_key_error(
    base_case: dict[str, Any],
    *,
    case_id: str,
    seed: int,
) -> dict[str, Any]:

    case = copy.deepcopy(
        base_case
    )

    candidate = choose_candidate(
        candidates_identifying_key_error(
            case
        ),
        seed,
    )

    relationship = (
        candidate["relationship"]
    )

    child_fks = (
        candidate["child_fks"]
    )

    rng = random.Random(seed)

    removed_key_component = (
        rng.choice(child_fks)
    )

    removed_key_component[
        "primary_key"
    ] = False

    return finalize_invalid_case(
        case,
        original_case_id=(
            base_case["case_id"]
        ),
        case_id=case_id,
        error_type=(
            ERROR_IDENTIFYING_RELATIONSHIP_KEY_ERROR
        ),
        entity=relationship["child"],
        attribute=(
            removed_key_component[
                "name"
            ]
        ),
        relationship=(
            relationship["name"]
        ),
        details={
            "parent_entity": (
                relationship["parent"]
            ),
            "removed_child_key_component": (
                removed_key_component[
                    "name"
                ]
            ),
        },
        seed=seed,
    )


def inject_missing_required_relationship(
    base_case: dict[str, Any],
    *,
    case_id: str,
    seed: int,
) -> dict[str, Any]:

    case = copy.deepcopy(
        base_case
    )

    candidate = choose_candidate(
        candidates_missing_relationship(
            case
        ),
        seed,
    )

    relationship = (
        candidate["relationship"]
    )

    relationship_name_value = (
        relationship["name"]
    )

    child_fks = (
        candidate["child_fks"]
    )

    removed_fk_names = []

    for child_fk in child_fks:

        removed_fk_names.append(
            child_fk["name"]
        )

        child_fk[
            "foreign_key"
        ] = False

        child_fk.pop(
            "references",
            None,
        )

    case["relationships"] = [
        existing_relationship
        for existing_relationship
        in case["relationships"]
        if (
            existing_relationship[
                "name"
            ]
            != relationship_name_value
        )
    ]

    return finalize_invalid_case(
        case,
        original_case_id=(
            base_case["case_id"]
        ),
        case_id=case_id,
        error_type=(
            ERROR_MISSING_REQUIRED_RELATIONSHIP
        ),
        entity=relationship["child"],
        attribute=(
            removed_fk_names[0]
            if removed_fk_names
            else None
        ),
        relationship=(
            relationship_name_value
        ),
        details={
            "required_parent": (
                relationship["parent"]
            ),
            "required_child": (
                relationship["child"]
            ),
            "removed_foreign_keys": (
                removed_fk_names
            ),
        },
        seed=seed,
    )


INJECTORS = {
    ERROR_FK_TARGET_NOT_KEY: (
        inject_fk_target_not_key
    ),
    ERROR_FK_WRONG_ENTITY: (
        inject_fk_wrong_entity
    ),
    ERROR_COMPOSITE_FK_INCOMPLETE: (
        inject_composite_fk_incomplete
    ),
    ERROR_CARDINALITY_UNIQUENESS_CONFLICT: (
        inject_cardinality_uniqueness_conflict
    ),
    ERROR_PARTICIPATION_OPTIONALITY_CONFLICT: (
        inject_participation_optionality_conflict
    ),
    ERROR_IDENTIFYING_RELATIONSHIP_KEY_ERROR: (
        inject_identifying_relationship_key_error
    ),
    ERROR_MISSING_REQUIRED_RELATIONSHIP: (
        inject_missing_required_relationship
    ),
}


def inject_error(
    base_case: dict[str, Any],
    error_type: str,
    *,
    case_id: str,
    seed: int,
) -> dict[str, Any]:
    """
    Inject one controlled logical error into
    a valid ER case.
    """
    validate_case_dict(
        base_case
    )

    if not base_case[
        "ground_truth"
    ]["valid"]:
        raise ValueError(
            "Error injection requires "
            "a valid base case."
        )

    if error_type not in INJECTORS:
        raise ValueError(
            f"Unsupported error type: "
            f"{error_type}"
        )

    if (
        error_type
        not in eligible_error_types(
            base_case
        )
    ):
        raise ValueError(
            f"{base_case['case_id']} "
            f"is not eligible for "
            f"{error_type}."
        )

    injector = INJECTORS[
        error_type
    ]

    return injector(
        base_case,
        case_id=case_id,
        seed=seed,
    )