---
name: sv-technical-doc
description: >-
  Enforce deep, technically specific SystemVerilog and NaturalDocs comments.
  Strictly prohibits generic, tautological, or common-sense comments (e.g.,
  'SystemVerilog element definition for tb template if',
  'SystemVerilog assignment definition for tb if',
  'Initial process executing startup initialization',
  'SystemVerilog process definition for item'). Mandates concrete explanations
  of hardware/testbench behavior, protocol semantics, signal routing, handshake
  logic, clocking, and reset conditions. Requires all comment lines to stay
  strictly below 80 characters.
---

# Specific Technical Documentation for SystemVerilog & UVM

This skill defines mandatory quality standards for all agent-generated
NaturalDocs comments in SystemVerilog and UVM codebases.

---

## 1. Absolute Prohibition: No "Common Sense" or Boilerplate Comments

The agent **MUST NEVER** generate generic, tautological, or common-sense
comments. Any comment that merely restates the identifier name, the language
construct, or an obvious high-level truism is strictly forbidden.

### Strictly Banned Patterns:
| Banned Pattern | Why It Is Unacceptable |
| :--- | :--- |
| `SystemVerilog element definition for <name>.` | Empty generic tautology stating only construct and identifier name. |
| `SystemVerilog <kind> definition for <name>.` | Tautological boilerplate with zero design or verification insight. |
| `SystemVerilog process definition for item.` | Uses placeholder `item` and generic language construct statement. |
| `Initial process executing startup initialization and configuration setup.` | Vague hand-waving that ignores actual statements inside the block. |
| `Class member '<name>' of type <type>.` | Regurgitates syntax already visible in the line below it. |
| `Constructor creates and initializes <name>.` | Boilerplate repetition of the `new` keyword. |
| `TODO [SVND]: Add description for ...` | Unresolved placeholder stub. |
| Truncating hierarchical paths (e.g. using `tb_if` for `tb_if.m_abs_agent1_if.ready`) | Erroneously conflates container with target signal being assigned. |

---

## 2. Technical Specificity Requirements by Construct

Every comment must provide concrete, non-obvious engineering value derived
from deep analysis of the code context:

### A. Continuous Assignments (`assign`)
1. **Target Identification**:
   - For hierarchical signals (e.g., `tb_if.m_abs_agent1_if.ready = 1'b1;`),
     identify exact signal and interface role (`tb_if.m_abs_agent1_if.ready`
     or `abs_agent1_ready`), never the root interface prefix (`tb_if`).
2. **Logic and Dataflow Analysis**:
   - **Handshake Tie-Offs (`ready = 1'b1`, `valid = 1'b1`)**: Explain whether
     the interface acts as an always-ready responder or an active driver.
   - **Inactive/Reset Tie-Offs (`1'b0`, `'0`)**: Explain what function is
     disabled or held in reset.
   - **Data Passthrough / Mirroring (`data = last_data_o`)**: Explain data
     origin, destination bus, and verification role (e.g., scoreboard
     observation, downstream monitor snooping).
   - **Multiplexing / Expressions (`cond ? a : b`)**: Detail the selection
     condition and arbitration scheme.

### B. Procedural Processes (`initial`, `always_ff`, `always_comb`, `always`)
1. **Trigger & Sensitivity**: State clock edges (`posedge clk`), asynchronous
   resets, or combinational sensitivities.
2. **Operational Role**:
   - In testbenches: Configuration object retrieval
     (`tb_template_sys_get_m_config`), virtual interface binding (`set_vif`),
     watchdog timers, or stimulus sequencing.
   - In RTL/DUT: State register updates, counter increments, pipeline stage
     advances, or handshake state machines.

### C. Interfaces & Modports
1. **Container Interfaces (e.g., `tb_template_if`)**:
   - Detail structural verification role: top-level project interface container.
   - Document bundled virtual interfaces (`m_abs_agent*_if`) and link
     interfaces (`m_abs_agent*_link_if`) for DUT communication.
   - Prohibit generic tautologies like `SystemVerilog element definition for
     tb template if.`
2. **Protocol & Link Interfaces**:
   - Explain the bus protocol (AXI, APB, abstract streaming, handshake).
   - State signal roles, clock domains, and whether the interface connects
     DUT ports to UVM testbench agents.

### D. Functions & Tasks
- Detail parameter constraints, return values, algorithmic transformations,
  and UVM phase execution context (`build_phase`, `connect_phase`, `run_phase`).

---

## 3. Multi-Line Comment Formatting: Strict 80-Character Limit

Every line of a comment block—including indentation, comment delimiters
(`//`, `/*`, ` * `), and text—**MUST stay strictly below 80 characters**
(maximum 78 characters per line).

### Line Wrapping Rules:
1. **Wrap All Descriptions**: Any description exceeding 80 columns must be
   wrapped cleanly across multiple lines.
2. **Single-Line Style (`//`)**:
   ```systemverilog
   // Assign: tb_if.m_abs_agent1_if.ready
   //   Ties the ABS_AGENT1 ready handshake signal permanently high,
   //   indicating responder is always ready to receive transactions.
   assign tb_if.m_abs_agent1_if.ready = 1'b1;
   ```
3. **Block Comment Style (`/* ... */`)**:
   ```systemverilog
   /*
     Interface: tb_template_if

     Top-level project interface container bundling abstract agent pin
     interfaces and link interfaces for DUT communication.
   */
   ```
4. **Natural Word Boundaries**: Break lines at natural word boundaries or
   punctuation, never inside identifiers or expressions.

---

## 4. Comparison Reference: Common-Sense vs Specific Technical Comments

| Construct | BAD (Common-Sense / Generic) | GOOD (Specific Technical Insight < 80 chars) |
| :--- | :--- | :--- |
| `interface tb_template_if(...)` | `/*`<br>`  Interface: tb_template_if`<br>`  SystemVerilog element definition for tb template if.`<br>`*/` | `/*`<br>`  Interface: tb_template_if`<br><br>`  Top-level project interface container bundling abstract agent pin`<br>`  interfaces and link interfaces for DUT communication.`<br>`*/` |
| `assign tb_if.m_abs_agent1_if.ready = 1'b1;` | `// Assign: tb_if`<br>`// SystemVerilog assignment definition for tb if.` | `// Assign: tb_if.m_abs_agent1_if.ready`<br>`//   Ties the ABS_AGENT1 ready handshake signal permanently high,`<br>`//   indicating responder is always ready to receive transactions.` |
| `assign tb_if.m_abs_agent1_if.data = last_data_o;` | `// Assign: tb_if`<br>`// SystemVerilog assignment definition for tb if.` | `// Assign: tb_if.m_abs_agent1_if.data`<br>`//   Mirrors captured AGENT0 transfer data from last_data_o onto the`<br>`//   ABS_AGENT1 data bus for downstream observation.` |
| `initial begin ... set_vif(...) ... end` | `// Process: item`<br>`// Initial process executing startup initialization and configuration setup.` | `// Process: abs_agent0_connect`<br>`//   Retrieves top-level testbench configuration and binds the`<br>`//   ABS_AGENT0 virtual interface to the agent config in active/passive mode.` |
| `initial begin ... watchdog ... end` | `// Process: init_proc`<br>`// Process executing verification initialization.` | `// Process: watchdog_vif_connect`<br>`//   Binds physical watchdog virtual interface to watchdog agent config`<br>`//   and synchronizes clock to primary clk_if[0].` |
| `tb_template_config m_config;` | `// Variable: m_config`<br>`// Class member 'm_config' of type tb_template_config.` | `// Variable: m_config`<br>`//   Top-level environment configuration object holding sub-agent configs`<br>`//   and connection topology.` |
| `interface tb_template_common_link_if;` | `// Interface: tb_template_common_link_if`<br>`// TODO [SVND]: Add description for element 'item'` | `// Interface: tb_template_common_link_if`<br>`//   Common link interface for non-reusable testbench connections,`<br>`//   binding physical clock, reset, and watchdog VIFs to m_config.` |

---

## 5. Agent Execution Checklist Before Proposing or Modifying Any Comment

1. [ ] **No Generic Phrases**: The text contains **no** instances of
   `"element definition"`, `"definition for"`, `"description for"`,
   `"TODO [SVND]"`, or `"process definition for item"`.
2. [ ] **Accurate Identifier**: The documented identifier exactly matches
   the code construct or full hierarchical signal (not just container/prefix).
3. [ ] **Explains the "Why" and "How"**: Explains what the code accomplishes
   in verification architecture, dataflow, or protocol state.
4. [ ] **NaturalDocs Compliant**: Keyword line starts with
   `// <Keyword>: <Identifier>` (or block comment header) with exactly one
   space after colon, followed by indented description lines.
5. [ ] **Line Length < 80 Chars**: Every single line of the comment block
   is strictly below 80 characters.
