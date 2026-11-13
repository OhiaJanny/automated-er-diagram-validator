

# ER Case Data Format

## 1. Purpose

This document defines the common data representation used by every validation method.

All three methods must operate on equivalent information.

The canonical dataset format is **JSON Lines (`.jsonl`)**, where each line contains one ER validation case.

## 2. Dataset Files

The project may contain:

```text
data/
├── train.jsonl
├── dev.jsonl
├── test.jsonl
└── toy/
    ├── valid_example.json
    └── invalid_example.json
```

`train.jsonl` and `dev.jsonl` may contain labeled examples for development.

The final test cases must be evaluated through the shared evaluation pipeline.

## 3. Case Structure

Each case contains the following major sections:

```text
case_id
domain
description
entities
relationships
requirements
metadata
ground_truth
```

`ground_truth` is used only for dataset construction and evaluation. Validation methods must not use it when generating predictions.

## 4. Example Valid Case

```json
{
  "case_id": "ER_0001",
  "domain": "university",
  "description": "Students enroll in courses through enrollment records.",
  "entities": [
    {
      "name": "STUDENT",
      "attributes": [
        {
          "name": "student_id",
          "type": "INTEGER",
          "primary_key": true,
          "nullable": false
        },
        {
          "name": "student_name",
          "type": "VARCHAR",
          "primary_key": false,
          "nullable": false
        }
      ]
    },
    {
      "name": "COURSE",
      "attributes": [
        {
          "name": "course_id",
          "type": "INTEGER",
          "primary_key": true,
          "nullable": false
        }
      ]
    },
    {
      "name": "ENROLLMENT",
      "attributes": [
        {
          "name": "student_id",
          "type": "INTEGER",
          "primary_key": true,
          "foreign_key": true,
          "references": {
            "entity": "STUDENT",
            "attribute": "student_id"
          },
          "nullable": false
        },
        {
          "name": "course_id",
          "type": "INTEGER",
          "primary_key": true,
          "foreign_key": true,
          "references": {
            "entity": "COURSE",
            "attribute": "course_id"
          },
          "nullable": false
        }
      ]
    }
  ],
  "relationships": [
    {
      "name": "student_enrollment",
      "parent": "STUDENT",
      "child": "ENROLLMENT",
      "parent_cardinality": "1",
      "child_cardinality": "0..*",
      "identifying": true
    },
    {
      "name": "course_enrollment",
      "parent": "COURSE",
      "child": "ENROLLMENT",
      "parent_cardinality": "1",
      "child_cardinality": "0..*",
      "identifying": true
    }
  ],
  "requirements": [
    {
      "requirement_id": "R1",
      "text": "Each enrollment belongs to exactly one student."
    },
    {
      "requirement_id": "R2",
      "text": "Each enrollment belongs to exactly one course."
    }
  ],
  "metadata": {
    "source": "synthetic",
    "difficulty": "medium",
    "version": 1
  },
  "ground_truth": {
    "valid": true,
    "errors": []
  }
}
```

## 5. Invalid Cases

Invalid cases use the same ER structure.

Only the relevant design component is mutated.

Example:

```json
{
  "ground_truth": {
    "valid": false,
    "errors": [
      {
        "error_type": "FK_TARGET_NOT_KEY",
        "entity": "ENROLLMENT",
        "attribute": "student_id",
        "relationship": "student_enrollment"
      }
    ]
  }
}
```

## 6. Entity Representation

Each entity must include:

- `name`;
- `attributes`.

Each attribute may include:

- `name`;
- `type`;
- `primary_key`;
- `foreign_key`;
- `nullable`;
- `unique`;
- `references`.

Composite keys are represented by marking each participating attribute with:

```json
"primary_key": true
```

## 7. Foreign-Key Representation

Foreign keys must identify their target explicitly:

```json
"references": {
  "entity": "PARENT_ENTITY",
  "attribute": "parent_key"
}
```

For composite foreign keys, each component must specify the corresponding referenced attribute.

## 8. Relationship Representation

Each relationship contains:

```json
{
  "name": "relationship_name",
  "parent": "PARENT_ENTITY",
  "child": "CHILD_ENTITY",
  "parent_cardinality": "1",
  "child_cardinality": "0..*",
  "identifying": false
}
```

Allowed cardinality strings initially include:

```text
0..1
1
0..*
1..*
```

Additional forms may be added only through the shared schema.

## 9. Requirements

Requirements provide the semantic rules against which the candidate ER design is evaluated.

Example:

```json
{
  "requirement_id": "R3",
  "text": "Each order must belong to exactly one customer."
}
```

If a requirement has a machine-readable form, it may additionally contain:

```json
{
  "type": "relationship_cardinality",
  "source": "ORDER",
  "target": "CUSTOMER",
  "source_min": 1,
  "source_max": 1
}
```

Natural-language text should still be retained for the LLM method and for human interpretation.

## 10. Ground Truth

Ground truth contains:

```json
{
  "valid": false,
  "errors": []
}
```

Each error must use a label defined in `docs/error_taxonomy.md`.

Ground-truth labels must not be passed to a validator during prediction.

## 11. Metadata

Recommended metadata:

```json
{
  "source": "synthetic",
  "domain": "ecommerce",
  "difficulty": "hard",
  "error_count": 2,
  "generator_version": "1.0",
  "seed": 42
}
```

Metadata must not encode the correct answer in a way that can leak ground truth to a method.

## 12. PlantUML and PNG Files

PlantUML and PNG versions may be generated for:

- visual inspection;
- poster figures;
- human validation;
- case demonstrations.

They are not the authoritative ground-truth representation.

The canonical representation used for evaluation is the structured JSON case.