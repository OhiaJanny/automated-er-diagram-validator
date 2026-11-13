from __future__ import annotations

import copy
import random
from collections import Counter
from pathlib import Path
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
    save_json,
    save_jsonl,
    validate_case_dict,
)
from src.data.generate_base_cases import (
    generate_base_cases,
    save_base_cases,
)
from src.data.inject_errors import (
    eligible_error_types,
    inject_error,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = (
    PROJECT_ROOT
    / "data"
)

GENERATED_VALID_DIR = (
    DATA_DIR
    / "generated"
    / "valid"
)

GENERATED_INVALID_DIR = (
    DATA_DIR
    / "generated"
    / "invalid"
)

TRAIN_PATH = (
    DATA_DIR
    / "train.jsonl"
)

DEV_PATH = (
    DATA_DIR
    / "dev.jsonl"
)

TEST_PATH = (
    DATA_DIR
    / "test.jsonl"
)

MANIFEST_PATH = (
    DATA_DIR
    / "dataset_manifest.json"
)


BENCHMARK_VERSION = "1.0"
RANDOM_SEED = 811


ERROR_TYPES = (
    ERROR_FK_TARGET_NOT_KEY,
    ERROR_FK_WRONG_ENTITY,
    ERROR_COMPOSITE_FK_INCOMPLETE,
    ERROR_CARDINALITY_UNIQUENESS_CONFLICT,
    ERROR_PARTICIPATION_OPTIONALITY_CONFLICT,
    ERROR_IDENTIFYING_RELATIONSHIP_KEY_ERROR,
    ERROR_MISSING_REQUIRED_RELATIONSHIP,
)


ERROR_CODES = {
    ERROR_FK_TARGET_NOT_KEY: "E01",
    ERROR_FK_WRONG_ENTITY: "E02",
    ERROR_COMPOSITE_FK_INCOMPLETE: "E03",
    ERROR_CARDINALITY_UNIQUENESS_CONFLICT: "E04",
    ERROR_PARTICIPATION_OPTIONALITY_CONFLICT: "E05",
    ERROR_IDENTIFYING_RELATIONSHIP_KEY_ERROR: "E06",
    ERROR_MISSING_REQUIRED_RELATIONSHIP: "E07",
}


INVALID_QUOTAS = {
    "train": 14,
    "dev": 3,
    "test": 3,
}


def clear_generated_json() -> None:
    """
    Remove stale generated benchmark JSON files
    before rebuilding the production dataset.
    """
    GENERATED_VALID_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    GENERATED_INVALID_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for path in (
        GENERATED_VALID_DIR.glob(
            "*.json"
        )
    ):
        path.unlink()

    for path in (
        GENERATED_INVALID_DIR.glob(
            "*.json"
        )
    ):
        path.unlink()


def split_domains(
    base_cases: list[dict[str, Any]],
) -> dict[str, set[str]]:
    """
    Split by complete domain rather than by case.

    No domain appears in more than one split.

    14 domains:
    10 train
    2 dev
    2 test
    """
    domains = sorted(
        {
            case["domain"]
            for case in base_cases
        }
    )

    if len(domains) != 14:
        raise ValueError(
            "Production benchmark expects "
            "exactly 14 domains."
        )

    rng = random.Random(
        RANDOM_SEED
    )

    rng.shuffle(domains)

    return {
        "train": set(
            domains[:10]
        ),
        "dev": set(
            domains[10:12]
        ),
        "test": set(
            domains[12:14]
        ),
    }


def assign_base_cases_to_splits(
    base_cases: list[dict[str, Any]],
    domain_splits: dict[str, set[str]],
) -> dict[
    str,
    list[dict[str, Any]],
]:
    split_cases = {
        "train": [],
        "dev": [],
        "test": [],
    }

    for case in base_cases:

        matched_split = None

        for (
            split_name,
            domains,
        ) in domain_splits.items():

            if case["domain"] in domains:
                matched_split = (
                    split_name
                )
                break

        if matched_split is None:
            raise ValueError(
                f"No split assigned to "
                f"{case['domain']}."
            )

        split_cases[
            matched_split
        ].append(case)

    expected_sizes = {
        "train": 100,
        "dev": 20,
        "test": 20,
    }

    for (
        split_name,
        expected_size,
    ) in expected_sizes.items():

        actual_size = len(
            split_cases[
                split_name
            ]
        )

        if (
            actual_size
            != expected_size
        ):
            raise ValueError(
                f"{split_name} expected "
                f"{expected_size} base cases "
                f"but found {actual_size}."
            )

    return split_cases


def create_valid_record(
    base_case: dict[str, Any],
    *,
    split_name: str,
) -> dict[str, Any]:
    """
    Convert a generated base design into a final
    valid benchmark record.
    """
    case = copy.deepcopy(
        base_case
    )

    base_case_id = (
        base_case["case_id"]
    )

    numeric_id = (
        base_case_id.split(
            "_"
        )[-1]
    )

    case["case_id"] = (
        f"VALID_{numeric_id}"
    )

    case["metadata"] = copy.deepcopy(
        case["metadata"]
    )

    case["metadata"][
        "parent_case_id"
    ] = base_case_id

    case["metadata"][
        "benchmark_version"
    ] = BENCHMARK_VERSION

    case["metadata"][
        "split"
    ] = split_name

    case["metadata"][
        "error_count"
    ] = 0

    case["ground_truth"] = {
        "valid": True,
        "errors": [],
    }

    validate_case_dict(case)

    return case


def create_valid_records(
    split_base_cases: dict[
        str,
        list[dict[str, Any]],
    ],
) -> dict[
    str,
    list[dict[str, Any]],
]:
    result = {
        "train": [],
        "dev": [],
        "test": [],
    }

    for (
        split_name,
        base_cases,
    ) in split_base_cases.items():

        for base_case in base_cases:

            result[
                split_name
            ].append(
                create_valid_record(
                    base_case,
                    split_name=(
                        split_name
                    ),
                )
            )

    return result


def eligible_cases_for_error(
    base_cases: list[dict[str, Any]],
    error_type: str,
) -> list[dict[str, Any]]:
    return [
        case
        for case in base_cases
        if (
            error_type
            in eligible_error_types(
                case
            )
        )
    ]


def select_invalid_base_cases(
    base_cases: list[dict[str, Any]],
    *,
    error_type: str,
    quota: int,
    seed: int,
) -> list[dict[str, Any]]:
    """
    Select distinct eligible base schemas for one
    error type within one split.
    """
    eligible = (
        eligible_cases_for_error(
            base_cases,
            error_type,
        )
    )

    if len(eligible) < quota:
        raise ValueError(
            f"Insufficient eligible cases for "
            f"{error_type}. "
            f"Required {quota}, found "
            f"{len(eligible)}."
        )

    eligible = sorted(
        eligible,
        key=lambda case: (
            case["case_id"]
        ),
    )

    rng = random.Random(seed)

    rng.shuffle(eligible)

    return eligible[:quota]


def create_invalid_records(
    split_base_cases: dict[
        str,
        list[dict[str, Any]],
    ],
) -> dict[
    str,
    list[dict[str, Any]],
]:
    result = {
        "train": [],
        "dev": [],
        "test": [],
    }

    split_seed_offsets = {
        "train": 100000,
        "dev": 200000,
        "test": 300000,
    }

    for (
        split_name,
        base_cases,
    ) in split_base_cases.items():

        quota = INVALID_QUOTAS[
            split_name
        ]

        for error_index, error_type in enumerate(
            ERROR_TYPES,
            start=1,
        ):

            selection_seed = (
                RANDOM_SEED
                + split_seed_offsets[
                    split_name
                ]
                + error_index
            )

            selected_bases = (
                select_invalid_base_cases(
                    base_cases,
                    error_type=(
                        error_type
                    ),
                    quota=quota,
                    seed=(
                        selection_seed
                    ),
                )
            )

            error_code = (
                ERROR_CODES[
                    error_type
                ]
            )

            for (
                item_index,
                base_case,
            ) in enumerate(
                selected_bases,
                start=1,
            ):

                mutation_seed = (
                    selection_seed
                    + item_index
                    * 100
                )

                case_id = (
                    f"INVALID_"
                    f"{error_code}_"
                    f"{split_name.upper()}_"
                    f"{item_index:03d}"
                )

                invalid_case = (
                    inject_error(
                        base_case,
                        error_type,
                        case_id=(
                            case_id
                        ),
                        seed=(
                            mutation_seed
                        ),
                    )
                )

                invalid_case[
                    "metadata"
                ][
                    "benchmark_version"
                ] = (
                    BENCHMARK_VERSION
                )

                invalid_case[
                    "metadata"
                ][
                    "split"
                ] = split_name

                validate_case_dict(
                    invalid_case
                )

                result[
                    split_name
                ].append(
                    invalid_case
                )

    return result


def verify_error_distribution(
    invalid_records: dict[
        str,
        list[dict[str, Any]],
    ],
) -> None:
    expected_per_split = {
        "train": 14,
        "dev": 3,
        "test": 3,
    }

    global_counts = Counter()

    for (
        split_name,
        cases,
    ) in invalid_records.items():

        split_counts = Counter(
            case["ground_truth"][
                "errors"
            ][0]["error_type"]
            for case in cases
        )

        expected = (
            expected_per_split[
                split_name
            ]
        )

        for error_type in ERROR_TYPES:

            actual = split_counts[
                error_type
            ]

            if actual != expected:
                raise ValueError(
                    f"{split_name}: "
                    f"{error_type} expected "
                    f"{expected}, found "
                    f"{actual}."
                )

        global_counts.update(
            split_counts
        )

    for error_type in ERROR_TYPES:

        if (
            global_counts[
                error_type
            ]
            != 20
        ):
            raise ValueError(
                f"{error_type} expected "
                "20 cases globally, found "
                f"{global_counts[error_type]}."
            )


def verify_domain_isolation(
    domain_splits: dict[
        str,
        set[str],
    ],
) -> None:
    train = domain_splits[
        "train"
    ]

    dev = domain_splits[
        "dev"
    ]

    test = domain_splits[
        "test"
    ]

    if train & dev:
        raise ValueError(
            "Domain leakage between "
            "train and dev."
        )

    if train & test:
        raise ValueError(
            "Domain leakage between "
            "train and test."
        )

    if dev & test:
        raise ValueError(
            "Domain leakage between "
            "dev and test."
        )


def verify_parent_isolation(
    final_splits: dict[
        str,
        list[dict[str, Any]],
    ],
) -> None:
    """
    Ensure no base schema contributes any valid or
    invalid descendant to more than one split.
    """
    parent_sets = {}

    for (
        split_name,
        cases,
    ) in final_splits.items():

        parent_sets[
            split_name
        ] = {
            case["metadata"][
                "parent_case_id"
            ]
            for case in cases
        }

    if (
        parent_sets["train"]
        & parent_sets["dev"]
    ):
        raise ValueError(
            "Base-schema leakage between "
            "train and dev."
        )

    if (
        parent_sets["train"]
        & parent_sets["test"]
    ):
        raise ValueError(
            "Base-schema leakage between "
            "train and test."
        )

    if (
        parent_sets["dev"]
        & parent_sets["test"]
    ):
        raise ValueError(
            "Base-schema leakage between "
            "dev and test."
        )


def verify_unique_case_ids(
    final_splits: dict[
        str,
        list[dict[str, Any]],
    ],
) -> None:
    case_ids = []

    for cases in (
        final_splits.values()
    ):
        case_ids.extend(
            case["case_id"]
            for case in cases
        )

    if len(case_ids) != len(
        set(case_ids)
    ):
        raise ValueError(
            "Duplicate final benchmark "
            "case IDs detected."
        )


def verify_topology_coverage(
    final_splits: dict[
        str,
        list[dict[str, Any]],
    ],
) -> None:
    """
    Every split must contain all ten topology
    families through its valid cases.
    """
    for (
        split_name,
        cases,
    ) in final_splits.items():

        topologies = {
            case["metadata"][
                "topology_family"
            ]
            for case in cases
            if case[
                "ground_truth"
            ]["valid"]
        }

        if len(topologies) != 10:
            raise ValueError(
                f"{split_name} contains "
                f"{len(topologies)} "
                "topology families; "
                "expected 10."
            )


def validate_all_cases(
    final_splits: dict[
        str,
        list[dict[str, Any]],
    ],
) -> None:
    for cases in (
        final_splits.values()
    ):

        for case in cases:
            validate_case_dict(case)


def shuffle_split(
    cases: list[dict[str, Any]],
    *,
    seed: int,
) -> list[dict[str, Any]]:
    shuffled = copy.deepcopy(
        cases
    )

    rng = random.Random(seed)

    rng.shuffle(shuffled)

    return shuffled


def save_individual_cases(
    valid_records: dict[
        str,
        list[dict[str, Any]],
    ],
    invalid_records: dict[
        str,
        list[dict[str, Any]],
    ],
) -> None:
    clear_generated_json()

    for (
        split_name,
        cases,
    ) in valid_records.items():

        for case in cases:

            filename = (
                f"{case['case_id'].lower()}_"
                f"{split_name}.json"
            )

            save_json(
                case,
                GENERATED_VALID_DIR
                / filename,
            )

    for (
        split_name,
        cases,
    ) in invalid_records.items():

        for case in cases:

            filename = (
                f"{case['case_id'].lower()}"
                ".json"
            )

            save_json(
                case,
                GENERATED_INVALID_DIR
                / filename,
            )


def build_manifest(
    *,
    domain_splits: dict[
        str,
        set[str],
    ],
    final_splits: dict[
        str,
        list[dict[str, Any]],
    ],
) -> dict[str, Any]:

    error_distribution = Counter()

    for cases in (
        final_splits.values()
    ):

        for case in cases:

            if not case[
                "ground_truth"
            ]["valid"]:

                error_distribution.update(
                    [
                        case[
                            "ground_truth"
                        ][
                            "errors"
                        ][0][
                            "error_type"
                        ]
                    ]
                )

    split_summary = {}

    for (
        split_name,
        cases,
    ) in final_splits.items():

        valid_count = sum(
            1
            for case in cases
            if case[
                "ground_truth"
            ]["valid"]
        )

        invalid_count = (
            len(cases)
            - valid_count
        )

        split_summary[
            split_name
        ] = {
            "total": len(cases),
            "valid": valid_count,
            "invalid": invalid_count,
            "domains": sorted(
                domain_splits[
                    split_name
                ]
            ),
        }

    return {
        "benchmark_version": (
            BENCHMARK_VERSION
        ),
        "random_seed": (
            RANDOM_SEED
        ),
        "diagram_type": (
            "Information Engineering "
            "Crow's-Foot ER"
        ),
        "total_cases": sum(
            len(cases)
            for cases in (
                final_splits.values()
            )
        ),
        "valid_cases": 140,
        "invalid_cases": 140,
        "domains": 14,
        "topology_families": 10,
        "error_types": 7,
        "cases_per_error_type": 20,
        "split_strategy": (
            "Domain-grouped split. "
            "A domain and all schemas derived "
            "from it occur in exactly one split."
        ),
        "splits": split_summary,
        "error_distribution": dict(
            sorted(
                error_distribution.items()
            )
        ),
    }


def print_split_summary(
    split_name: str,
    cases: list[dict[str, Any]],
) -> None:
    valid_count = sum(
        1
        for case in cases
        if case[
            "ground_truth"
        ]["valid"]
    )

    invalid_count = (
        len(cases)
        - valid_count
    )

    print(
        f"{split_name.capitalize()}: "
        f"{len(cases)} cases "
        f"({valid_count} valid, "
        f"{invalid_count} invalid)"
    )


def build_dataset() -> dict[
    str,
    list[dict[str, Any]],
]:
    """
    Build the complete production benchmark.

    Final size:
    140 valid cases
    140 invalid cases
    280 total cases

    Each of seven error categories has
    exactly 20 invalid cases.
    """
    base_cases = (
        generate_base_cases()
    )

    if len(base_cases) != 140:
        raise ValueError(
            "Expected exactly 140 "
            "production base cases."
        )

    save_base_cases(
        base_cases
    )

    domain_splits = (
        split_domains(
            base_cases
        )
    )

    verify_domain_isolation(
        domain_splits
    )

    split_base_cases = (
        assign_base_cases_to_splits(
            base_cases,
            domain_splits,
        )
    )

    valid_records = (
        create_valid_records(
            split_base_cases
        )
    )

    invalid_records = (
        create_invalid_records(
            split_base_cases
        )
    )

    verify_error_distribution(
        invalid_records
    )

    final_splits = {}

    split_shuffle_seeds = {
        "train": RANDOM_SEED + 1,
        "dev": RANDOM_SEED + 2,
        "test": RANDOM_SEED + 3,
    }

    for split_name in (
        "train",
        "dev",
        "test",
    ):

        combined = (
            valid_records[
                split_name
            ]
            + invalid_records[
                split_name
            ]
        )

        final_splits[
            split_name
        ] = shuffle_split(
            combined,
            seed=(
                split_shuffle_seeds[
                    split_name
                ]
            ),
        )

    validate_all_cases(
        final_splits
    )

    verify_unique_case_ids(
        final_splits
    )

    verify_parent_isolation(
        final_splits
    )

    verify_topology_coverage(
        final_splits
    )

    total_cases = sum(
        len(cases)
        for cases in (
            final_splits.values()
        )
    )

    if total_cases != 280:
        raise ValueError(
            f"Expected 280 final cases, "
            f"found {total_cases}."
        )

    save_individual_cases(
        valid_records,
        invalid_records,
    )

    save_jsonl(
        final_splits["train"],
        TRAIN_PATH,
    )

    save_jsonl(
        final_splits["dev"],
        DEV_PATH,
    )

    save_jsonl(
        final_splits["test"],
        TEST_PATH,
    )

    manifest = build_manifest(
        domain_splits=domain_splits,
        final_splits=final_splits,
    )

    save_json(
        manifest,
        MANIFEST_PATH,
    )

    print()
    print(
        "Production benchmark "
        "build complete."
    )
    print()

    print_split_summary(
        "train",
        final_splits["train"],
    )

    print_split_summary(
        "dev",
        final_splits["dev"],
    )

    print_split_summary(
        "test",
        final_splits["test"],
    )

    print()

    print(
        "Total cases: 280"
    )

    print(
        "Valid cases: 140"
    )

    print(
        "Invalid cases: 140"
    )

    print(
        "Cases per error type: 20"
    )

    print()

    print(
        "Dataset manifest:"
    )

    print(
        MANIFEST_PATH
    )

    return final_splits


def main() -> None:
    build_dataset()


if __name__ == "__main__":
    main()