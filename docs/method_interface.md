

# Validator Method Interface

## 1. Purpose

This document defines the software contract that all three validation methods must follow.

Each method may use a completely different internal algorithm, but its external input and output must follow the same interface.

## 2. Common Validator Contract

Conceptually, every method implements:

```python
prediction = validator.validate(case)
```

where:

- `case` is one normalized ER case;
- `prediction` follows the shared prediction schema.

## 3. Required Python Interface

Each method should expose a validator class containing:

```python
class Validator:
    method_name: str

    def validate(self, case: dict) -> dict:
        ...
```

The method name must be one of:

```text
rule_based
constraint_solver
llm_based
```

## 4. Standard Input

`validate()` receives one ER case.

Ground-truth labels must be removed or ignored before validation.

The validator may access:

- case ID;
- domain;
- entities;
- attributes;
- keys;
- foreign keys;
- relationships;
- cardinalities;
- requirements.

It must not access the gold answer during prediction.

## 5. Standard Output

Each method must return:

```json
{
  "case_id": "ER_0042",
  "method": "rule_based",
  "predicted_valid": false,
  "errors": [
    {
      "error_type": "FK_TARGET_NOT_KEY",
      "entity": "ORDER",
      "attribute": "customer_id",
      "relationship": "order_customer",
      "message": "Foreign key references a non-key attribute."
    }
  ],
  "runtime_ms": 12.4
}
```

## 6. Valid Prediction

A method predicting no error must return:

```json
{
  "case_id": "ER_0001",
  "method": "constraint_solver",
  "predicted_valid": true,
  "errors": [],
  "runtime_ms": 8.2
}
```

## 7. Error Labels

`error_type` must use labels from:

```text
docs/error_taxonomy.md
```

Initially supported:

```text
FK_TARGET_NOT_KEY
FK_WRONG_ENTITY
COMPOSITE_FK_INCOMPLETE
CARDINALITY_UNIQUENESS_CONFLICT
PARTICIPATION_OPTIONALITY_CONFLICT
IDENTIFYING_RELATIONSHIP_KEY_ERROR
MISSING_REQUIRED_RELATIONSHIP
```

## 8. Command-Line Interface

Each method should support the same command pattern.

Example:

```bash
python -m src.methods.rule_based.validator \
    --input data/test.jsonl \
    --output outputs/rule_based/predictions.jsonl
```

Constraint solver:

```bash
python -m src.methods.constraint_solver.validator \
    --input data/test.jsonl \
    --output outputs/constraint_solver/predictions.jsonl
```

LLM validator:

```bash
python -m src.methods.llm_based.validator \
    --input data/test.jsonl \
    --output outputs/llm_based/predictions.jsonl
```

## 9. Batch Processing

Each validator must:

1. load input cases;
2. validate each case independently;
3. record runtime;
4. produce one prediction per case;
5. preserve the original `case_id`;
6. write predictions as JSONL.

One failed case should not terminate evaluation of the entire dataset.

## 10. Runtime Measurement

Runtime must be measured around the validation operation.

Example:

```python
start = time.perf_counter()
prediction = validator.validate(case)
runtime_ms = (time.perf_counter() - start) * 1000
```

For the LLM method, API/network latency should be reported as part of inference runtime and documented separately where appropriate.

## 11. Method-Specific Freedom

Each teammate may choose the internal implementation of their assigned method.

### Rule-Based Method

May use:

- Python;
- NetworkX;
- deterministic validation functions;
- graph traversal;
- key/relationship consistency rules.

### Constraint-Solver Method

May use:

- Python;
- Z3;
- Boolean constraints;
- integer/cardinality constraints;
- satisfiability checking.

### LLM-Based Method

May use:

- a documented LLM;
- a fixed prompt template;
- structured JSON output;
- deterministic or low-temperature generation settings where supported.

The LLM prompt must not contain test-case answers.

## 12. Required Method Documentation

Each method owner must provide:

- brief description;
- algorithm or pseudocode;
- dependencies;
- assumptions;
- command to run;
- parameters;
- output location;
- known limitations.

This information will later be incorporated into the project README and paper.

## 13. Method-Specific Tests

Each method owner is responsible for their unit test:

```text
tests/test_rule_based.py
tests/test_solver.py
tests/test_llm.py
```

The Benchmark/Integration Lead is responsible for:

```text
tests/test_data_schema.py
tests/test_evaluation.py
```

## 14. Output Directories

Each method writes only to its assigned directory:

```text
outputs/
├── rule_based/
├── constraint_solver/
└── llm_based/
```

Methods must not overwrite another method's output.

## 15. Evaluation Separation

Individual validators do not calculate final comparison metrics.

Final metrics are computed centrally by:

```text
src/evaluation/metrics.py
src/evaluation/evaluate.py
src/evaluation/compare_methods.py
```

This prevents each method from using different evaluation definitions.

## 16. Reproducibility

Where randomness is used:

- document the random seed;
- expose the seed as a parameter where practical;
- record relevant configuration;
- preserve case IDs.

The same test cases must produce a comparable set of predictions across all methods.