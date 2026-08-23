# Keyword Reference Table (sv_documentation_rules.md §27)

| Construct | Comment Keyword | Example |
|---|---|---|
| File header | `/* */` block | — |
| Section heading | `// Group:` | `// Group: Methods` |
| Preprocessor define | `// define:` | `// define: ND_MAX_BURST_LEN` |
| Package | `// Package:` | `// Package: nd_example_pkg` |
| Class | `// Class:` | `// Class: nd_config` |
| Enum typedef | `// enum:` | `// enum: state_e` |
| Struct typedef | `// Struct:` | `// Struct: ctrl_fields_t` |
| Union typedef | `// Union:` | `// Union: data_overlay_t` |
| Type alias (typedef) | `// Variable:` | `// Variable: addr_t` |
| Variable / signal | `// Variable:` | `// Variable: m_addr` |
| Parameter | `// Variable:` | `// Variable: NUM_LANES` |
| Localparam | `// Variable:` | `// Variable: DEFAULT_TIMEOUT` |
| Constraint | `// constraint:` | `// constraint: addr_range_c` |
| Covergroup | `// covergroup:` | `// covergroup: config_cg` |
| Coverpoint | `// coverpoint:` | `// coverpoint: cp_num_trans` |
| Function | `// Function:` | `// Function: new` |
| Task | `// Task:` | `// Task: run_phase` |
| Extern implementation | `// Function:` or `// Task:` | — |
| Interface | `// Interface:` | `// Interface: nd_bus_if` |
| Module | `// Module:` | `// Module: nd_top_wrapper` |
| Property | `// Property:` | `// Property: stable_addr_during_burst` |
| Assertion | `// Assertion:` | `// Assertion: chk_stable_addr` |
| Checker | `// checker:` | `// checker: protocol_checker` |
| Binding | `// bind:` | `// bind: dut_bind` |
| Process | `// process:` | `// process: clk_gen` |
| Assign | `// assign:` | `// assign: out_signal` |
| Program | `// program:` | `// program: test_program` |
| Clocking | `// Clocking:` | `// Clocking: manager_cb` |
| Modport | `// Modport:` | `// Modport: manager` |
