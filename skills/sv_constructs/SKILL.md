---
name: sv_constructs
description: Generate NaturalDocs comments for interfaces, modules, checkers, bind, programs, clocking, and modports
applies_to: [ND-013, ND-014, ND-025, ND-026, ND-029, ND-031, ND-032]
llm_required: false
---

## System Prompt

You are a SystemVerilog documentation expert following NaturalDocs conventions.
Generate NaturalDocs comment blocks for structural SystemVerilog constructs.
Output only the comment lines — no code.

## Keyword Selection (sv_documentation_rules.md §19, §20, §23, §27)

| Construct | Keyword | Naming Convention |
|---|---|---|
| `interface` | `// Interface:` | `_if` suffix (e.g. `nd_bus_if`) |
| `module` | `// Module:` | No specific suffix |
| `checker` | `// checker:` | No specific suffix |
| `bind` | `// bind:` | Instance name used as identifier |
| `program` | `// program:` | No specific suffix |
| `clocking` | `// Clocking:` | No specific suffix |
| `modport` | `// Modport:` | `_mp` suffix (e.g. `driver_mp`) |

## End Label Table (sv_documentation_rules.md §26)

All structural constructs REQUIRE a matching end label:

| Construct | End Statement |
|---|---|
| `interface` | `endinterface : <name>` |
| `module` | `endmodule : <name>` |
| `checker` | `endchecker : <name>` |
| `program` | `endprogram : <name>` |

## Interface (sv_documentation_rules.md §19)

```systemverilog
// Interface: nd_bus_if
// Simple bus interface used by the driver and monitor to communicate
// with the DUT. Contains clock, reset, address, data, and control signals.
interface nd_bus_if (input logic clk, input logic rst_n);
```

Rules:
- Keyword: `// Interface: <name>`
- All signals inside the interface MUST be documented with `// Variable:`.
- `_if` suffix convention (naming §15).
- `endinterface : <name>` end label required.

## Module (sv_documentation_rules.md §20)

```systemverilog
// Module: nd_top_wrapper
// Top-level wrapper module that instantiates the bus interface and
// connects the DUT to the verification environment.
module nd_top_wrapper;
```

Rules:
- Keyword: `// Module: <name>`
- All signals and instances inside MUST be documented with `// Variable:`.
- `endmodule : <name>` end label required.
- `initial`/`always` blocks do NOT require NaturalDocs comments unless project requires it.

## Checker (sv_documentation_rules.md §23)

```systemverilog
// checker: protocol_checker
// Formal checker verifying bus protocol compliance.
// Checks that all handshaking signals are correctly sequenced.
checker protocol_checker(input logic clk, input logic valid, input logic ready);
```

Rules:
- Keyword: `// checker: <name>` (lowercase `c`).
- `endchecker : <name>` end label required.

## Bind Statement (sv_documentation_rules.md §23)

```systemverilog
// bind: dut_bind
// Attaches the protocol_checker to the DUT instance for formal verification.
bind nd_dut protocol_checker dut_bind (.clk(clk), .valid(valid), .ready(ready));
```

Rules:
- Keyword: `// bind: <instance_name>`.
- Description: explain what is being bound and why.

## Program (sv_documentation_rules.md §23)

```systemverilog
// program: nd_test_program
// Top-level test program that drives the testbench stimulus.
program nd_test_program;
```

Rules:
- Keyword: `// program: <name>`.
- `endprogram : <name>` end label required.

## Clocking Block (sv_documentation_rules.md §27)

```systemverilog
// Clocking: manager_cb
// Manager clocking block defining input/output timing relative to clock edge.
clocking manager_cb @(posedge clk);
```

Rules:
- Keyword: `// Clocking: <name>`.
- Describe the clock edge and timing role (manager/subordinate/monitor).

## Modport (sv_documentation_rules.md §27)

```systemverilog
// Modport: driver_mp
// Driver modport — output signals driven by the driver, input signals observed.
modport driver_mp (output addr, output data, input ready);
```

Rules:
- Keyword: `// Modport: <name>`.
- `_mp` suffix convention (naming §16).
- Describe the direction perspective (driver drives, monitor observes, etc.).

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
