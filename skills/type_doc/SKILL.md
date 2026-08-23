---
name: type_doc
description: Generate NaturalDocs comments for typedef enums, structs, unions, and packages
applies_to: [ND-008, ND-010, ND-011]
llm_required: false
---

## System Prompt

You are a SystemVerilog documentation expert following NaturalDocs conventions.
Generate NaturalDocs comment blocks for type definition constructs.
Output only the comment lines — no code.

## Keyword Selection (sv_documentation_rules.md §6, §8–§11)

| Construct | Keyword | Naming Convention |
|---|---|---|
| `package` | `// Package:` | `_pkg` suffix (e.g. `nd_example_pkg`) |
| `typedef enum {...} name_e` | `// enum:` | `_e` suffix (e.g. `state_e`) |
| `typedef struct packed {...} name_t` | `// Struct:` | `_t` suffix (e.g. `ctrl_fields_t`) |
| `typedef union packed {...} name_t` | `// Union:` | `_t` suffix (e.g. `data_overlay_t`) |
| `typedef logic [N:0] name_t` | `// Variable:` | `_t` suffix (e.g. `addr_t`) |

## Examples

### Package (sv_documentation_rules.md §6)

```systemverilog
// Package: nd_example_pkg
// Example package demonstrating correct NaturalDocs documentation.
// Contains properly documented classes, functions, tasks, and constraints.
package nd_example_pkg;
```

### Enum (sv_documentation_rules.md §8)

```systemverilog
// enum: state_e
// State machine enumeration type for agent states
typedef enum {
  IDLE_t,   /// IDLE state
  ACTIVE_t, /// ACTIVE state
  WAIT_t,   /// Wait state
  DONE_t    /// Done state
} state_e;
```

Rules:
- Each enum value SHOULD have an inline `//` trailing comment.
- `///` triple-slash is preferred as forward-compat with NaturalDocs 2.5+.
- `_e` suffix is a linted convention for enum type names.
- Values use `UPPER_SNAKE_CASE` (no suffix).

### Struct (sv_documentation_rules.md §10)

```systemverilog
// Struct: ctrl_fields_t
// Packed struct holding transaction control fields
typedef struct packed {
  logic [3:0] burst_len; /// burst length in beats
  logic [2:0] prot;      /// protection type
  logic       lock;      /// lock signal
} ctrl_fields_t;
```

Rules:
- Each member field SHOULD have an inline `///` trailing comment.
- `_t` suffix is a linted convention for struct type names.

### Union (sv_documentation_rules.md §11)

```systemverilog
// Union: data_overlay_t
// Packed union allowing raw or byte-level access to a 16-bit value
typedef union packed {
  logic [15:0] raw;       /// Raw 16-bit word value
  logic [1:0][7:0] bytes; /// Byte-level slice access
} data_overlay_t;
```

### Simple Type Alias (sv_documentation_rules.md §9)

```systemverilog
// Variable: addr_t
// Address type for memory operations (32-bit wide)
typedef logic [31:0] addr_t;
```

## User Prompt Template

```
Linter violation:
  Rule:    {{rule_id}}
  Message: {{message}}
  File:    {{file}}, Line: {{line}}

Declaration context (lines {{context_start}}–{{context_end}}):
{{source_context}}

Generate the NaturalDocs comment for this {{construct_type}} named {{name}}.
Output only the comment lines.
```
