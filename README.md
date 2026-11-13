# ER Defense Validator

## Project Overview

This repository contains the CSCE 811 Data Modeling final project:

**Automated Detection of Non-Trivial Integrity and Relationship Errors in ER Diagrams: A Comparison of Rule-Based, Constraint-Solver, and LLM-Based Validation**

The project focuses on automated validation of Information Engineering / Crow's-Foot ER designs.

The goal is to determine whether an ER design satisfies predefined integrity and relationship constraints and, when invalid, identify the corresponding logical design error.

Three methods are compared on the same benchmark:

1. Deterministic Rule-Based Validator
2. Constraint-Solver Validator using Z3
3. LLM-Based Validator

All three methods use the same input format, the same seven-error taxonomy, and the same prediction-output format so their results can be compared directly.

---

## Error Categories

The project evaluates the following seven logical ER-design errors:

- `FK_TARGET_NOT_KEY`
- `FK_WRONG_ENTITY`
- `COMPOSITE_FK_INCOMPLETE`
- `CARDINALITY_UNIQUENESS_CONFLICT`
- `PARTICIPATION_OPTIONALITY_CONFLICT`
- `IDENTIFYING_RELATIONSHIP_KEY_ERROR`
- `MISSING_REQUIRED_RELATIONSHIP`

Full definitions are available in:

```text
docs/error_taxonomy.md
```

---

## Benchmark Dataset

The production benchmark contains:

- 280 total ER cases
- 140 valid cases
- 140 invalid cases
- 14 application domains
- 10 ER topology families
- 7 error categories
- 20 invalid cases per error category

Dataset split:

```text
Train: 198 cases
Dev:    41 cases
Test:   41 cases
```

The dataset uses a domain-grouped split so the same application domain does not appear across multiple splits.

The primary benchmark files are:

```text
data/train.jsonl
data/dev.jsonl
data/test.jsonl
data/dataset_manifest.json
```

The benchmark can be regenerated using:

```powershell
python -m src.data.generate_base_cases
python -m src.data.build_dataset
```

---

## Repository Structure

```text
er-defense-validator/
│
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── config.yaml
├── pytest.ini
│
├── docs/
│   ├── project_scope.md
│   ├── data_format.md
│   ├── error_taxonomy.md
│   └── method_interface.md
│
├── schemas/
│   ├── er_case.schema.json
│   └── prediction.schema.json
│
├── data/
│   ├── base/
│   │   └── valid_cases/
│   ├── generated/
│   │   ├── valid/
│   │   └── invalid/
│   ├── train.jsonl
│   ├── dev.jsonl
│   ├── test.jsonl
│   ├── dataset_manifest.json
│   └── toy/
│       ├── valid_example.json
│       └── invalid_example.json
│
├── diagrams/
│   ├── plantuml/
│   └── png/
│
├── src/
│   ├── core/
│   │   ├── models.py
│   │   ├── io.py
│   │   ├── validator_interface.py
│   │   └── constants.py
│   │
│   ├── data/
│   │   ├── generate_base_cases.py
│   │   ├── inject_errors.py
│   │   ├── build_dataset.py
│   │   └── render_plantuml.py
│   │
│   ├── methods/
│   │   ├── rule_based/
│   │   │   └── validator.py
│   │   ├── constraint_solver/
│   │   │   └── validator.py
│   │   └── llm_based/
│   │       ├── validator.py
│   │       └── prompt.txt
│   │
│   └── evaluation/
│       ├── metrics.py
│       ├── evaluate.py
│       └── compare_methods.py
│
├── tests/
│
├── outputs/
│   ├── rule_based/
│   ├── constraint_solver/
│   └── llm_based/
│
├── results/
│   └── figures/
│
└── report/
    └── notes/
```

---

## Installation

Clone the repository and move into the project directory.

Install all required Python packages with:

```powershell
python -m pip install -r requirements.txt
```

The main dependencies include:

- `jsonschema`
- `pytest`
- `networkx`
- `z3-solver`
- `openai`
- `numpy`
- `pandas`
- `scikit-learn`
- `matplotlib`
- `PyYAML`
- `python-dotenv`

---

## Running the Tests

Run the complete test suite from the repository root:

```powershell
pytest -v
```

All existing shared tests should pass before method-specific changes are merged.

Method-specific tests may also be run individually.

Rule-based:

```powershell
pytest tests/test_rule_based.py -v
```

Constraint solver:

```powershell
pytest tests/test_solver.py -v
```

LLM-based:

```powershell
pytest tests/test_llm.py -v
```

---

## Shared Architecture

All validation methods use the shared infrastructure under:

```text
src/core/
```

Important files include:

### `src/core/models.py`

Defines common project data structures such as:

- `ERCase`
- `Entity`
- `Attribute`
- `Relationship`
- `Prediction`
- `PredictionError`

### `src/core/io.py`

Handles:

- JSON and JSONL loading
- schema validation
- prediction loading/writing
- conversion between dictionaries and dataclasses
- removal of ground truth before method execution

### `src/core/validator_interface.py`

Defines the common `BaseValidator` interface.

Every validation method must inherit from `BaseValidator`.

### `src/core/constants.py`

Defines the official:

- method names
- seven error labels
- cardinality values
- shared constants

Shared files should not be changed independently without coordinating with the team.

---

## Method Development

Each team member should work primarily inside the directory assigned to their method.

### Rule-Based Validator

Implementation:

```text
src/methods/rule_based/validator.py
```

Method name:

```text
rule_based
```

Output:

```text
outputs/rule_based/predictions.jsonl
```

Tests:

```text
tests/test_rule_based.py
```

---

### Constraint-Solver Validator

Implementation:

```text
src/methods/constraint_solver/validator.py
```

Method name:

```text
constraint_solver
```

Use the Z3 SMT solver to express and evaluate the same ER integrity constraints used by the other methods.

Output:

```text
outputs/constraint_solver/predictions.jsonl
```

Tests:

```text
tests/test_solver.py
```

---

### LLM-Based Validator

Implementation:

```text
src/methods/llm_based/validator.py
```

Prompt:

```text
src/methods/llm_based/prompt.txt
```

Method name:

```text
llm_based
```

Output:

```text
outputs/llm_based/predictions.jsonl
```

Tests:

```text
tests/test_llm.py
```

The LLM must only return the seven supported error labels.

Ground-truth labels must never be included in the model prompt.

---

## Common Prediction Format

All three methods must return the same prediction structure.

Example valid prediction:

```json
{
  "case_id": "VALID_0001",
  "method": "rule_based",
  "predicted_valid": true,
  "errors": [],
  "runtime_ms": 1.8
}
```

Example invalid prediction:

```json
{
  "case_id": "INVALID_E01_TEST_001",
  "method": "rule_based",
  "predicted_valid": false,
  "errors": [
    {
      "error_type": "FK_TARGET_NOT_KEY",
      "entity": "ORDER",
      "attribute": "customer_id",
      "relationship": "customer_order",
      "message": "Foreign key references a non-key attribute."
    }
  ],
  "runtime_ms": 2.4
}
```

The full prediction specification is defined in:

```text
schemas/prediction.schema.json
```

---

## Ground-Truth Protection

Method implementations must never inspect:

```python
case["ground_truth"]
```

Ground truth is used only for:

- dataset generation
- benchmark verification
- final evaluation

The shared I/O layer removes ground truth before cases are supplied to validators.

---

## Evaluation

Shared evaluation code belongs in:

```text
src/evaluation/
```

The project compares methods using metrics including:

- Precision
- Recall
- F1 score
- Macro-F1
- Valid/invalid accuracy
- Exact error-set accuracy
- Localization accuracy
- False-positive rate
- Runtime

Raw predictions belong in:

```text
outputs/
```

Final comparison tables and figures belong in:

```text
results/
```

---

## API Keys

Do not commit API keys to GitHub.

For the LLM method, copy:

```text
.env.example
```

to:

```text
.env
```

and add the key locally:

```text
OPENAI_API_KEY=your_key_here
```

The `.env` file is excluded from Git through `.gitignore`.

---

## Team Implementation Guide

A more detailed architecture and implementation guide is available at:

```text
report/notes/team_implementation_guide.md
```

Team members should read that file before implementing their assigned method.

It explains:

- project architecture
- shared files
- method ownership
- required interfaces
- output locations
- testing requirements
- AI-assisted coding instructions
- collaboration rules

---

## Collaboration Guidelines

Before starting work:

```powershell
git pull
```

Use a separate branch for your assigned method where appropriate.

Example:

```powershell
git checkout -b rule-based-validator
```

Before requesting a merge:

```powershell
pytest -v
```

should pass.

Do not commit:

```text
.env
__pycache__/
*.pyc
.pytest_cache/
IDE temporary files
API keys
```

Do not independently modify the benchmark, schemas, shared taxonomy, or core interfaces without coordinating with the team.

---

## Project Principle

All three validation methods must solve the same problem:

> Determine whether an ER design satisfies the project's predefined integrity and relationship constraints and identify any corresponding logical design errors.

The methods must use the same:

- benchmark
- input representation
- error taxonomy
- output schema
- evaluation procedure

This ensures that the final performance comparison is fair and reproducible.