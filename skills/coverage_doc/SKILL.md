---
name: coverage_doc
description: Generate NaturalDocs comments for constraints, covergroups, and coverpoints
applies_to: [ND-020, ND-021, ND-022]
llm_required: false
---

## System Prompt

You are a SystemVerilog documentation expert following NaturalDocs conventions.
Generate comment blocks for coverage and constraint constructs.
Output only the comment lines — no code.

## Keyword Selection

| Construct | Keyword | Naming Convention |
|---|---|---|
| `constraint` | `// constraint:` | `_c` suffix (e.g. `addr_range_c`) |
| `covergroup` | `// covergroup:` | `_cg` suffix (e.g. `config_cg`) |
| `coverpoint` | `// coverpoint:` | `cp_` prefix (e.g. `cp_num_trans`) |

## Constraint (sv_documentation_rules.md §13)

```systemverilog
// constraint: addr_range_c
// Constrains address to valid aligned regions within the register map.
// Ensures 4KB-boundary alignment for all burst transactions.
constraint addr_range_c {
  addr inside {[32'h0000_0000 : 32'hFFFF_FFFF]};
  addr % 4096 == 0;
}
```

Rules:
- Keyword line: `// constraint: <name>`
- Description: explain what is being constrained and why.
- The constraint name MUST match the code identifier.
- No `m_` prefix on constraint names (naming convention §1).

## Covergroup (sv_documentation_rules.md §14)

```systemverilog
// covergroup: config_cg
// Covergroup that samples configuration parameter combinations.
// Tracks whether all important config states have been exercised.
covergroup config_cg;
```

Rules:
- Keyword line: `// covergroup: <name>`
- Description: explain what is being covered and why it matters.
- `endgroup : <name>` end label is REQUIRED (sv_documentation_rules.md §26).
- `_cg` suffix is convention (sv_naming_format_conventions.md §10).

## Coverpoint (sv_documentation_rules.md §15)

```systemverilog
// coverpoint: cp_num_trans
//   Coverpoint that samples the number of transactions generated per test.
//   Covers low (1-100), mid (101-500), and high (501-1000) ranges.
  cp_num_trans: coverpoint m_num_transactions {
    bins low  = {[1:100]};
    bins mid  = {[101:500]};
    bins high = {[501:1000]};
  }
```

Rules:
- Keyword line: `// coverpoint: <label>`
- Description: indented with `//   ` (3 extra spaces).
- The coverpoint label in the comment MUST match the label in the code.
- `cp_` prefix is convention (sv_naming_format_conventions.md §11).
- Describe **what** is sampled and the meaningful bins or ranges.

## Description Quality Guidelines

- **Constraint**: Say what is constrained AND why (valid ranges, alignment requirements, protocol rules).
- **Covergroup**: Say what functional scenario is being measured.
- **Coverpoint**: Say what signal/variable is sampled and what the bins represent.

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
