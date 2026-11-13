from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Reference:
    entity: str
    attribute: str


@dataclass
class Attribute:
    name: str
    type: str
    primary_key: bool
    nullable: bool

    foreign_key: bool = False
    unique: bool = False
    references: Reference | None = None


@dataclass
class Entity:
    name: str
    attributes: list[Attribute] = field(default_factory=list)

    def get_attribute(self, name: str) -> Attribute | None:
        """Return an attribute by name, if it exists."""
        for attribute in self.attributes:
            if attribute.name == name:
                return attribute
        return None

    def primary_key_attributes(self) -> list[Attribute]:
        """Return all attributes participating in the primary key."""
        return [
            attribute
            for attribute in self.attributes
            if attribute.primary_key
        ]

    def foreign_key_attributes(self) -> list[Attribute]:
        """Return all attributes marked as foreign keys."""
        return [
            attribute
            for attribute in self.attributes
            if attribute.foreign_key
        ]


@dataclass
class Relationship:
    name: str
    parent: str
    child: str
    parent_cardinality: str
    child_cardinality: str
    identifying: bool


@dataclass
class Requirement:
    requirement_id: str
    text: str

    type: str | None = None
    source: str | None = None
    target: str | None = None

    source_min: int | None = None
    source_max: int | str | None = None

    target_min: int | None = None
    target_max: int | str | None = None


@dataclass
class GroundTruthError:
    error_type: str

    entity: str | None = None
    attribute: str | None = None
    relationship: str | None = None

    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class GroundTruth:
    valid: bool
    errors: list[GroundTruthError] = field(default_factory=list)


@dataclass
class ERCase:
    case_id: str
    domain: str

    entities: list[Entity]
    relationships: list[Relationship]
    requirements: list[Requirement]

    metadata: dict[str, Any]
    ground_truth: GroundTruth

    description: str = ""

    def get_entity(self, name: str) -> Entity | None:
        """Return an entity by name, if it exists."""
        for entity in self.entities:
            if entity.name == name:
                return entity
        return None


@dataclass
class PredictionError:
    error_type: str
    message: str

    entity: str | None = None
    attribute: str | None = None
    relationship: str | None = None

    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Prediction:
    case_id: str
    method: str
    predicted_valid: bool

    errors: list[PredictionError]
    runtime_ms: float