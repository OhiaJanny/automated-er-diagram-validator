from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from src.core.io import (
    save_json,
    validate_case_dict,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "base"
    / "valid_cases"
)

GENERATOR_VERSION = "2.0"
BASE_RANDOM_SEED = 811000


DOMAIN_SPECS = [
    {
        "domain": "ecommerce",
        "a": "CUSTOMER",
        "b": "ORDER",
        "c": "PRODUCT",
        "d": "LINE_ITEM",
    },
    {
        "domain": "university",
        "a": "STUDENT",
        "b": "COURSE",
        "c": "INSTRUCTOR",
        "d": "ENROLLMENT",
    },
    {
        "domain": "healthcare",
        "a": "PATIENT",
        "b": "APPOINTMENT",
        "c": "DOCTOR",
        "d": "TREATMENT",
    },
    {
        "domain": "library",
        "a": "MEMBER",
        "b": "LOAN",
        "c": "BOOK",
        "d": "LOAN_ITEM",
    },
    {
        "domain": "hotel",
        "a": "GUEST",
        "b": "RESERVATION",
        "c": "ROOM",
        "d": "STAY_DETAIL",
    },
    {
        "domain": "banking",
        "a": "CUSTOMER",
        "b": "ACCOUNT",
        "c": "BRANCH",
        "d": "ACCOUNT_HOLDER",
    },
    {
        "domain": "company",
        "a": "EMPLOYEE",
        "b": "PROJECT",
        "c": "DEPARTMENT",
        "d": "ASSIGNMENT",
    },
    {
        "domain": "inventory",
        "a": "SUPPLIER",
        "b": "PRODUCT",
        "c": "WAREHOUSE",
        "d": "STOCK_ENTRY",
    },
    {
        "domain": "airline",
        "a": "PASSENGER",
        "b": "BOOKING",
        "c": "FLIGHT",
        "d": "TICKET",
    },
    {
        "domain": "insurance",
        "a": "POLICYHOLDER",
        "b": "POLICY",
        "c": "AGENT",
        "d": "CLAIM",
    },
    {
        "domain": "logistics",
        "a": "CUSTOMER",
        "b": "SHIPMENT",
        "c": "WAREHOUSE",
        "d": "PACKAGE",
    },
    {
        "domain": "education",
        "a": "LEARNER",
        "b": "PROGRAM",
        "c": "INSTRUCTOR",
        "d": "REGISTRATION",
    },
    {
        "domain": "manufacturing",
        "a": "VENDOR",
        "b": "PURCHASE_ORDER",
        "c": "PART",
        "d": "ORDER_LINE",
    },
    {
        "domain": "media",
        "a": "SUBSCRIBER",
        "b": "SUBSCRIPTION",
        "c": "PLAN",
        "d": "PAYMENT",
    },
]


def id_name(entity_name: str) -> str:
    return f"{entity_name.lower()}_id"


def display_name(entity_name: str) -> str:
    return f"{entity_name.lower()}_name"


def relationship_name(
    parent: str,
    child: str,
) -> str:
    return (
        f"{parent.lower()}_"
        f"{child.lower()}"
    )


def attribute(
    name: str,
    data_type: str,
    *,
    primary_key: bool = False,
    foreign_key: bool = False,
    nullable: bool = False,
    unique: bool = False,
    references: dict[str, str] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": name,
        "type": data_type,
        "primary_key": primary_key,
        "foreign_key": foreign_key,
        "nullable": nullable,
        "unique": unique,
    }

    if references is not None:
        result["references"] = references

    return result


def entity(
    name: str,
    attributes: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "name": name,
        "attributes": attributes,
    }


def standard_entity(
    name: str,
) -> dict[str, Any]:
    return entity(
        name,
        [
            attribute(
                id_name(name),
                "INTEGER",
                primary_key=True,
                unique=True,
            ),
            attribute(
                display_name(name),
                "VARCHAR",
            ),
            attribute(
                "status_code",
                "INTEGER",
            ),
        ],
    )


def relationship(
    parent: str,
    child: str,
    parent_cardinality: str,
    child_cardinality: str,
    *,
    identifying: bool = False,
) -> dict[str, Any]:
    return {
        "name": relationship_name(
            parent,
            child,
        ),
        "parent": parent,
        "child": child,
        "parent_cardinality": (
            parent_cardinality
        ),
        "child_cardinality": (
            child_cardinality
        ),
        "identifying": identifying,
    }


def cardinality_bounds(
    cardinality: str,
) -> tuple[int, int | str]:
    mapping = {
        "0..1": (0, 1),
        "1": (1, 1),
        "0..*": (0, "*"),
        "1..*": (1, "*"),
    }

    return mapping[cardinality]


def requirement_from_relationship(
    relationship_data: dict[str, Any],
    requirement_id: str,
) -> dict[str, Any]:
    parent = relationship_data["parent"]
    child = relationship_data["child"]

    child_to_parent_min, child_to_parent_max = (
        cardinality_bounds(
            relationship_data[
                "parent_cardinality"
            ]
        )
    )

    parent_to_child_min, parent_to_child_max = (
        cardinality_bounds(
            relationship_data[
                "child_cardinality"
            ]
        )
    )

    if child_to_parent_min == 1:
        text = (
            f"Every {child} must be related to "
            f"exactly one {parent}."
        )
    else:
        text = (
            f"Each {child} may be related to "
            f"at most one {parent}."
        )

    return {
        "requirement_id": requirement_id,
        "text": text,
        "type": "relationship_cardinality",
        "source": child,
        "target": parent,
        "source_min": child_to_parent_min,
        "source_max": child_to_parent_max,
        "target_min": parent_to_child_min,
        "target_max": parent_to_child_max,
    }


def requirements_from_relationships(
    relationships: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    requirements = []

    for index, relationship_data in enumerate(
        relationships,
        start=1,
    ):
        requirements.append(
            requirement_from_relationship(
                relationship_data,
                f"R{index}",
            )
        )

    return requirements


def standard_child_with_fk(
    child_name: str,
    parent_name: str,
    *,
    nullable: bool,
    unique: bool = False,
) -> dict[str, Any]:
    child = standard_entity(
        child_name
    )

    child["attributes"].append(
        attribute(
            id_name(parent_name),
            "INTEGER",
            foreign_key=True,
            nullable=nullable,
            unique=unique,
            references={
                "entity": parent_name,
                "attribute": id_name(
                    parent_name
                ),
            },
        )
    )

    return child


def pattern_one_to_many_mandatory(
    spec: dict[str, str],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    str,
]:
    a = spec["a"]
    b = spec["b"]
    c = spec["c"]

    parent = standard_entity(a)

    child = standard_child_with_fk(
        b,
        a,
        nullable=False,
    )

    optional_parent = standard_entity(c)

    child["attributes"].append(
        attribute(
            id_name(c),
            "INTEGER",
            foreign_key=True,
            nullable=True,
            references={
                "entity": c,
                "attribute": id_name(c),
            },
        )
    )

    relationships = [
        relationship(
            a,
            b,
            "1",
            "0..*",
        ),
        relationship(
            c,
            b,
            "0..1",
            "0..*",
        ),
    ]

    description = (
        "A mandatory one-to-many relationship "
        "combined with an optional secondary "
        "reference."
    )

    return (
        [parent, child, optional_parent],
        relationships,
        description,
    )


def pattern_one_to_many_optional(
    spec: dict[str, str],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    str,
]:
    a = spec["a"]
    b = spec["b"]
    c = spec["c"]

    parent = standard_entity(a)

    child = standard_child_with_fk(
        b,
        a,
        nullable=True,
    )

    second_parent = standard_entity(c)

    child["attributes"].append(
        attribute(
            id_name(c),
            "INTEGER",
            foreign_key=True,
            nullable=False,
            references={
                "entity": c,
                "attribute": id_name(c),
            },
        )
    )

    relationships = [
        relationship(
            a,
            b,
            "0..1",
            "0..*",
        ),
        relationship(
            c,
            b,
            "1",
            "0..*",
        ),
    ]

    description = (
        "An optional one-to-many relationship "
        "combined with a second mandatory parent."
    )

    return (
        [parent, child, second_parent],
        relationships,
        description,
    )


def pattern_one_to_one_optional(
    spec: dict[str, str],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    str,
]:
    a = spec["a"]
    b = spec["b"]

    parent = standard_entity(a)

    child = standard_child_with_fk(
        b,
        a,
        nullable=False,
        unique=True,
    )

    relationships = [
        relationship(
            a,
            b,
            "1",
            "0..1",
        )
    ]

    description = (
        "A one-to-one relationship where a parent "
        "may have zero or one child."
    )

    return (
        [parent, child],
        relationships,
        description,
    )


def pattern_one_to_one_mandatory(
    spec: dict[str, str],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    str,
]:
    a = spec["a"]
    b = spec["b"]

    parent = standard_entity(a)

    child = standard_child_with_fk(
        b,
        a,
        nullable=False,
        unique=True,
    )

    relationships = [
        relationship(
            a,
            b,
            "1",
            "1",
        )
    ]

    description = (
        "A mandatory one-to-one relationship "
        "represented by a unique foreign key."
    )

    return (
        [parent, child],
        relationships,
        description,
    )


def pattern_associative_identifying(
    spec: dict[str, str],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    str,
]:
    a = spec["a"]
    c = spec["c"]
    d = spec["d"]

    first_parent = standard_entity(a)
    second_parent = standard_entity(c)

    association = entity(
        d,
        [
            attribute(
                id_name(a),
                "INTEGER",
                primary_key=True,
                foreign_key=True,
                references={
                    "entity": a,
                    "attribute": id_name(a),
                },
            ),
            attribute(
                id_name(c),
                "INTEGER",
                primary_key=True,
                foreign_key=True,
                references={
                    "entity": c,
                    "attribute": id_name(c),
                },
            ),
            attribute(
                "quantity",
                "INTEGER",
            ),
            attribute(
                "status_code",
                "INTEGER",
            ),
        ],
    )

    relationships = [
        relationship(
            a,
            d,
            "1",
            "0..*",
            identifying=True,
        ),
        relationship(
            c,
            d,
            "1",
            "0..*",
            identifying=True,
        ),
    ]

    description = (
        "A many-to-many design resolved through "
        "an identifying associative entity."
    )

    return (
        [
            first_parent,
            second_parent,
            association,
        ],
        relationships,
        description,
    )


def pattern_weak_entity_identifying(
    spec: dict[str, str],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    str,
]:
    a = spec["a"]
    b = spec["b"]
    c = spec["c"]

    owner = standard_entity(a)
    lookup = standard_entity(c)

    weak_entity = entity(
        b,
        [
            attribute(
                id_name(a),
                "INTEGER",
                primary_key=True,
                foreign_key=True,
                references={
                    "entity": a,
                    "attribute": id_name(a),
                },
            ),
            attribute(
                "sequence_number",
                "INTEGER",
                primary_key=True,
            ),
            attribute(
                id_name(c),
                "INTEGER",
                foreign_key=True,
                nullable=True,
                references={
                    "entity": c,
                    "attribute": id_name(c),
                },
            ),
            attribute(
                "status_code",
                "INTEGER",
            ),
        ],
    )

    relationships = [
        relationship(
            a,
            b,
            "1",
            "1..*",
            identifying=True,
        ),
        relationship(
            c,
            b,
            "0..1",
            "0..*",
            identifying=False,
        ),
    ]

    description = (
        "A weak entity identified by its owner "
        "together with a local sequence number."
    )

    return (
        [
            owner,
            weak_entity,
            lookup,
        ],
        relationships,
        description,
    )


def composite_parent(
    name: str,
) -> dict[str, Any]:
    return entity(
        name,
        [
            attribute(
                f"{name.lower()}_code",
                "VARCHAR",
                primary_key=True,
            ),
            attribute(
                f"{name.lower()}_version",
                "INTEGER",
                primary_key=True,
            ),
            attribute(
                display_name(name),
                "VARCHAR",
            ),
            attribute(
                "status_code",
                "INTEGER",
            ),
        ],
    )


def add_composite_foreign_key(
    child: dict[str, Any],
    parent_name: str,
    *,
    part_of_primary_key: bool,
) -> None:
    child["attributes"].extend(
        [
            attribute(
                f"{parent_name.lower()}_code",
                "VARCHAR",
                primary_key=(
                    part_of_primary_key
                ),
                foreign_key=True,
                references={
                    "entity": parent_name,
                    "attribute": (
                        f"{parent_name.lower()}_code"
                    ),
                },
            ),
            attribute(
                f"{parent_name.lower()}_version",
                "INTEGER",
                primary_key=(
                    part_of_primary_key
                ),
                foreign_key=True,
                references={
                    "entity": parent_name,
                    "attribute": (
                        f"{parent_name.lower()}_version"
                    ),
                },
            ),
        ]
    )


def pattern_composite_nonidentifying(
    spec: dict[str, str],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    str,
]:
    a = spec["a"]
    b = spec["b"]
    c = spec["c"]

    parent = composite_parent(a)

    child = standard_entity(b)

    add_composite_foreign_key(
        child,
        a,
        part_of_primary_key=False,
    )

    alternate_parent = standard_entity(c)

    child["attributes"].append(
        attribute(
            id_name(c),
            "INTEGER",
            foreign_key=True,
            nullable=True,
            references={
                "entity": c,
                "attribute": id_name(c),
            },
        )
    )

    relationships = [
        relationship(
            a,
            b,
            "1",
            "0..*",
            identifying=False,
        ),
        relationship(
            c,
            b,
            "0..1",
            "0..*",
            identifying=False,
        ),
    ]

    description = (
        "A non-identifying relationship to a "
        "parent that has a composite primary key."
    )

    return (
        [
            parent,
            child,
            alternate_parent,
        ],
        relationships,
        description,
    )


def pattern_composite_identifying(
    spec: dict[str, str],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    str,
]:
    a = spec["a"]
    b = spec["b"]
    c = spec["c"]

    parent = composite_parent(a)

    child = entity(
        b,
        [
            attribute(
                "local_number",
                "INTEGER",
                primary_key=True,
            ),
            attribute(
                "status_code",
                "INTEGER",
            ),
        ],
    )

    add_composite_foreign_key(
        child,
        a,
        part_of_primary_key=True,
    )

    lookup = standard_entity(c)

    child["attributes"].append(
        attribute(
            id_name(c),
            "INTEGER",
            foreign_key=True,
            nullable=True,
            references={
                "entity": c,
                "attribute": id_name(c),
            },
        )
    )

    relationships = [
        relationship(
            a,
            b,
            "1",
            "1..*",
            identifying=True,
        ),
        relationship(
            c,
            b,
            "0..1",
            "0..*",
            identifying=False,
        ),
    ]

    description = (
        "An identifying relationship in which "
        "a composite parent key is propagated "
        "into the child primary key."
    )

    return (
        [
            parent,
            child,
            lookup,
        ],
        relationships,
        description,
    )


def pattern_dual_parent_transaction(
    spec: dict[str, str],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    str,
]:
    a = spec["a"]
    b = spec["b"]
    c = spec["c"]
    d = spec["d"]

    first_parent = standard_entity(a)
    second_parent = standard_entity(c)
    optional_lookup = standard_entity(d)

    child = standard_entity(b)

    child["attributes"].extend(
        [
            attribute(
                id_name(a),
                "INTEGER",
                foreign_key=True,
                references={
                    "entity": a,
                    "attribute": id_name(a),
                },
            ),
            attribute(
                id_name(c),
                "INTEGER",
                foreign_key=True,
                references={
                    "entity": c,
                    "attribute": id_name(c),
                },
            ),
            attribute(
                id_name(d),
                "INTEGER",
                foreign_key=True,
                nullable=True,
                references={
                    "entity": d,
                    "attribute": id_name(d),
                },
            ),
        ]
    )

    relationships = [
        relationship(
            a,
            b,
            "1",
            "0..*",
        ),
        relationship(
            c,
            b,
            "1",
            "0..*",
        ),
        relationship(
            d,
            b,
            "0..1",
            "0..*",
        ),
    ]

    description = (
        "A transactional entity with two mandatory "
        "parents and one optional lookup relationship."
    )

    return (
        [
            first_parent,
            child,
            second_parent,
            optional_lookup,
        ],
        relationships,
        description,
    )


def pattern_three_level_chain(
    spec: dict[str, str],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    str,
]:
    a = spec["a"]
    b = spec["b"]
    c = spec["c"]
    d = spec["d"]

    root = standard_entity(a)

    middle = standard_child_with_fk(
        b,
        a,
        nullable=False,
    )

    leaf = standard_child_with_fk(
        c,
        b,
        nullable=False,
    )

    optional_lookup = standard_entity(d)

    leaf["attributes"].append(
        attribute(
            id_name(d),
            "INTEGER",
            foreign_key=True,
            nullable=True,
            references={
                "entity": d,
                "attribute": id_name(d),
            },
        )
    )

    relationships = [
        relationship(
            a,
            b,
            "1",
            "0..*",
        ),
        relationship(
            b,
            c,
            "1",
            "0..*",
        ),
        relationship(
            d,
            c,
            "0..1",
            "0..*",
        ),
    ]

    description = (
        "A three-level relationship chain with "
        "an optional lookup attached to the leaf."
    )

    return (
        [
            root,
            middle,
            leaf,
            optional_lookup,
        ],
        relationships,
        description,
    )


PatternBuilder = Callable[
    [dict[str, str]],
    tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        str,
    ],
]


TOPOLOGY_FAMILIES: list[
    tuple[
        str,
        PatternBuilder,
        str,
    ]
] = [
    (
        "one_to_many_mandatory",
        pattern_one_to_many_mandatory,
        "easy",
    ),
    (
        "one_to_many_optional",
        pattern_one_to_many_optional,
        "medium",
    ),
    (
        "one_to_one_optional",
        pattern_one_to_one_optional,
        "medium",
    ),
    (
        "one_to_one_mandatory",
        pattern_one_to_one_mandatory,
        "medium",
    ),
    (
        "associative_identifying",
        pattern_associative_identifying,
        "hard",
    ),
    (
        "weak_entity_identifying",
        pattern_weak_entity_identifying,
        "hard",
    ),
    (
        "composite_nonidentifying",
        pattern_composite_nonidentifying,
        "hard",
    ),
    (
        "composite_identifying",
        pattern_composite_identifying,
        "hard",
    ),
    (
        "dual_parent_transaction",
        pattern_dual_parent_transaction,
        "medium",
    ),
    (
        "three_level_chain",
        pattern_three_level_chain,
        "hard",
    ),
]


def build_case(
    *,
    case_id: str,
    domain: str,
    topology_family: str,
    difficulty: str,
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    description: str,
    seed: int,
) -> dict[str, Any]:
    case = {
        "case_id": case_id,
        "domain": domain,
        "description": description,
        "entities": entities,
        "relationships": relationships,
        "requirements": (
            requirements_from_relationships(
                relationships
            )
        ),
        "metadata": {
            "source": "synthetic",
            "difficulty": difficulty,
            "version": 1,
            "generator_version": (
                GENERATOR_VERSION
            ),
            "topology_family": (
                topology_family
            ),
            "seed": seed,
            "error_count": 0,
        },
        "ground_truth": {
            "valid": True,
            "errors": [],
        },
    }

    validate_case_dict(case)

    return case


def generate_base_cases() -> list[dict[str, Any]]:
    """
    Generate the complete production collection
    of valid ER base schemas.

    14 domains x 10 topology families = 140 cases.
    """
    cases: list[dict[str, Any]] = []

    counter = 1

    for spec in DOMAIN_SPECS:

        for (
            topology_family,
            builder,
            difficulty,
        ) in TOPOLOGY_FAMILIES:

            (
                entities,
                relationships,
                description,
            ) = builder(spec)

            case = build_case(
                case_id=(
                    f"BASE_{counter:04d}"
                ),
                domain=spec["domain"],
                topology_family=(
                    topology_family
                ),
                difficulty=difficulty,
                entities=entities,
                relationships=relationships,
                description=description,
                seed=(
                    BASE_RANDOM_SEED
                    + counter
                ),
            )

            cases.append(case)

            counter += 1

    return cases


def save_base_cases(
    cases: list[dict[str, Any]],
) -> None:
    """
    Replace the base-case directory with the
    current production base collection.
    """
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for existing_file in (
        OUTPUT_DIR.glob("*.json")
    ):
        existing_file.unlink()

    for case in cases:

        validate_case_dict(case)

        topology_family = (
            case["metadata"][
                "topology_family"
            ]
        )

        filename = (
            f"{case['case_id'].lower()}_"
            f"{case['domain']}_"
            f"{topology_family}.json"
        )

        save_json(
            case,
            OUTPUT_DIR / filename,
        )


def main() -> None:
    cases = generate_base_cases()

    save_base_cases(cases)

    domains = {
        case["domain"]
        for case in cases
    }

    topologies = {
        case["metadata"][
            "topology_family"
        ]
        for case in cases
    }

    print(
        f"Generated {len(cases)} "
        "production valid base cases."
    )

    print(
        f"Domains: {len(domains)}"
    )

    print(
        f"Topology families: "
        f"{len(topologies)}"
    )


if __name__ == "__main__":
    main()