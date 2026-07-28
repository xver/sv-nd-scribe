<!--
  Copyright (c) 2026 IC Verimeter
  Licensed under the MIT license. See LICENSE file in the project root for details.
-->

# SystemVerilog Naming Convention Rules

> **Apply together with `sv_documentation_rules.md`.**

When writing, reviewing, or generating SystemVerilog code, apply every rule in
this document.
---

## 1  Class Member Variable Prefix — `m_` or `is_`

Every class member variable (property) MUST start with `m_` or `is_`.

### Scope
- Inside a `class` declaration, AND
- Outside any `function`, `task`, `initial`, or `always` scope (i.e. they are
  **class properties**, not local variables).

### Valid prefixes

| Prefix | Use for | Example |
|--------|---------|---------|
| `m_`   | General class member variables | `m_num_transactions`, `m_addr`, `m_data`, `m_config`, `m_timeout_cycles` |
| `is_`  | Boolean flag / status members  | `is_active`, `is_enabled` |

### What counts as a class member variable
- `rand` / `randc` fields
- Plain fields (`bit`, `logic`, `int`, `string`, `time`, UVM types, etc.)
- Class handle members (e.g., `nd_config m_config;`)
- UVM analysis ports and TLM ports (see §4 for the port handle suffix rule)
- UVM verbosity fields (e.g., `uvm_verbosity m_verbosity;`)

### Exceptions

1. **`parameter` and `localparam`** — These are constants, not member
   variables. They do NOT require the `m_` prefix. See §13 for the `UPPER_SNAKE_CASE` naming rule.

2. **Virtual interface handles** — See §2.

3. **Port-type and Export-type handles** — If the handle type or name ends with `_port` or `_export`, the `m_` prefix is not required (e.g., `analysis_port`). See §4.

4. **UVM Special Variables** — A number of special variables named in the UVM documentation do NOT require the `m_` prefix: `is_active`, `coverage_enable`, `checks_enable`, and `regmodel`.

### Reference examples from `good_example.sv`

```systemverilog
// ✅ Correct
rand int m_num_transactions;
rand int m_timeout_cycles;
bit m_enable_coverage;
uvm_verbosity m_verbosity;
nd_config m_config;
state_t m_current_state;
int m_cycle_count;
int m_transaction_count;
// uvm_analysis_port — see §4 for port handle naming rule
rand addr_t m_addr;
rand data_t m_data;
rand bit m_write;
bit m_valid;
time m_timestamp;
rand int m_num_items;

// ❌ Wrong — missing prefix
rand int num_transactions;     // should be m_num_transactions
bit enable_coverage;           // should be m_enable_coverage
int cycle_count;               // should be m_cycle_count
```

---

## 1a  Local Variables and Function/Task Parameters — `lower_snake_case`

Variables declared **inside** a function or task (local variables) and
**function/task parameter names** MUST use `lower_snake_case` with **no prefix**.

```systemverilog
// ✅ Correct
function void process_data(int num_items, logic [31:0] base_addr);
  int loop_count;
  logic [31:0] current_addr;
  ...
endfunction : process_data

task drive_transaction(nd_transaction trans, int delay_cycles);
  int retry_count;
  ...
endtask : drive_transaction

// ❌ Wrong — m_ prefix does not apply inside functions/tasks
function void process_data(int m_num_items);  // m_ is for class members only
  int m_loop_count;                           // wrong inside a function body
endfunction : process_data
```

### Rules
- Local variables: `lower_snake_case`, no prefix.
- Function and task parameters: `lower_snake_case`, no prefix.
- Do NOT apply `m_` or `is_` to any local variable or parameter.

---

## 2  Virtual Interface Handle Names — `vif` or `*_vif`

Virtual interface handles inside a class MUST be named either:
- Exactly `vif`, OR
- End with the suffix `_vif`

The standard `m_` / `is_` prefix does **not** apply to virtual interface
handles.

### Valid names

```systemverilog
// ✅ Correct
virtual nd_bus_if vif;
virtual nd_bus_if manager_vif;
virtual nd_bus_if axi_vif;

// ❌ Wrong
virtual nd_bus_if m_vif;       // use 'vif' or '*_vif', not 'm_vif'
virtual nd_bus_if bus_handle;  // should be 'vif' or 'bus_vif'
virtual nd_bus_if intf;        // should be 'vif' or '*_vif'
```

---

## 3  Typedef and Enum Naming

This section covers two related but distinct rules: the **typedef name** suffix
and the **enum value** naming style. Keeping them together avoids splitting
enum-related rules across the document.

### 3a  Typedef Name Suffix

Every `typedef`-defined user type MUST have a suffix indicating its kind.

| Kind | Required suffix | Example |
|------|----------------|---------|
| Enum typedef | `_e` | `state_e` |
| Struct typedef | `_t` | `ctrl_fields_t` |
| Union typedef | `_t` | `data_overlay_t` |
| Simple alias typedef | `_t` | `addr_t`, `data_t` |

> **Key rule:** `_t` is reserved for typedef *names* only. Never use `_t` on
> enum *values* — see §3b below.

```systemverilog
// ✅ Correct — enum typedef
typedef enum { IDLE, ACTIVE, WAIT, DONE } state_e;

// ✅ Correct — struct typedef
typedef struct packed {
  logic [3:0] burst_len;
  logic [2:0] prot;
  logic       lock;
} ctrl_fields_t;

// ✅ Correct — union typedef
typedef union packed {
  logic [15:0] raw;
  logic [1:0][7:0] bytes;
} data_overlay_t;

// ✅ Correct — simple alias
typedef logic [31:0] addr_t;
typedef logic [63:0] data_t;

// ❌ Wrong — wrong or missing suffix
typedef enum { ... } state_type;        // should be state_e
typedef enum { ... } state_t;           // _t is reserved for non-enum typedefs
typedef struct packed { ... } ctrl_s;   // should be ctrl_fields_t
typedef logic [31:0] addr;              // missing _t
```

### 3b  Enum Value Names — `UPPER_SNAKE_CASE`

Enum literal values MUST use plain `UPPER_SNAKE_CASE` with **no suffix**.

> **Rationale:** `_t` is reserved for typedef *names* (§3a). Using `_t` on
> enum *values* creates a visual collision — a reader cannot tell if an
> identifier is a type or a value. Plain `UPPER_SNAKE_CASE` is the
> SystemVerilog standard and eliminates this ambiguity.

```systemverilog
// ✅ Correct
typedef enum {
  IDLE,
  ACTIVE,
  WAIT,
  DONE
} state_e;

// ❌ Wrong — _t suffix on values conflicts with §3a typedef rule
typedef enum {
  IDLE_t,    // _t is for typedef names, not values
  ACTIVE_t,
  WAIT_t,
  DONE_t
} state_e;
```

---

## 4  Port Handle Names — `_port` Suffix


When a variable is declared with a type whose name ends in `_port` (e.g.,
`uvm_analysis_port`, `uvm_blocking_put_port`, or any custom `*_port` type),
the **handle name** MUST also end with `_port`.

This rule applies to all non-local data declarations (class members, module
members, package-level).

```systemverilog
// ✅ Correct
uvm_analysis_port #(nd_transaction) m_analysis_port;
uvm_blocking_put_port #(data_t) m_put_port;

// ❌ Wrong — handle name missing _port suffix
uvm_analysis_port #(nd_transaction) m_ap;      // should be m_analysis_port or m_ap_port
uvm_analysis_port #(nd_transaction) analysis;   // should end with _port
```

### Interaction with `m_` prefix rule
When a port handle ends with `_port`, the `m_` prefix requirement is
**waived**. Both of these are acceptable:

```systemverilog
uvm_analysis_port #(nd_transaction) m_analysis_port;  // ✅ m_ + _port
uvm_analysis_port #(nd_transaction) analysis_port;    // ✅ _port only
```

---

## 5  Env / Agent Instance Handle Names — `_env` / `_agent` Suffix

When a variable is declared with a type whose name ends in `_env` or `_agent`,
the **handle name** MUST end with the matching suffix.

This rule applies to all non-local data declarations (class members, module
members, package-level).

| Type name ends with | Handle name must end with |
|---------------------|--------------------------|
| `_env`              | `_env`                   |
| `_agent`            | `_agent`                 |

```systemverilog
// ✅ Correct
nd_env m_nd_env;
axi_agent m_axi_agent;

// ❌ Wrong — handle suffix doesn't match type suffix
nd_env m_env_inst;        // should end with _env
axi_agent m_axi_handle;  // should end with _agent
```

---

## 6  Configuration Naming (Convention)

This section covers two related rules: the configuration **class type name**
suffix and the configuration **handle instance name**. Keeping them together
avoids splitting config-related rules across the document.

### 6a  Configuration Class Type Name — `_config` Suffix

User-defined configuration class names MUST end with `_config`.

```systemverilog
// ✅ Correct
class nd_config extends uvm_object;
class axi_config extends uvm_object;
class bus_config extends uvm_object;

// ❌ Wrong — missing _config suffix
class nd_cfg extends uvm_object;       // should be nd_config
class nd_settings extends uvm_object;  // should be *_config
class nd_params extends uvm_object;    // should use _config suffix
```

### 6b  Configuration Object Instance Name — `m_config`

The handle name of a configuration object inside any component or sequence
MUST be `m_config`. This ensures a consistent, predictable name across the
entire verification environment.

```systemverilog
// ✅ Correct
class nd_driver extends uvm_driver #(nd_transaction);
  nd_config m_config;
  ...
endclass

class nd_monitor extends uvm_monitor;
  nd_config m_config;
  ...
endclass

// ❌ Wrong — non-standard config instance name
nd_config cfg;          // should be m_config
nd_config m_cfg;        // should be m_config
nd_config config_obj;   // should be m_config
nd_config m_nd_config;  // should be m_config
```

### Convention
- Both rules are project conventions, not linted rules.

---

## 7  Constraint Names — `_c` Suffix (Convention)

The reference file uses `_c` suffix for all constraint names:

```systemverilog
constraint num_transactions_c { ... }
constraint timeout_cycles_c { ... }
constraint addr_range_c { ... }
constraint data_non_zero_c { ... }
constraint num_items_range_c { ... }
```

### Convention
- All constraint identifiers SHOULD end with `_c`.
- This is a project convention, not a linted rule.

---

## 8  External Functions and Tasks (Convention)

All functions and tasks declared inside a class MUST be defined as `extern`, with their actual implementations defined outside the class scope.

### Exceptions
- The class constructor (`function new`) is excluded from this rule and may be defined inline.

### Reference examples

```systemverilog
// ✅ Correct
class nd_driver extends uvm_driver #(nd_transaction);
  function new(string name = "nd_driver", uvm_component parent = null);
    super.new(name, parent);
  endfunction : new

  extern virtual task run_phase(uvm_phase phase);
  extern task drive_transaction(nd_transaction trans);
endclass

task nd_driver::run_phase(uvm_phase phase);
  // implementation
endtask : run_phase

task nd_driver::drive_transaction(nd_transaction trans);
  // implementation
endtask : drive_transaction

// ❌ Wrong
class nd_driver extends uvm_driver #(nd_transaction);
  // Non-constructor function defined inline
  task run_phase(uvm_phase phase);
    // inline implementation
  endtask : run_phase
endclass
```

### Convention
- All class methods (other than the constructor `new`) SHOULD be declared as `extern` inside the class, with the body defined outside the class.
- This is a project convention, not a linted rule.

---

## 9  File Organization and Naming (Convention)

Each SystemVerilog source file MUST contain only one primary declaration (one class, one module, one interface, or one package). The file name MUST be the same as the name of the declared class, module, interface, or package.

### Package Files
- Package file naming follows the `_pkg` suffix rule. See §14 for the `_pkg` suffix rule.

### Exceptions
- Test files (containing test class definitions) and sequence library files may contain several class declarations.

### Reference examples

- A class named `nd_driver` must be in a file named `nd_driver.sv`.
- An interface named `nd_bus_if` must be in a file named `nd_bus_if.sv`.
- A package named `nd_example_pkg` → file `nd_example_pkg.sv` (see §14 for the `_pkg` suffix rule).
- A test file `nd_test.sv` may include config and sequence classes
- A sequence library file `nd_seq_lib.sv` may define `nd_base_seq`, `nd_read_seq`, `nd_write_seq`, etc.

### Convention
- Source files SHOULD follow the one-construct-per-file mapping, naming files after their constructs.
- Package files SHOULD use the `_pkg` filename suffix.
- This is a project convention, not a linted rule.

---

## 10  Covergroup Names — `_cg` Suffix (Convention)

The reference file uses `_cg` suffix for covergroup names:

```systemverilog
covergroup config_cg;
```

### Convention
- All covergroup identifiers SHOULD end with `_cg`.
- This is a project convention, not a linted rule.

---

## 11  Coverpoint Labels — `cp_` Prefix (Convention)

The reference file uses `cp_` prefix for coverpoint labels:

```systemverilog
cp_num_trans: coverpoint m_num_transactions { ... }
cp_coverage_en: coverpoint m_enable_coverage;
```

### Convention
- All coverpoint labels SHOULD start with `cp_`.
- This is a project convention, not a linted rule.
nted rule.

---

## 12  Preprocessor Macro Names — `<Project_Name>_` Prefix, `UPPER_SNAKE_CASE` (Convention)

The reference file uses `ND_` as a `<Project_Name>_` prefix and `UPPER_SNAKE_CASE` for all
preprocessor defines:

```systemverilog
`define ND_MAX_BURST_LEN 256
`define ND_FIFO_DEPTH 32'h0000_0040
`define ND_BASE_ADDR 32'hDEAD_0000
`define ND_TIMEOUT_CYCLES 50000
`define ND_LOG_INFO(MSG) ...
`define ND_CHECK_FIELD(FIELD, EXP) ...
```

### Convention
- Macro names SHOULD use a project-specific prefix (e.g. `ND_`) followed by
  `UPPER_SNAKE_CASE`.
- Include guard macros follow the pattern: `FILENAME_<FILE EXTENTION>` (file basename in
  upper case, dot replaced with underscore).
- This is a project convention, not a linted rule.

---

## 13  Parameters and Localparams — `UPPER_SNAKE_CASE` (Convention)

```systemverilog
parameter int NUM_LANES = 4;
localparam int DEFAULT_TIMEOUT = 5000;
```

### Convention
- Constants use `UPPER_SNAKE_CASE` with no prefix.
- This is a project convention, not a linted rule.

---

## 14  Package Names — `_pkg` Suffix (Convention)

```systemverilog
package nd_example_pkg;
```

### Convention
- Package names SHOULD end with `_pkg`.
- This is a project convention, not a linted rule.

---

## 15  Interface Names — `_if` Suffix (Convention)

```systemverilog
interface nd_bus_if (input logic clk, input logic rst_n);
```

### Convention
- Interface names SHOULD end with `_if`.
- This is a project convention, not a linted rule.

---

## 16  Modport Names — `_mp` Suffix (Convention)

Modport identifiers inside an interface SHOULD end with `_mp`.

```systemverilog
// ✅ Correct
modport driver_mp  (output addr, output data, input  ready);
modport monitor_mp (input  addr, input  data, input  ready);

// ❌ Wrong
modport driver  (output addr, ...);
modport monitor (input  addr, ...);
```

### Convention
- This is a project convention, not a linted rule.

---

## 17  Generate Block Labels — `lower_snake_case` (Convention)

Named `generate` blocks and named `begin : label` blocks SHOULD use
`lower_snake_case`.

```systemverilog
// ✅ Correct
generate
  for (genvar i = 0; i < NUM_LANES; i++) begin : lane_gen
    ...
  end
endgenerate

// ❌ Wrong
begin : LaneGen
begin : LANE_GEN
```

### Convention
- This is a project convention, not a linted rule.

---
---

## 18  Text Format Conventions (Convention)

To ensure visual consistency and readability across the testbench codebase, all SystemVerilog files SHOULD adhere to the following formatting and layout conventions:

### 18a  Indentation and Whitespace
- **No Trailing Spaces:** Lines MUST NOT have any trailing whitespace characters at the end.
- **Structural Indentation:**
  - Content within packages, classes, modules, interfaces, and programs is indented.
  - Code blocks (`begin...end`, `fork...join`, task/function bodies, processes) indent their inner statements.
  - Multi-line statements (such as wrapped function arguments or continuous assignments) should be indented to align with the start of the expression or parameter list.

### 18b  End Labels and Block Naming
- Named blocks (`begin : block_name`) should end with matching labels when they span more than a few lines or represent main processes.
- All structural close statements (`endclass`, `endfunction`, `endtask`, `endmodule`, `endinterface`, `endpackage`, `endgroup`, `endproperty`, `endprogram`, `endchecker`) MUST end with ` : <identifier>` matching the declaration name exactly.

### 18c  File Ending
- **End-of-File Newline:** Every file MUST end with a newline at the end, as required by Verilator and compiler guidelines to avoid warnings.
---

## Quick Reference Table

| Construct | Naming Rule | Enforced? | Example |
|-----------|------------|-----------|---------| 
| Class member variable | `m_` or `is_` prefix | ✅ Linted | `m_data`, `is_active` |
| Local variable | `lower_snake_case`, no prefix | ✅ Linted | `loop_count`, `base_addr` |
| Function/task parameter | `lower_snake_case`, no prefix | ✅ Linted | `num_items`, `trans` |
| Virtual interface handle | `vif` or `*_vif` | ✅ Linted | `vif`, `axi_vif` |
| Typedef (non-enum) (§3a) | `_t` suffix | ✅ Linted | `addr_t`, `ctrl_fields_t` |
| Typedef (enum) (§3a) | `_e` suffix | ✅ Linted | `state_e` |
| Enum value (§3b) | `UPPER_SNAKE_CASE`, no suffix | Convention | `IDLE`, `ACTIVE` |
| Port handle | `_port` suffix | ✅ Linted | `m_analysis_port` |
| Env handle | `m_` prefix + `_env` suffix | ✅ Linted | `m_nd_env` |
| Agent handle | `m_` prefix + `_agent` suffix | ✅ Linted | `m_axi_agent` |
| Config class name (§6a) | `_config` suffix | Convention | `nd_config` |
| Config instance name (§6b) | `m_config` | Convention | `m_config` |
| Constraint name | `_c` suffix (no `m_` prefix) | Convention | `addr_range_c` |
| External methods | `extern` (except `new`) | Convention | `extern task run_phase(...)` |
| File organization | One construct per file | Convention | `nd_driver.sv` |
| Covergroup name | `_cg` suffix | Convention | `config_cg` |
| Coverpoint label | `cp_` prefix | Convention | `cp_num_trans` |
| Macro name | `ND_` prefix + `UPPER_SNAKE_CASE` | Convention | `ND_MAX_BURST_LEN` |
| Parameter / localparam | `UPPER_SNAKE_CASE` | Convention | `NUM_LANES` |
| Package name | `_pkg` suffix | Convention | `nd_example_pkg` |
| Interface name | `_if` suffix | Convention | `nd_bus_if` |
| Modport name | `_mp` suffix | Convention | `driver_mp` |
| Generate block label | `lower_snake_case` | Convention | `lane_gen` |