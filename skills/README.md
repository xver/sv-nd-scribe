# SystemVerilog NaturalDocs Skills Knowledge Base ![](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)

![sv-nd-scribe Logo](../scribe_logo.jpg)

← [Back to main README](../README.md)


The `skills/` directory contains 12 modular documentation skills designed for developers and AI assistants (Antigravity, Cursor, Claude, LLMs). Each skill specifies syntactic patterns, comment formats, parameter tags, and priority guidelines according to the NaturalDocs specification for SystemVerilog.

---

## Skill Catalog

| Skill Directory | Target Constructs | Applicable Rules | Documentation Link |
|---|---|---|---|
| **[`file_header`](file_header/SKILL.md)** | File header blocks, metadata, copyright, legal, title | `ND-001` | [View Skill](file_header/SKILL.md) |
| **[`sv_constructs`](sv_constructs/SKILL.md)** | Modules, interfaces, classes, packages, clocking blocks, modports, programs, checkers, bind | `ND-008`, `ND-009`, `ND-013`, `ND-014`, `ND-018`, `ND-025`, `ND-026`, `ND-029`, `ND-031`, `ND-032` | [View Skill](sv_constructs/SKILL.md) |
| **[`function_task`](function_task/SKILL.md)** | Functions, tasks, return values, parameters, extern declarations | `ND-016`, `ND-017`, `ND-030` | [View Skill](function_task/SKILL.md) |
| **[`process_assign`](process_assign/SKILL.md)** | Procedural blocks (`always`, `initial`, `always_ff`, `always_comb`, `always_latch`) and continuous assignments (`assign`) | `ND-027`, `ND-028` | [View Skill](process_assign/SKILL.md) |
| **[`type_doc`](type_doc/SKILL.md)** | Typedefs, enums, structs, unions | `ND-010`, `ND-011` | [View Skill](type_doc/SKILL.md) |
| **[`variable_doc`](variable_doc/SKILL.md)** | Class member variables, ports, parameters, local variables, net declarations | `ND-012`, `ND-023` | [View Skill](variable_doc/SKILL.md) |
| **[`inline_doc`](inline_doc/SKILL.md)** | Enum members, struct fields, inline field documentation | `ND-024` | [View Skill](inline_doc/SKILL.md) |
| **[`coverage_doc`](coverage_doc/SKILL.md)** | Covergroups, coverpoints, cross coverage, sample triggers | `ND-020`, `ND-021`, `ND-022` | [View Skill](coverage_doc/SKILL.md) |
| **[`assertion_property`](assertion_property/SKILL.md)** | Concurrent assertions, sequences, properties, assume, cover statements | `ND-015` | [View Skill](assertion_property/SKILL.md) |
| **[`group_heading`](group_heading/SKILL.md)** | Group headings, section divisions, architectural blocks | `ND-006` | [View Skill](group_heading/SKILL.md) |
| **[`nd_comment`](nd_comment/SKILL.md)** | NaturalDocs general syntax, colon spacing, comment styling, keyword table reference | `ND-003`, `ND-004`, `ND-005`, `ND-019` | [View Skill](nd_comment/SKILL.md) |
| **[`triage`](triage/SKILL.md)** | Multi-rule conflict resolution, fix priority hierarchy, batch sequencing | All rules | [View Skill](triage/SKILL.md) |

---

## Keyword Reference Table

The `nd_comment` skill contains the definitive mapping of SystemVerilog constructs to NaturalDocs keywords. See [`skills/nd_comment/references/keyword_table.md`](nd_comment/references/keyword_table.md) for the complete reference.

### Summary Table

| Construct | NaturalDocs Keyword | Comment Syntax |
|---|---|---|
| File Header | `File:` / `Title:` | `/* File: <name> ... */` |
| Module | `Module:` | `// Module: <name>` |
| Class | `Class:` | `// Class: <name>` |
| Interface | `Interface:` | `// Interface: <name>` |
| Package | `Package:` | `// Package: <name>` |
| Function | `Function:` | `// Function: <name>` |
| Task | `Task:` | `// Task: <name>` |
| Variable | `Variable:` | `// Variable: <name>` |
| Typedef | `Type:` / `enum:` / `struct:` | `// Type: <name>` |
| Property | `Property:` | `// Property: <name>` |
| Group | `Group:` | `// Group: <Section Name>` |
| Process | `Process:` | `// Process: <name>` |
| Continuous Assign | `Assign:` | `// Assign: <target>` |
| Covergroup | `Covergroup:` | `// Covergroup: <name>` |
| Coverpoint | `Coverpoint:` | `// Coverpoint: <name>` |
| Clocking Block | `Clocking:` | `// Clocking: <name>` |
| Modport | `Modport:` | `// Modport: <name>` |

---

## Triage Priority Hierarchy

When auto-fixing files containing multiple overlapping violations, the agent resolves rules according to the priority table defined in [`skills/triage/references/priority_table.md`](triage/references/priority_table.md):

1. **Structural & Formatting Fixes (P1)**: `WKL-006` (trailing whitespace), `WKL-008` (tabs), `WKL-005` (EOF newline).
2. **File Level Blocks (P2)**: `ND-001` (file header), `ND-002` (include guard).
3. **Containers & High-Level Constructs (P3)**: `ND-008` (package), `ND-014` (module), `ND-013` (interface), `ND-009` (class).
4. **Member Declarations (P4)**: `ND-017` (function/task), `ND-020` (constraint), `ND-021` (covergroup), `ND-023` (variable).
5. **Inline & Statement Level (P5)**: `ND-024` (inline enum/struct items), `ND-027` (process), `ND-028` (assign).

---

## Support

For assistance with integration or customization, contact us at [icshunt.help@gmail.com](mailto:icshunt.help@gmail.com).

Report bugs and feature requests to [GitHub Issues](https://github.com/xver/sv-nd-scribe/issues).

---

![img](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![img](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)
Copyright (c) 2026 IC Verimeter
