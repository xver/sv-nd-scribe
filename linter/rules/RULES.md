# Linting Rules

The linter enforces two categories of rules. Each violation is reported with a **severity** (`[ERROR]` or `[WARNING]`), a **rule ID**, and a descriptive message.

## Wellknown Rules (WKL)

Style and formatting rules that apply to all SystemVerilog files.

| Rule ID  | Severity    | Description |
|----------|-------------|-------------|
| WKL-001  | ERROR       | Class member variables must have a `m_` prefix. |
| WKL-002  | ERROR       | Typedef declarations must end with the `_t` suffix. |
| WKL-003  | ERROR       | Macro names must be in `UPPER_SNAKE_CASE`. |
| WKL-004  | ERROR       | Interface names must end with the `_if` suffix. |
| WKL-005  | **WARNING** | File must end with exactly one empty line (no missing or multiple trailing newlines). |
| WKL-006  | ERROR       | Lines must not contain trailing whitespace. |
| WKL-007  | **WARNING** | Lines must not exceed the maximum allowed length (default: 120 characters). |
| WKL-008  | ERROR       | Tab characters (`\t`) are not allowed; use spaces instead. |
| WKL-009  | ERROR       | Each data/net declaration statement must declare only one variable. |

## NaturalDocs Rules (ND)

Documentation rules that enforce [NaturalDocs](https://www.naturaldocs.org/) comment conventions in SystemVerilog source files.

| Rule ID  | Severity | Description |
|----------|----------|-------------|
| ND-001   | ERROR    | Every file must begin with a NaturalDocs file header block containing a `File:` keyword. |
| ND-002   | ERROR    | Non-module `.sv` files must have an `` `ifndef`` / `` `define`` include guard. |
| ND-003   | ERROR    | NaturalDocs keywords must be followed by a space and colon (e.g. `// Function: name`). |
| ND-004   | ERROR    | Any documented construct must be immediately preceded by a NaturalDocs comment block. |
| ND-005   | ERROR    | Missing space after colon in a NaturalDocs keyword (e.g. `//Function:name`). |
| ND-006   | ERROR    | Group headings must follow the format `// Group: Section Name`. |
| ND-007   | ERROR    | Macro defines must be preceded by a `// define: <name>` NaturalDocs comment. |
| ND-008   | ERROR    | Package declarations must be preceded by a `// Package: <name>` NaturalDocs comment. |
| ND-009   | ERROR    | Class declarations must be preceded by a `// Class: <name>` NaturalDocs comment. |
| ND-010   | ERROR    | Enum typedefs must be preceded by a `// enum: <name>` NaturalDocs comment. |
| ND-011   | ERROR    | Typedef declarations must be preceded by a NaturalDocs comment. |
| ND-012   | ERROR    | NaturalDocs keyword comments must include a non-empty description on the following line. |
| ND-013   | ERROR    | Interface declarations must be preceded by a `// Interface: <name>` NaturalDocs comment. |
| ND-014   | ERROR    | Module declarations must be preceded by a `// Module: <name>` NaturalDocs comment. |
| ND-015   | ERROR    | Property declarations must be preceded by a NaturalDocs comment. |
| ND-016   | ERROR    | Block constructs (`endmodule`, `endclass`, etc.) must use a labeled end statement (e.g. `endmodule : name`). |
| ND-017   | ERROR    | Functions and tasks must be preceded by a `// Function:` or `// Task:` NaturalDocs comment. |
| ND-018   | ERROR    | Checker declarations must be preceded by a NaturalDocs comment. |
| ND-019   | ERROR    | The identifier in a NaturalDocs comment must match the identifier in the code. |
| ND-020   | ERROR    | Constraint blocks must be preceded by a NaturalDocs comment. |
| ND-021   | ERROR    | Covergroup declarations must be preceded by a NaturalDocs comment. |
| ND-022   | ERROR    | Coverpoint declarations must be preceded by a NaturalDocs comment. |
| ND-023   | ERROR    | Variable and typedef declarations must include inline or preceding NaturalDocs documentation. |
| ND-024   | ERROR    | Enum items and struct fields must include an inline `//` documentation comment. |
| ND-025   | ERROR    | Checker declarations must be preceded by a `// Checker: <name>` NaturalDocs comment. |
| ND-026   | ERROR    | `bind` statements must be preceded by a NaturalDocs comment. |
| ND-027   | ERROR    | Procedural blocks (`initial`, `always`, `always_ff`, etc.) must be preceded by a NaturalDocs comment. |
| ND-028   | ERROR    | Continuous assignments (`assign`) must be preceded by a NaturalDocs comment. |
| ND-029   | ERROR    | Program declarations must be preceded by a NaturalDocs comment. |
| ND-030   | *(Disabled)* | *(Deprecated) Method documentation belongs on declarations inside class bodies, not out-of-body implementations.* |
| ND-031   | ERROR    | Clocking block declarations must be preceded by a `// Clocking: <name>` NaturalDocs comment. |
| ND-032   | ERROR    | Modport declarations must be preceded by a `// Modport: <name>` NaturalDocs comment. |
