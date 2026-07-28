<!--
  Copyright (c) 2026 IC Verimeter
  Licensed under the MIT license. See LICENSE file in the project root for details.
-->

# SystemVerilog NaturalDocs Documentation Rules

> **Apply together with `sv_naming_conventions.md`.**

This file defines the mandatory rules for documenting SystemVerilog files
using NaturalDocs-style comments. All rules are derived from the reference
file `good_example.sv` and the NaturalDocs configuration (`Comments.txt`,
`Languages.txt`).

When asked to document, lint, or review a SystemVerilog file, apply every
rule in this document.

***

## 1  General Principles

1. **Every documentable SystemVerilog statement MUST have a NaturalDocs comment block immediately above it** (no blank lines between the comment and the statement).
2. Both `//` line comments and `/* */` block comments are fully supported by NaturalDocs. The only hard requirement is that **no part of a NaturalDocs comment may be on the same line as code**. The project convention is to use `//` line comments for all documentation comments and reserve `/* */` for the file header — but this is a convention, not a NaturalDocs restriction.
3. **Spacing rule — applies to every NaturalDocs comment line without exception:**
    - Every NaturalDocs comment line must begin with `//` followed by either a space or a keyword token such as `Group:` or `define:`.
    - Every keyword line ends with `:` which MUST be followed by **at least one space** before the identifier or description text.
    - Valid: `// Group: identifier` · `// Description text` · `//Group: Preprocessor Defines`
    - Invalid: `//Keyword:identifier` · `//Keyword: identifier` · `// Keyword:identifier`
    - Violations cause NaturalDocs to **silently drop** the comment from output.
4. Multi-line descriptions continue with `// ` prefix and maintain consistent indentation.
5. All NaturalDocs keywords are not **case-sensitive** .

### Canonical format

```systemverilog
// Keyword: identifier
// First line of description.
// Continued description if needed.
<code statement>
```


***

## 2  File Header

Every `.sv` file MUST begin with a block comment header using `/* */` syntax:

```systemverilog
/*******************************************************************************
 * File: <filename>.sv
 *
 * Company: <company name>
 *
 * Author: <email>
 *
 * Description: <brief multi-line description of the file's purpose>
 *
 * Created: <date> (<author>)
 *
 * Updated: <date> (<author>)
 ******************************************************************************/
```


### Rules

- The asterisk border uses exactly 80 characters.
- Fields: `File`, `Company`, `Author`, `Description`, `Created`, `Updated`.
- `Author` field format: `<email address>` — an email address is required. A full name before the email is optional.
- `Description` may span multiple lines, each prefixed with ` *` and aligned.
- `Created` and `Updated` include both date and author email in parentheses.

***

## 3  Include Guards

Files MUST use ```ifndef / `define / `endif`` include guards. The guard macro name is the file name in upper case with `.` replaced by `_`:

```systemverilog
`ifndef GOOD_EXAMPLE_SV
`define GOOD_EXAMPLE_SV
// ... file contents ...
`endif // GOOD_EXAMPLE_SV
```

The ```endif`` line MUST carry a trailing comment naming the guard macro. Include guards themselves do NOT require a NaturalDocs comment and should not trigger ND-007.

***

## 4  Groups (`// Group:`)

Use `// Group:` to create logical sections within a scope (file, package, class, module, interface). Groups act as section headings.

```systemverilog
// Group: Preprocessor Defines

// Group: Type Definitions

// Group: Configuration Classes

// Group: Methods
```


### Rules

- `// Group: <section name>` — exactly this format.
- Every class should organise its members under Groups (e.g. `Configuration Parameters`, `Constraints`, `Coverage`, `Methods`, `Transaction Fields`, `Analysis Ports`, `Internal State`, `Statistics`).
- Groups do **not** document a code element directly; they organise the elements that follow.

***

## 5  Preprocessor Defines (`// define:`)

NaturalDocs keyword: **`define`** (mapped to the Macro comment type).

```systemverilog
// define: ND_MAX_BURST_LEN
// Maximum burst length supported by the DUT (decimal)
`define ND_MAX_BURST_LEN 256
```


### Rules

- Keyword line: `// define: <MACRO_NAME>`
- Description lines follow immediately, each starting with `// `.
- Multi-line descriptions are allowed and encouraged for complex macros.
- For multi-line defines (backslash continuation), describe what the macro does and note that it is multi-line:

```systemverilog
// define: ND_CHECK_FIELD
// Multi-line define that compares a transaction field and reports
// an error on mismatch. Demonstrates a multi-line macro with
// hex literal and begin/end block.
`define ND_CHECK_FIELD(FIELD, EXP) \
  begin \
    ...
  end
```


***

## 6  Packages (`// Package:`)

NaturalDocs keyword: **`Package`** (built-in).

```systemverilog
// Package: nd_example_pkg
// Example package demonstrating correct NaturalDocs documentation.
// This package contains properly documented classes, functions, tasks,
// and constraints that comply with ND coding standards.
package nd_example_pkg;
```


### Rules

- Keyword line: `// Package: <package_name>`
- Description: one or more lines explaining the package purpose and contents.
- The package name in the comment MUST match the identifier in the `package` statement.

***

## 7  Classes (`// Class:`)

NaturalDocs keyword: **`Class`** (built-in, with `Scope: Start`).

```systemverilog
// Class: nd_config
// Configuration class for the verification environment.
// Contains all configuration parameters for the testbench components.
class nd_config extends uvm_object;
```


### Rules

- Keyword line: `// Class: <class_name>`
- Description: multi-line explanation of class purpose.
- The class name MUST match the code identifier.
- The `endclass` line MUST carry a label: `endclass : <class_name>`.

***

## 8  Enumerations (`// enum:`)

NaturalDocs keyword: **`enum`** (custom comment type).

```systemverilog
// enum: state_e
// State machine enumeration type for agent states
typedef enum {
  IDLE,    // IDLE state
  ACTIVE,  // ACTIVE state
  WAIT,    // Wait state
  DONE     // Done state
} state_e;
```


### Rules

- Keyword line: `// enum: <enum_type_name>`
- Description line(s) explaining the enum purpose.
- Each enum value SHOULD have an inline `//` trailing comment describing it.
- **Inline enum documentation is pregferable (`///`):** NaturalDocs 2.4 does not yet support same-line quick documentation for SystemVerilog enums (only C\# has full parser support). Use plain `//` inline comments for enum values until ND 2.5+ adds SystemVerilog full-parser support. See §24 for details.

***

## 9  Typedefs / Type Aliases (`// Variable:`)

NaturalDocs keyword: **`Variable`** (built-in).

For simple type aliases (`typedef logic [...] name_t`):

```systemverilog
// Variable: addr_t
// Address type for memory operations
typedef logic [31:0] addr_t;
```


### Rules

- Keyword line: `// Variable: <type_name>`
- Description explaining what the type represents and its width/purpose.

***

## 10  Structs (`// Struct:`)

NaturalDocs keyword: **`Struct`** (altered built-in comment type).

```systemverilog
// Struct: ctrl_fields_t
// Packed struct holding transaction control fields
typedef struct packed {
  logic [3:0] burst_len; // burst length in beats
  logic [2:0] prot;      // protection type
  logic       lock;      // lock signal
} ctrl_fields_t;
```


### Rules

- Keyword line: `// Struct: <struct_name>`
- Description explaining what the struct contains.
- Each member field SHOULD have an inline `//` trailing comment.
- Inline documentation is preferable (`///`)

***

## 11  Unions (`// Union:`)

NaturalDocs keyword: **`Union`** (custom comment type).

```systemverilog
// Union: data_overlay_t
// Packed union allowing raw or byte-level access to a 16-bit value
typedef union packed {
  logic [15:0] raw;
  logic [1:0][7:0] bytes;
} data_overlay_t;
```


### Rules

- Keyword line: `// Union: <union_name>`
- Description explaining the union purpose and access modes.
- Inline documentation is preferable (`///`)
***

## 12  Variables, Signals, and Ports (`// Variable:`)

NaturalDocs keyword: **`Variable`** (built-in).

Applies to: `rand` fields, plain fields, `bit`, `logic`, `int`, `time`, `parameter`, `localparam`, UVM analysis ports, interface signals, module-level signals, and interface/module instances.

```systemverilog
// Variable: m_num_transactions
// Number of transactions to generate
rand int m_num_transactions;

// Variable: NUM_LANES
// Number of data lanes supported by the DUT
parameter int NUM_LANES = 4;

// Variable: DEFAULT_TIMEOUT
// Default timeout value used when no override is provided
localparam int DEFAULT_TIMEOUT = 5000;

// Variable: m_analysis_port
// Analysis port for broadcasting observed transactions
uvm_analysis_port #(nd_transaction) m_analysis_port;

// Variable: addr
// Address bus for memory-mapped transactions
logic [31:0] addr;

// Variable: bus_if
// Bus interface instance connecting DUT to the verification environment
nd_bus_if bus_if (.clk(clk), .rst_n(rst_n));
```


### Rules

- Keyword line: `// Variable: <variable_name>`
- Description: explain purpose, units, encoding, or special values.
- Covers **all** of the following SystemVerilog declarations:
    - `rand` / `randc` variables
    - Plain class member variables (`bit`, `logic`, `int`, `string`, etc.)
    - `parameter` and `localparam` declarations
    - `time` variables
    - UVM analysis ports and other TLM port objects
    - `uvm_verbosity` and similar UVM type fields
    - Interface signals (`logic` declarations inside `interface` blocks)
    - Module-level signals (`logic` declarations inside `module` blocks)
    - Interface or module instances declared as variables

***

## 13  Constraints (`// constraint:`)

NaturalDocs keyword: **`constraint`** (custom comment type).

```systemverilog
// constraint: addr_range_c
// Constrains address to valid memory range
constraint addr_range_c {
  m_addr inside {[32'h1000:32'h1FFF]};
  m_addr[1:0] == 2'b00;  // Word aligned
}
```


### Rules

- Keyword line: `// constraint: <constraint_name>`
- Description explaining what the constraint enforces and why.
- The constraint name in the comment MUST match the code identifier.
- Inline documentation is preferable (`///`)
***

## 14  Covergroups (`// covergroup:`)

NaturalDocs keyword: **`covergroup`** (custom Coverage comment type).

```systemverilog
// covergroup: config_cg
// Covergroup that samples configuration parameter combinations
covergroup config_cg;
```


### Rules

- Keyword line: `// covergroup: <covergroup_name>`
- Description explaining what is being covered.
- The `endgroup` line MUST carry a label: `endgroup : <covergroup_name>`.

***

## 15  Coverpoints (`// coverpoint:`)

NaturalDocs keyword: **`coverpoint`** (custom Coverage comment type).

```systemverilog
// coverpoint: cp_num_trans
//   Coverpoint that samples the number of transactions
  cp_num_trans: coverpoint m_num_transactions {
    bins low   = {[1:100]};
    bins mid   = {[101:500]};
    bins high  = {[501:1000]};
  }
```


### Rules

- Keyword line: `// coverpoint: <coverpoint_label>`
- Description: indented with `//   ` (3 extra spaces) describing what is sampled.
- The coverpoint label in the comment MUST match the label in the code.

***

## 16  Functions (`// Function:`)

NaturalDocs keyword: **`Function`** (built-in).

```systemverilog
// Function: new
// Constructor for configuration object
//
// Parameters:
//   name - Object name for UVM factory
function new(string name = "nd_config");
```


### Rules

- Keyword line: `// Function: <function_name>`
- Description line(s) explaining the function purpose.
- **Parameters section** (when the function has arguments):
    - Blank comment line (`//`) before `// Parameters:`
    - `// Parameters:` heading
    - Each parameter on its own line: `//   <param_name> - <description>`
- **Returns section** (when the function returns a meaningful value):
    - Blank comment line before `// Returns:`
    - `// Returns:` heading
    - `//   <description of return value>`
- The `endfunction` line MUST carry a label: `endfunction : <function_name>`.
- For `virtual` functions, the comment is identical — do not add `virtual` to the comment keyword line.


### Full example with Parameters and Returns

```systemverilog
// Function: do_compare
// UVM compare method override
//
// Parameters:
//   rhs      - Right-hand side object to compare with
//   comparer - UVM comparer object
//
// Returns:
//   1 if objects match, 0 otherwise
virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
```


***

## 17  Tasks (`// Function:` or `// Task:`)

NaturalDocs keyword: **`Task`** is mapped as an alias of the **`Function`** comment type in `Comments.txt`. This means NaturalDocs treats both `// Function:` and `// Task:` identically for task declarations.

**Preferred convention:** Use `// Task:` for tasks, matching the pattern used for functions. This is the style used throughout `good_example.sv` for tasks such as `run_phase`, `drive_transaction`, `collect_transaction`, and `reset_driver`. The keyword `// Task:` is also acceptable (used for `body` in `good_example.sv`).

```systemverilog
// Task: body
// Main sequence body that generates transactions.
// Creates and randomizes the specified number of transactions.
virtual task body();
```


### Rules

- Keyword line: `// Task: <task_name>` — use `Task` for **all** tasks regardless of whether they have parameters.
- Description line(s) explaining the task purpose.
- **Parameters section** follows the same rules as §16 when the task has arguments:

```systemverilog
// Task: drive_transaction
// Drive a single transaction on the interface
//
// Parameters:
//   trans - Transaction to drive
virtual task drive_transaction(nd_transaction trans);
```

- The `endtask` line MUST carry a label: `endtask : <task_name>`.

***

## 18  Extern Declarations and Out-of-Class Implementations

### Extern Prototype (inside the class)

The prototype inside the class MUST have the full NaturalDocs comment (keyword line + description):

```systemverilog
// Function: sample_config
// Trigger covergroup sampling after configuration is finalized
extern function void sample_config();

// Task: reset_driver
// Reset the driver state machine and cycle counter to initial values
extern task reset_driver();
```


### Out-of-Class Implementation (outside the class)

The out-of-class implementation also carries a NaturalDocs keyword line with a brief description noting it is the out-of-class implementation:

```systemverilog
// Out-of-class implementation of sample_config.
// Samples the configuration covergroup using the current field values.
function void nd_config_c::sample_config();
  config_cg.sample();
endfunction : sample_config

// Task: reset_driver
// Out-of-class implementation of the extern task prototype
task nd_driver::reset_driver();
  m_current_state = IDLE_t;
  m_cycle_count = 0;
endtask : reset_driver
```


### Rules

- The extern prototype inside the class MUST have the full NaturalDocs comment (keyword line + description). This is the **primary documentation entry** for the function.
- The out-of-class implementation MUST also carry a NaturalDocs keyword line (`// Function:` for functions, `// Task:` for tasks) followed by a brief description (e.g., "Out-of-class implementation of the extern prototype"). 
- The description on the out-of-class implementation should be kept brief — it is not the primary documentation. Avoid duplicating the full prototype description.

***

## 19  Interfaces (`// Interface:`)

NaturalDocs keyword: **`Interface`** (built-in).

```systemverilog
// Interface: nd_bus_if
// Simple bus interface used by the driver and monitor to communicate
// with the DUT. Contains clock, reset, address, data, and control signals.
interface nd_bus_if (input logic clk, input logic rst_n);
```


### Rules

- Keyword line: `// Interface: <interface_name>`
- Description: multi-line, explaining the interface purpose and signals.
- All signals inside the interface MUST be documented with `// Variable:`.
- `modport` declarations do NOT require NaturalDocs comments.
- The `endinterface` line MUST carry a label: `endinterface : <interface_name>`.

***

## 20  Modules (`// Module:`)

NaturalDocs keyword: **`Module`** (built-in).

```systemverilog
// Module: nd_top_wrapper
// Top-level wrapper module that instantiates the bus interface and
// connects the DUT to the verification environment.
module nd_top_wrapper;
```


### Rules

- Keyword line: `// Module: <module_name>`
- Description: multi-line, explaining the module purpose.
- All signals and instances inside the module MUST be documented with `// Variable:`.
- `initial` and `always` blocks inside modules do NOT require NaturalDocs comments (unless the project chooses to document them using the `// process:` keyword).
- The `endmodule` line MUST carry a label: `endmodule : <module_name>`.

***

## 21  UVM Phase Methods

UVM phase methods (`build_phase`, `run_phase`, `report_phase`, etc.) follow the same rules as regular Functions. Use `// Function:` for **all** phase methods, whether they are declared as `function` or `task`:

```systemverilog
// Function: build_phase
// UVM build phase — get configuration object from the config DB.
//
// Parameters:
//   phase - UVM phase object
virtual function void build_phase(uvm_phase phase);

// Task: run_phase
// UVM run phase - main driver execution
//
// Parameters:
//   phase - UVM phase object
virtual task run_phase(uvm_phase phase);
```


### Rules

- Use `// Function:` for function-based phases (`build_phase`, `report_phase`, `connect_phase`, etc.).
- Use `// Task:` for task-based phases (`run_phase`, etc.).
- Always include the `Parameters` section with `phase` described.

***

## 22  Properties and Assertions (`// Property:` / `// Assertion:`)

NaturalDocs keywords: **`Property`**, **`Assertion`** (custom comment types from `Comments.txt`).

```systemverilog
// Property: stable_addr_during_burst
// Verifies that the address remains stable throughout a burst transfer.
property stable_addr_during_burst;
  @(posedge clk) burst_active |-> ##[1:$] $stable(addr);
endproperty : stable_addr_during_burst

// Assertion: chk_stable_addr
// Checks stable_addr_during_burst at all times.
chk_stable_addr: assert property (stable_addr_during_burst)
  else $error("Address changed during burst");
```


### Rules

- Keyword line: `// Property: <property_name>` or `// Assertion: <label_name>`.
- Description: explain what is being checked and under what condition.
- `endproperty` MUST carry a label: `endproperty : <property_name>`.
- `assert`, `assume`, and `cover` statements that have a label use `// Assertion:`.
- Unlabelled assertions do NOT require a NaturalDocs comment.

***

## 23  Additional Comment Types (from NaturalDocs Configuration)

The following comment types are defined in the project's `Comments.txt` and are available when the corresponding SystemVerilog constructs appear:


| Keyword | Use For |
| :-- | :-- |
| `// checker:` | `checker` declarations |
| `// bind:` | `bind` statements (mapped to Function comment type) |
| `// assertion:` | Labelled assertion declarations |
| `// process:` | `initial`, `always`, `always_comb`, `always_ff`, `always_latch`, `forever` blocks |
| `// assign:` | `assign` continuous assignments |
| `// program:` | `program` blocks |

### Format for these types

```systemverilog
// checker: <checker_name>
// <description>
checker <checker_name>(...);
...
endchecker : <checker_name>

// bind: <instance_name>
// <description of the binding>
bind <target_module> <checker_or_module> <instance_name> (...);

// assign: <signal_name>
// <description of the assignment>
assign <signal_name> = <expression>;

// process: <descriptive_name>
// <description of what the process does>
always_ff @(posedge clk) begin : <descriptive_name>
  ...
end

// program: <program_name>
// <description of the program block>
program <program_name>;
  ...
endprogram : <program_name>
```


***

## 24  Quick Documentation (`///`) — Future Feature

NaturalDocs 2.4 introduced "Finishing Up Quick Documentation" — inline same-line comments using `///` — **for C\# only**. SystemVerilog is currently a basic/commented-code language in NaturalDocs and does not have a full parser, so the quick-documentation machinery is **not activated** for SV.

**Current status (ND 2.4):**

- Use `///` (triple-slash) for inline comments on enum values and struct/union members. While these are **not rendered** by NaturalDocs 2.4 for SystemVerilog, the triple-slash convention:
  - Provides clear human-readable documentation inline.
  - Distinguishes documentation-intent comments from ordinary code comments.
  - Will automatically become NaturalDocs documentation once SV full-parser support arrives.
- Use the standard `// enum:` / `// Struct:` / `// Union:` block comment above the `typedef` for all generated documentation.
- Plain `//` inline comments remain appropriate for regular code comments (not documentation-intent).

**Example:**

```systemverilog
typedef enum {
  IDLE_t, /// IDLE state
  ACTIVE_t, /// ACTIVE state
} state_e;

typedef struct packed {
  logic [3:0] burst_len; /// burst length in beats
  logic [2:0] prot; /// protection type
} ctrl_fields_t;
```

**Expected in ND 2.5+:**

- The ND author has stated SystemVerilog full-parser support (which would unlock `///` quick documentation) is planned for the 2.5 release cycle.
- Once available, this section will be updated with the activated syntax.

***

## 25  What Does NOT Require NaturalDocs Documentation

1. **Include guard directives** (```ifndef``, ```define``, ```endif``).
2. **`import` statements** (e.g., `import uvm_pkg::*;`).
3. **```include`` directives** (e.g., ```include "uvm_macros.svh"``).
4. **UVM utility macros** (```uvm_object_utils``, ```uvm_component_utils``).
5. **`modport` declarations** inside interfaces.
6. **`initial` / `always` blocks** (optional — use `// process:` only when project policy requires it).
7. **Inline code comments** (regular `//` comments that are not NaturalDocs documentation).
8. **`bins` declarations** inside coverpoints.

***

## 26  End Labels

| Construct | End Statement |
| :-- | :-- |
| `package` | `endpackage : <name>` |
| `class` | `endclass : <name>` |
| `function` | `endfunction : <name>` |
| `task` | `endtask : <name>` |
| `covergroup` | `endgroup : <name>` |
| `interface` | `endinterface : <name>` |
| `module` | `endmodule : <name>` |
| `property` | `endproperty : <name>` |
| `checker` | `endchecker : <name>` |
| `program` | `endprogram : <name>` |
| ```endif`` | ```endif // <GUARD_MACRO>`` |  |


***

## 27  Formatting Summary

| Element | Comment Keyword | Example Identifier |
| :-- | :-- | :-- |
| File header | `/* */` block | N/A |
| Section heading | `// Group:` | `Methods` |
| Preprocessor define | `// define:` | `ND_MAX_BURST_LEN` |
| Package | `// Package:` | `nd_example_pkg` |
| Class | `// Class:` | `nd_config` |
| Enum typedef | `// enum:` | `state_e` |
| Struct typedef | `// Struct:` | `ctrl_fields_t` |
| Union typedef | `// Union:` | `data_overlay_t` |
| Type alias (typedef) | `// Variable:` | `addr_t` |
| Variable / signal | `// Variable:` | `m_addr` |
| Parameter | `// Variable:` | `NUM_LANES` |
| Localparam | `// Variable:` | `DEFAULT_TIMEOUT` |
| Analysis port | `// Variable:` | `m_analysis_port` |
| Interface instance | `// Variable:` | `bus_if` |
| Constraint | `// constraint:` | `addr_range_c` |
| Covergroup | `// covergroup:` | `config_cg` |
| Coverpoint | `// coverpoint:` | `cp_num_trans` |
| Function | `// Function:` | `new` |
| Task (any) | `// Task:` (preferred) or `// Function:` | `run_phase`, `body` |
| Extern prototype | `// Function:` | `sample_config` |
| Extern implementation | `// Function:` (brief description) | `sample_config` |
| Interface | `// Interface:` | `nd_bus_if` |
| Module | `// Module:` | `nd_top_wrapper` |
| Property | `// Property:` | `stable_addr_during_burst` |
| Assertion | `// Assertion:` | `chk_stable_addr` |
| Checker | `// checker:` | `protocol_checker` |
| Binding | `// bind:` | `dut_bind` |
| Process | `// process:` | `clk_gen` |
| Assign | `// assign:` | `out_signal` |
| Program | `// program:` | `test_program` |
| Clocking | `// Clocking:` | `manager_cb` |
| Modport | `// Modport:` | `manager` |


***

## 28  Checklist for Reviewing a SystemVerilog File

- [ ] File header exists with all required fields (`File`, `Company`, `Author` as `<email>`, `Description`, `Created`, `Updated`)
- [ ] Include guards are present and correctly named
- [ ] Every `package` has `// Package:` comment
- [ ] Every `class` has `// Class:` comment
- [ ] Every `function` has `// Function:` comment with `Parameters` / `Returns` sections as applicable
- [ ] Every `task` has `// Task:` comment with `Parameters` section as applicable
- [ ] Every variable / signal / port has `// Variable:` comment
- [ ] Every `parameter` and `localparam` has `// Variable:` comment
- [ ] Every `constraint` has `// constraint:` comment
- [ ] Every `covergroup` has `// covergroup:` comment
- [ ] Every `coverpoint` has `// coverpoint:` comment
- [ ] Every `typedef enum` has `// enum:` comment
- [ ] Every `typedef struct` has `// Struct:` comment
- [ ] Every `typedef union` has `// Union:` comment
- [ ] Every `typedef` (simple alias) has `// Variable:` comment
- [ ] Every `interface` has `// Interface:` comment
- [ ] Every `module` has `// Module:` comment
- [ ] Every named `property` has `// Property:` comment
- [ ] Every labelled assertion has `// Assertion:` comment
- [ ] Every `checker` has `// checker:` comment
- [ ] Every `program` has `// program:` comment
- [ ] Every `clocking` block has `// Clocking:` comment
- [ ] Every `modport` declaration has `// Modport:` comment
- [ ] Every `bind` statement has `// bind:` comment
- [ ] Every named `initial`/`always`/`always_comb`/`always_ff` process block has `// process:` comment
- [ ] Every `assign` continuous assignment has `// assign:` comment
- [ ] Every extern prototype has a full NaturalDocs comment; its out-of-class implementation also has a `// Function:` keyword line with a brief description
- [ ] Logical groups (`// Group:`) organise related members
- [ ] All `end*` labels match their opening statement (see §26)
- [ ] Comment identifiers match code identifiers exactly
- [ ] No blank lines between NaturalDocs comment and the documented statement
- [ ] All comment lines follow the §1 spacing rule: `//` prefix with either a space or keyword token, space after `:` in keyword lines

