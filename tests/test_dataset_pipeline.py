from __future__ import annotations

import copy
from collections import Counter

import pytest

from src.core.io import (
    load_json,
    load_jsonl,
    validate_case_dict,
)
from src.data.build_dataset import (
    DEV_PATH,
    MANIFEST_PATH,
    TEST_PATH,
    TRAIN_PATH,
    build_dataset,
)
from src.data.generate_base_cases import (
    DOMAIN_SPECS,
    TOPOLOGY_FAMILIES,
    generate_base_cases,
)
from src.data.inject_errors import (
    ERROR_ORDER,
    eligible_error_types,
    inject_error,
)


@pytest.fixture(scope="module")
def base_cases():
    return generate_base_cases()


@pytest.fixture(scope="module")
def final_splits():
    return build_dataset()


def test_production_base_case_count(
    base_cases,
):
    assert len(base_cases) == 140

    case_ids = [
        case["case_id"]
        for case in base_cases
    ]

    assert len(case_ids) == len(
        set(case_ids)
    )


def test_domain_and_topology_coverage(
    base_cases,
):
    domains = {
        case["domain"]
        for case in base_cases
    }

    topology_families = {
        case["metadata"][
            "topology_family"
        ]
        for case in base_cases
    }

    assert len(domains) == 14

    assert len(domains) == len(
        DOMAIN_SPECS
    )

    assert (
        len(topology_families)
        == 10
    )

    assert (
        len(topology_families)
        == len(TOPOLOGY_FAMILIES)
    )

    domain_counts = Counter(
        case["domain"]
        for case in base_cases
    )

    for count in (
        domain_counts.values()
    ):
        assert count == 10

    topology_counts = Counter(
        case["metadata"][
            "topology_family"
        ]
        for case in base_cases
    )

    for count in (
        topology_counts.values()
    ):
        assert count == 14


def test_all_base_cases_are_valid(
    base_cases,
):
    for case in base_cases:
        validate_case_dict(case)

        assert (
            case["ground_truth"][
                "valid"
            ]
            is True
        )

        assert (
            case["ground_truth"][
                "errors"
            ]
            == []
        )

        assert (
            case["metadata"][
                "error_count"
            ]
            == 0
        )


def test_every_error_type_has_eligible_cases(
    base_cases,
):
    eligibility_counts = Counter()

    for case in base_cases:

        for error_type in (
            eligible_error_types(
                case
            )
        ):
            eligibility_counts[
                error_type
            ] += 1

    for error_type in ERROR_ORDER:
        assert (
            eligibility_counts[
                error_type
            ]
            >= 20
        )


def test_generic_error_injection(
    base_cases,
):
    """
    Verify that every error type can be injected
    generically without modifying its source case.
    """
    for index, error_type in enumerate(
        ERROR_ORDER,
        start=1,
    ):
        eligible_case = next(
            case
            for case in base_cases
            if (
                error_type
                in eligible_error_types(
                    case
                )
            )
        )

        original = copy.deepcopy(
            eligible_case
        )

        invalid_case = inject_error(
            eligible_case,
            error_type,
            case_id=(
                f"TEST_INVALID_"
                f"{index:02d}"
            ),
            seed=(
                900000 + index
            ),
        )

        validate_case_dict(
            invalid_case
        )

        assert eligible_case == original

        assert (
            invalid_case[
                "ground_truth"
            ]["valid"]
            is False
        )

        assert (
            len(
                invalid_case[
                    "ground_truth"
                ]["errors"]
            )
            == 1
        )

        assert (
            invalid_case[
                "ground_truth"
            ]["errors"][0][
                "error_type"
            ]
            == error_type
        )

        assert (
            invalid_case[
                "metadata"
            ]["mutation"]
            == error_type
        )

        assert (
            invalid_case[
                "metadata"
            ]["parent_case_id"]
            == eligible_case[
                "case_id"
            ]
        )


def test_final_split_sizes_and_balance(
    final_splits,
):
    assert (
        len(final_splits["train"])
        == 198
    )

    assert (
        len(final_splits["dev"])
        == 41
    )

    assert (
        len(final_splits["test"])
        == 41
    )

    expected_counts = {
        "train": {
            "valid": 100,
            "invalid": 98,
        },
        "dev": {
            "valid": 20,
            "invalid": 21,
        },
        "test": {
            "valid": 20,
            "invalid": 21,
        },
    }

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

        assert (
            valid_count
            == expected_counts[
                split_name
            ]["valid"]
        )

        assert (
            invalid_count
            == expected_counts[
                split_name
            ]["invalid"]
        )


def test_error_distribution_is_balanced(
    final_splits,
):
    expected_per_split = {
        "train": 14,
        "dev": 3,
        "test": 3,
    }

    global_counts = Counter()

    for (
        split_name,
        cases,
    ) in final_splits.items():

        error_counts = Counter(
            case["ground_truth"][
                "errors"
            ][0]["error_type"]
            for case in cases
            if not case[
                "ground_truth"
            ]["valid"]
        )

        for error_type in ERROR_ORDER:

            assert (
                error_counts[
                    error_type
                ]
                == expected_per_split[
                    split_name
                ]
            )

        global_counts.update(
            error_counts
        )

    for error_type in ERROR_ORDER:

        assert (
            global_counts[
                error_type
            ]
            == 20
        )


def test_domains_do_not_cross_splits(
    final_splits,
):
    domains = {}

    for (
        split_name,
        cases,
    ) in final_splits.items():

        domains[split_name] = {
            case["domain"]
            for case in cases
        }

    assert not (
        domains["train"]
        & domains["dev"]
    )

    assert not (
        domains["train"]
        & domains["test"]
    )

    assert not (
        domains["dev"]
        & domains["test"]
    )

    assert (
        len(domains["train"])
        == 10
    )

    assert (
        len(domains["dev"])
        == 2
    )

    assert (
        len(domains["test"])
        == 2
    )


def test_parent_schemas_do_not_cross_splits(
    final_splits,
):
    parent_ids = {}

    for (
        split_name,
        cases,
    ) in final_splits.items():

        parent_ids[
            split_name
        ] = {
            case["metadata"][
                "parent_case_id"
            ]
            for case in cases
        }

    assert not (
        parent_ids["train"]
        & parent_ids["dev"]
    )

    assert not (
        parent_ids["train"]
        & parent_ids["test"]
    )

    assert not (
        parent_ids["dev"]
        & parent_ids["test"]
    )


def test_all_final_case_ids_are_unique(
    final_splits,
):
    case_ids = []

    for cases in (
        final_splits.values()
    ):

        for case in cases:

            validate_case_dict(
                case
            )

            case_ids.append(
                case["case_id"]
            )

    assert len(case_ids) == 280

    assert len(case_ids) == len(
        set(case_ids)
    )


def test_every_split_has_all_topologies(
    final_splits,
):
    for cases in (
        final_splits.values()
    ):

        topology_families = {
            case["metadata"][
                "topology_family"
            ]
            for case in cases
            if case[
                "ground_truth"
            ]["valid"]
        }

        assert (
            len(topology_families)
            == 10
        )


def test_saved_jsonl_files_match_dataset(
    final_splits,
):
    saved_train = load_jsonl(
        TRAIN_PATH
    )

    saved_dev = load_jsonl(
        DEV_PATH
    )

    saved_test = load_jsonl(
        TEST_PATH
    )

    assert (
        len(saved_train)
        == len(
            final_splits[
                "train"
            ]
        )
        == 198
    )

    assert (
        len(saved_dev)
        == len(
            final_splits[
                "dev"
            ]
        )
        == 41
    )

    assert (
        len(saved_test)
        == len(
            final_splits[
                "test"
            ]
        )
        == 41
    )

    assert {
        case["case_id"]
        for case in saved_train
    } == {
        case["case_id"]
        for case in final_splits[
            "train"
        ]
    }

    assert {
        case["case_id"]
        for case in saved_dev
    } == {
        case["case_id"]
        for case in final_splits[
            "dev"
        ]
    }

    assert {
        case["case_id"]
        for case in saved_test
    } == {
        case["case_id"]
        for case in final_splits[
            "test"
        ]
    }


def test_dataset_manifest(
    final_splits,
):
    manifest = load_json(
        MANIFEST_PATH
    )

    assert (
        manifest[
            "total_cases"
        ]
        == 280
    )

    assert (
        manifest[
            "valid_cases"
        ]
        == 140
    )

    assert (
        manifest[
            "invalid_cases"
        ]
        == 140
    )

    assert (
        manifest[
            "domains"
        ]
        == 14
    )

    assert (
        manifest[
            "topology_families"
        ]
        == 10
    )

    assert (
        manifest[
            "error_types"
        ]
        == 7
    )

    assert (
        manifest[
            "cases_per_error_type"
        ]
        == 20
    )

    assert (
        manifest[
            "splits"
        ]["train"]["total"]
        == 198
    )

    assert (
        manifest[
            "splits"
        ]["dev"]["total"]
        == 41
    )

    assert (
        manifest[
            "splits"
        ]["test"]["total"]
        == 41
    )