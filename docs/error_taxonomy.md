# ER Validation Error Taxonomy

## 1. Purpose

All three validation methods must use the same error taxonomy.

A method may not create its own incompatible error labels during evaluation.

The initial taxonomy contains seven non-trivial logical design errors.

---

## E01 — FK_TARGET_NOT_KEY

### Definition

A foreign key references an attribute that is not a candidate key or primary key of the referenced entity.

### Example

```text
ORDER.customer_id
    references
CUSTOMER.customer_name
```

when `customer_name` is not unique.

### Expected Detection

The validator should identify:

- child entity;
- foreign-key attribute;
- referenced entity;
- invalid referenced attribute.

---

## E02 — FK_WRONG_ENTITY

### Definition

A foreign key references a key in the wrong parent entity relative to the specified relationship or requirement.

### Example

`ORDER.customer_id` incorrectly references `EMPLOYEE.employee_id` rather than `CUSTOMER.customer_id`.

### Difference from E01

E01 concerns whether the target attribute is a valid key.

E02 concerns whether the foreign key references the logically correct parent entity.

---

## E03 — COMPOSITE_FK_INCOMPLETE

### Definition

A relationship requires a composite foreign key, but one or more required components are missing, incorrectly mapped, or incomplete.

### Example

Parent key:

```text
COURSE(CollegeID, CourseNumber)
```

Child contains only:

```text
CourseNumber
```

when both attributes are required for the reference.

---

## E04 — CARDINALITY_UNIQUENESS_CONFLICT

### Definition

The declared relationship cardinality conflicts with the uniqueness/key structure.

### Example

A relationship is declared one-to-one, but the child foreign key is not unique and therefore allows multiple child rows to reference the same parent.

### Expected Detection

The validator should report the relationship and conflicting key/cardinality information.

---

## E05 — PARTICIPATION_OPTIONALITY_CONFLICT

### Definition

The relationship participation requirement conflicts with the nullability or optionality represented by the foreign key/design.

### Example

The requirement states:

```text
Every INVOICE must belong to exactly one CUSTOMER.
```

but:

```text
INVOICE.customer_id
```

is nullable.

---

## E06 — IDENTIFYING_RELATIONSHIP_KEY_ERROR

### Definition

A relationship is declared identifying, but the parent identifier is not correctly propagated into the child's primary key.

### Example

`ORDER_LINE` is identified by:

```text
(OrderID, ProductID)
```

but an identifying relationship from `ORDER` is declared while `OrderID` is not included in the `ORDER_LINE` primary key.

---

## E07 — MISSING_REQUIRED_RELATIONSHIP

### Definition

The case requirements state that two entities must be related, but the ER design does not contain the required relationship or equivalent foreign-key connection.

### Example

The requirement states:

```text
Every appointment belongs to one patient.
```

but no Patient–Appointment relationship or corresponding foreign key exists.

---

# Additional Dataset Rules

## Valid Cases

A valid case contains no taxonomy errors:

```json
{
  "valid": true,
  "errors": []
}
```

## Single-Error Cases

A single-error case contains exactly one injected logical error.

These cases are useful for measuring per-error detection performance.

## Multi-Error Cases

A multi-error case contains two or more errors.

These cases evaluate whether a validator can detect interacting violations without stopping after the first error.

## Error Injection Rules

When generating an invalid case:

1. Start from a verified valid base case.
2. Apply a controlled mutation.
3. Record the mutation type.
4. Record the affected component.
5. Verify that the intended error is actually present.
6. Avoid unintentionally introducing unrelated errors whenever possible.

## Error Severity

Cases may optionally be classified as:

```text
low
medium
high
```

Severity describes logical impact, not visual complexity.

## Future Extensions

Additional error labels may be introduced only after team agreement.

Any new label must:

- have a precise definition;
- be detectable from the shared input representation;
- be implemented consistently in evaluation;
- appear in enough cases for meaningful comparison.


