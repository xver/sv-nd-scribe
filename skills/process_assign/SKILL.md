---
name: process_assign
description: Generate NaturalDocs process/assign comments for procedural and continuous assignment blocks
applies_to: [ND-027, ND-028]
llm_required: false
---

## System Prompt

You are a SystemVerilog documentation expert following NaturalDocs conventions.
Generate `// process:` or `// assign:` comment blocks for procedural and continuous blocks.
Output only the comment lines — no code.

## When Documentation is Required (sv_documentation_rules.md §25)

| Construct | Required? |
|---|---|
| Named `always_ff`, `always_comb`, `always`, `initial` with `begin : label` | Required when project policy specifies it |
| `assign` continuous assignment | Required by ND-028 |
| Unlabelled `initial` / `always` blocks | Optional — no NaturalDocs comment needed |

> **Note:** sv_documentation_rules.md §25 states that `initial`/`always` blocks are optional documentation targets. Only document them when the project requires it or when they are named with `begin : label`.

## Keyword Selection (sv_documentation_rules.md §23)

| Construct | Keyword |
|---|---|
| `initial`, `always`, `always_comb`, `always_ff`, `always_latch`, `forever` | `// process:` |
| `assign` continuous assignments | `// assign:` |

## Process (sv_documentation_rules.md §23)

```systemverilog
// process: clk_gen
// Clock generation process — drives clk with 10ns period.
// Runs forever; reset by asserting rst_n.
always begin : clk_gen
  clk = 0;
  #5;
  clk = 1;
  #5;
end
```

```systemverilog
// process: register_update
// Synchronous register update on rising clock edge.
// Resets all registers to zero when rst_n is deasserted.
always_ff @(posedge clk or negedge rst_n) begin : register_update
  if (!rst_n)
    data_reg <= '0;
  else
    data_reg <= data_in;
end
```

Rules:
- Keyword: `// process: <descriptive_name>`
- Use the `begin : <label>` label as the process name identifier.
- Description: what the process does AND its trigger condition.

## Assign (sv_documentation_rules.md §23)

```systemverilog
// assign: out_valid
// Output valid signal — asserted whenever the pipeline output register is non-zero.
assign out_valid = (out_data != '0);

// assign: status_word
// Status word combining the ready, valid, and error flags for the AXI response.
assign status_word = {rdy, vld, err};
```

Rules:
- Keyword: `// assign: <signal_name>` — use the left-hand side signal name.
- Description: explain what drives the signal and the logic being expressed.

## Description Quality Guidelines & Anti-Boilerplate Rules

Generic placeholders and common-sense restatements such as:
- `SystemVerilog element definition for <name>.`
- `SystemVerilog assignment definition for <target>.`
- `SystemVerilog process definition for <name>.`
- `Initial process executing startup initialization and configuration setup.`
- `TODO [SVND]: Add description for ...`

are **STRICTLY PROHIBITED**.

For continuous assignments (`assign`):
- **Identifier**: Use the full hierarchical target signal name (e.g., `tb_if.m_abs_agent1_if.ready`), NEVER just the root interface instance (`tb_if`).
- **Handshake Tie-Offs (`ready = 1'b1`, `valid = 1'b1`)**: Explain whether the interface acts as an always-ready responder or active driver.
- **Signal Mirroring / Forwarding (`data = last_data_o`)**: Explain what captured data is mirrored and which downstream components/monitors observe it.
- **Expressions & Multiplexing**: State the arbitration condition or combinational logic being evaluated.

For procedural processes (`initial`, `always_ff`, `always_comb`):
- **Testbench Actions**: Detail configuration retrieval (`tb_template_sys_get_m_config`), virtual interface binding (`set_vif`), or watchdog setup.
- **RTL State & Triggers**: Describe register transfer logic, clock edge sensitivity, reset conditions, and transaction flow.

## Line Length Constraint (< 80 Characters)

- **Strict 80-Character Limit**: Every line of the comment block must stay strictly below 80 characters (maximum 78 characters per line).
- **Wrap Descriptions**: Break multi-line descriptions at natural word boundaries across indented lines:
  ```systemverilog
  // assign: tb_if.m_abs_agent1_if.ready
  //   Ties the ABS_AGENT1 ready handshake signal permanently high,
  //   indicating responder is always ready to receive transactions.
  assign tb_if.m_abs_agent1_if.ready = 1'b1;
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
