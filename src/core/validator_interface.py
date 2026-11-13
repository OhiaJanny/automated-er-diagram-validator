from __future__ import annotations

from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any

from src.core.constants import VALID_METHODS
from src.core.models import Prediction


class BaseValidator(ABC):
    """
    Common interface for all ER validation methods.

    Every validation method must inherit from this class
    and implement the _validate_case() method.
    """

    method_name: str

    def __init__(self) -> None:
        if not hasattr(self, "method_name"):
            raise ValueError(
                "Validator subclasses must define method_name."
            )

        if self.method_name not in VALID_METHODS:
            raise ValueError(
                f"Invalid method_name: {self.method_name}"
            )

    def validate(
        self,
        case: dict[str, Any],
    ) -> Prediction:
        """
        Validate one prediction-safe ER case.

        Runtime is measured automatically so all methods
        use the same timing procedure.
        """
        self._validate_input(case)

        start_time = perf_counter()

        prediction = self._validate_case(case)

        runtime_ms = (
            perf_counter() - start_time
        ) * 1000.0

        if not isinstance(
            prediction,
            Prediction,
        ):
            raise TypeError(
                "_validate_case() must return a Prediction object."
            )

        prediction.case_id = case["case_id"]
        prediction.method = self.method_name
        prediction.runtime_ms = runtime_ms

        self._validate_output(prediction)

        return prediction

    @abstractmethod
    def _validate_case(
        self,
        case: dict[str, Any],
    ) -> Prediction:
        """
        Implement method-specific validation logic.

        Each method owner must implement this function.
        """
        raise NotImplementedError

    def _validate_input(
        self,
        case: dict[str, Any],
    ) -> None:
        """
        Perform basic checks on method input.

        Method inputs must not contain ground-truth labels.
        """
        if not isinstance(case, dict):
            raise TypeError(
                "Validator input must be a dictionary."
            )

        if "case_id" not in case:
            raise ValueError(
                "Validator input is missing case_id."
            )

        if "ground_truth" in case:
            raise ValueError(
                "Ground truth must not be provided to validators."
            )

        required_fields = {
            "domain",
            "entities",
            "relationships",
            "requirements",
            "metadata",
        }

        missing_fields = (
            required_fields - case.keys()
        )

        if missing_fields:
            raise ValueError(
                "Validator input is missing required fields: "
                + ", ".join(
                    sorted(missing_fields)
                )
            )

    def _validate_output(
        self,
        prediction: Prediction,
    ) -> None:
        """
        Perform consistency checks on a prediction.
        """
        if (
            prediction.predicted_valid
            and prediction.errors
        ):
            raise ValueError(
                "A prediction marked valid cannot contain errors."
            )

        if (
            not prediction.predicted_valid
            and not prediction.errors
        ):
            raise ValueError(
                "A prediction marked invalid must contain "
                "at least one error."
            )

    def validate_batch(
        self,
        cases: list[dict[str, Any]],
    ) -> list[Prediction]:
        """
        Validate multiple cases using the same method.
        """
        predictions = []

        for case in cases:
            prediction = self.validate(case)
            predictions.append(prediction)

        return predictions