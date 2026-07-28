/******************************************************************************
 * File: nd_example_pkg.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Example package demonstrating correct NaturalDocs documentation.
 *              This package contains properly documented classes, functions, tasks,
 *              and constraints that comply with ND coding standards.
 *
 * Created: July 25, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

//Group: Preprocessor Defines

//define: ND_MAX_BURST_LEN
//Maximum burst length supported by the DUT (decimal)
`define ND_MAX_BURST_LEN 256

//define: ND_FIFO_DEPTH
//Depth of the internal FIFO in entries (hex)
`define ND_FIFO_DEPTH 32'h0000_0040

//define: ND_BASE_ADDR
//Base address of the register block.
//Aligned to a 4 KB boundary in the system memory map.
`define ND_BASE_ADDR 32'hDEAD_0000

//define: ND_TIMEOUT_CYCLES
//Number of clock cycles before the watchdog fires.
//Chosen to be long enough for the slowest expected transaction
//but short enough to catch real hangs during simulation.
`define ND_TIMEOUT_CYCLES 50000

//define: ND_LOG_INFO
//Convenience macro for logging an info message with the component name.
//Uses backslash continuation for a multi-line define (single statement).
`define ND_LOG_INFO(MSG) \
  `uvm_info(get_type_name(), MSG, UVM_MEDIUM)

//define: ND_CHECK_FIELD
//Multi-line define that compares a transaction field and reports
//an error on mismatch. Demonstrates a multi-line macro with
//hex literal and begin/end block.
`define ND_CHECK_FIELD(FIELD, EXP) \
  begin \
    if (FIELD !== EXP) begin \
      `uvm_error(get_type_name(), \
        $sformatf("Field mismatch: got 0x%0h, expected 0x%0h", \
                  FIELD, EXP)) \
    end \
  end

//Package: nd_example_pkg
//Example package demonstrating correct NaturalDocs documentation.
//This package contains properly documented classes, functions, tasks,
//and constraints that comply with ND coding standards.
package nd_example_pkg;

  // Import UVM
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  //Group: Type Definitions

  //enum: state_e
  //State machine enumeration type for agent states
  typedef enum {
    IDLE_t, /// IDLE state
    ACTIVE_t, /// ACTIVE state
    WAIT_t, /// Wait state
    DONE_t /// Done state
  } state_e;

  //Variable: addr_t
  //Address type for memory operations
  typedef logic [31:0] addr_t;

  //Variable: data_t
  //Data type for transactions
  typedef logic [63:0] data_t;

  //Struct: ctrl_fields_t
  //Packed struct holding transaction control fields
  typedef struct packed {
    logic [3:0] burst_len; /// burst length in beats
    logic [2:0] prot; /// protection type
    logic       lock; /// lock signal
  } ctrl_fields_t;

  //Union: data_overlay_t
  //Packed union allowing raw or byte-level access to a 16-bit value
  typedef union packed {
    logic [15:0] raw;       /// Raw 16-bit word value
    logic [1:0][7:0] bytes; /// Byte-level slice access
  } data_overlay_t;

  `include "nd_config.sv"
  `include "nd_transaction.sv"
  `include "nd_sequence.sv"
  `include "nd_driver.sv"
  `include "nd_monitor.sv"

endpackage : nd_example_pkg
