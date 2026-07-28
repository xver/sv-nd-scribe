/******************************************************************************
 * File: example.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Example SystemVerilog file with correct NaturalDocs documentation
 *              This file demonstrates proper documentation for all constructs
 *              and passes all naturaldocs_lint.py checks.
 *
 * Created: October 2, 2025 (vbesyakov@btadesignservices.com)
 *
 * Updated: June 13, 2026 (icshunt.help@gmail.com)
 ******************************************************************************/

`ifndef EXAMPLE_SV
`define EXAMPLE_SV

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
    logic [15:0] raw;
    logic [1:0][7:0] bytes;
  } data_overlay_t;

  //Group: Configuration Classes

  //Class: nd_config
  //Configuration class for the verification environment.
  //Contains all configuration parameters for the testbench components.
  class nd_config extends uvm_object;
    `uvm_object_utils(nd_config)

    //Group: Configuration Parameters

    //Variable: NUM_LANES
    //Number of data lanes supported by the DUT
    parameter int NUM_LANES = 4;

    //Variable: DEFAULT_TIMEOUT
    //Default timeout value used when no override is provided
    localparam int DEFAULT_TIMEOUT = 5000;

    //Variable: m_num_transactions
    //Number of transactions to generate
    rand int m_num_transactions;

    //Variable: m_timeout_cycles
    //Timeout value in clock cycles
    rand int m_timeout_cycles;

    //Variable: m_enable_coverage
    //Enable functional coverage collection
    bit m_enable_coverage;

    //Variable: m_verbosity
    //UVM verbosity level for reporting
    uvm_verbosity m_verbosity;

    //Group: Constraints

    //constraint: num_transactions_c
    //Constrains number of transactions to reasonable range
    constraint num_transactions_c {
      m_num_transactions inside {[1:1000]};
      m_num_transactions > 0;
    }

    //constraint: timeout_cycles_c
    //Constrains timeout to prevent simulation hangs
    constraint timeout_cycles_c {
      m_timeout_cycles inside {[100:10000]};
      m_timeout_cycles > m_num_transactions;
    }

    //Group: Coverage

    //covergroup: config_cg
    //Covergroup that samples configuration parameter combinations
    covergroup config_cg;
    // coverpoint: cp_num_trans
    //   Coverpoint that samples the number of transactions
      cp_num_trans: coverpoint m_num_transactions {
        bins low   = {[1:100]};
        bins mid   = {[101:500]};
        bins high  = {[501:1000]};
      }

      // coverpoint: cp_coverage_en
      //   Coverpoint that samples the coverage enable flag
      cp_coverage_en: coverpoint m_enable_coverage;
    endgroup : config_cg

    //Group: Methods

    //Function: new
    //Constructor for configuration object
    //
    //Parameters:
    //  name - Object name for UVM factory
    function new(string name = "nd_config");
      super.new(name);
      m_enable_coverage = 1;
      m_verbosity = UVM_MEDIUM;
      config_cg = new();
    endfunction : new

    //Function: do_print
    //UVM print method override
    //
    //Parameters:
    //  printer - UVM printer object
    virtual function void do_print(uvm_printer printer);
      super.do_print(printer);
      printer.print_field_int("m_num_transactions", m_num_transactions, $bits(m_num_transactions));
      printer.print_field_int("m_timeout_cycles", m_timeout_cycles, $bits(m_timeout_cycles));
      printer.print_field_int("m_enable_coverage", m_enable_coverage, 1);
    endfunction : do_print

    //Function: sample_config
    //Trigger covergroup sampling after configuration is finalized
    extern function void sample_config();

  endclass : nd_config

  //Function: sample_config
  //Out-of-class implementation of the extern prototype
  function void nd_config::sample_config();
    config_cg.sample();
  endfunction : sample_config

  //Group: Transaction Classes

  //Class: nd_transaction
  //Base transaction class for protocol transactions.
  //Contains address, data, and control fields.
  class nd_transaction extends uvm_sequence_item;
    `uvm_object_utils(nd_transaction)

    //Group: Transaction Fields

    //Variable: m_addr
    //Transaction address
    rand addr_t m_addr;

    //Variable: m_data
    //Transaction data payload
    rand data_t m_data;

    //Variable: m_write
    //Write enable (1=write, 0=read)
    rand bit m_write;

    //Variable: m_valid
    //Transaction valid signal
    bit m_valid;

    //Variable: m_timestamp
    //Transaction timestamp in simulation time
    time m_timestamp;

    //Group: Constraints

    //constraint: addr_range_c
    //Constrains address to valid memory range
    constraint addr_range_c {
      m_addr inside {[32'h1000:32'h1FFF]};
      m_addr[1:0] == 2'b00;  // Word aligned
    }

    //constraint: data_non_zero_c
    //Constrains data to non-zero for testing
    constraint data_non_zero_c {
      m_data != 0;
    }

    //Group: Methods

    //Function: new
    //Constructor for transaction object
    //
    //Parameters:
    //  name - Object name for UVM factory
    function new(string name = "nd_transaction");
      super.new(name);
      m_valid = 0;
      m_timestamp = 0;
    endfunction : new

    //Function: do_copy
    //UVM copy method override
    //
    //Parameters:
    //  rhs - Right-hand side object to copy from
    virtual function void do_copy(uvm_object rhs);
      nd_transaction rhs_trans;
      super.do_copy(rhs);
      if (!$cast(rhs_trans, rhs)) begin
        `uvm_fatal("CAST", "Failed to cast rhs object")
      end
      m_addr = rhs_trans.m_addr;
      m_data = rhs_trans.m_data;
      m_write = rhs_trans.m_write;
      m_valid = rhs_trans.m_valid;
      m_timestamp = rhs_trans.m_timestamp;
    endfunction : do_copy

    //Function: do_compare
    //UVM compare method override
    //
    //Parameters:
    //  rhs - Right-hand side object to compare with
    //  comparer - UVM comparer object
    //
    //Returns:
    //  1 if objects match, 0 otherwise
    virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
      nd_transaction rhs_trans;
      if (!$cast(rhs_trans, rhs)) return 0;
      return (super.do_compare(rhs, comparer) &&
              (m_addr == rhs_trans.m_addr) &&
              (m_data == rhs_trans.m_data) &&
              (m_write == rhs_trans.m_write));
    endfunction : do_compare

    //Function: convert2string
    //Convert transaction to string for printing
    //
    //Returns:
    //  String representation of transaction
    virtual function string convert2string();
      return $sformatf("addr=0x%08h data=0x%016h write=%0b valid=%0b",
                       m_addr, m_data, m_write, m_valid);
    endfunction : convert2string

  endclass : nd_transaction

  //Group: Sequence Classes

  //Class: nd_sequence
  //Base sequence class for generating transactions.
  //Generates a configurable number of random transactions.
  class nd_sequence extends uvm_sequence #(nd_transaction);
    `uvm_object_utils(nd_sequence)

    //Group: Sequence Parameters

    //Variable: m_num_items
    //Number of transactions to generate
    rand int m_num_items;

    //Group: Constraints

    //constraint: num_items_range_c
    //Constrains sequence length to reasonable range
    constraint num_items_range_c {
      m_num_items inside {[1:100]};
    }

    //Group: Methods

    //Function: new
    //Constructor for sequence object
    //
    //Parameters:
    //  name - Object name for UVM factory
    function new(string name = "nd_sequence");
      super.new(name);
      m_num_items = 10;
    endfunction : new

    //Task: body
    //Main sequence body that generates transactions.
    //Creates and randomizes the specified number of transactions.
    virtual task body();
      nd_transaction trans;

      `uvm_info(get_type_name(),
                $sformatf("Starting sequence with %0d transactions", m_num_items),
                UVM_MEDIUM)

      for (int i = 0; i < m_num_items; i++) begin
        trans = nd_transaction::type_id::create($sformatf("trans_%0d", i));
        start_item(trans);
        if (!trans.randomize()) begin
          `uvm_error(get_type_name(), "Failed to randomize transaction")
        end
        finish_item(trans);
      end

      `uvm_info(get_type_name(), "Sequence completed", UVM_MEDIUM)
    endtask : body

  endclass : nd_sequence

  //Group: Driver Classes

  //Class: nd_driver
  //Driver component that converts transactions to pin wiggles.
  //Implements the UVM driver interface for the protocol.
  class nd_driver extends uvm_driver #(nd_transaction);
    `uvm_component_utils(nd_driver)

    //Group: Configuration

    //Variable: m_config
    //Configuration object reference
    nd_config m_config;

    //Group: Internal State

    //Variable: m_current_state
    //Current state of the driver FSM
    state_t m_current_state;

    //Variable: m_cycle_count
    //Cycle counter for timing
    int m_cycle_count;

    //Group: Methods

    //Function: new
    //Constructor for driver component
    //
    //Parameters:
    //  name - Component name
    //  parent - Parent component
    function new(string name = "nd_driver", uvm_component parent = null);
      super.new(name, parent);
      m_current_state = IDLE_t;
      m_cycle_count = 0;
    endfunction : new

    //Function: build_phase
    //UVM build phase - get configuration
    //
    //Parameters:
    //  phase - UVM phase object
    virtual function void build_phase(uvm_phase phase);
      super.build_phase(phase);
      if (!uvm_config_db#(nd_config)::get(this, "", "config", m_config)) begin
        `uvm_info(get_type_name(), "Using default configuration", UVM_MEDIUM)
        m_config = nd_config::type_id::create("m_config");
      end
    endfunction : build_phase

    //Function: run_phase
    //UVM run phase - main driver execution
    //
    //Parameters:
    //  phase - UVM phase object
    virtual task run_phase(uvm_phase phase);
      nd_transaction trans;

      `uvm_info(get_type_name(), "Driver starting", UVM_MEDIUM)

      forever begin
        seq_item_port.get_next_item(trans);
        drive_transaction(trans);
        seq_item_port.item_done();
      end
    endtask : run_phase

    //Function: drive_transaction
    //Drive a single transaction on the interface
    //
    //Parameters:
    //  trans - Transaction to drive
    virtual task drive_transaction(nd_transaction trans);
      `uvm_info(get_type_name(),
                $sformatf("Driving transaction: %s", trans.convert2string()),
                UVM_HIGH)

      m_current_state = ACTIVE_t;

      // Simulate driving the transaction
      repeat (trans.m_write ? 1 : 2) @(posedge /* clk signal would go here */);

      m_cycle_count++;
      m_current_state = IDLE_t;
    endtask : drive_transaction

    //Function: reset_driver
    //Reset the driver state machine and cycle counter to initial values
    extern task reset_driver();

  endclass : nd_driver

  //Function: reset_driver
  //Out-of-class implementation of the extern task prototype
  task nd_driver::reset_driver();
    m_current_state = IDLE_t;
    m_cycle_count = 0;
  endtask : reset_driver

  //Group: Monitor Classes

  //Class: nd_monitor
  //Monitor component that observes pin activity and creates transactions.
  //Implements protocol monitoring and coverage collection.
  class nd_monitor extends uvm_monitor;
    `uvm_component_utils(nd_monitor)

    //Group: Analysis Ports

    //Variable: m_analysis_port
    //Analysis port for broadcasting observed transactions
    uvm_analysis_port #(nd_transaction) m_analysis_port;

    //Group: Configuration

    //Variable: m_config
    //Configuration object reference
    nd_config m_config;

    //Group: Statistics

    //Variable: m_transaction_count
    //Total number of transactions observed
    int m_transaction_count;

    //Group: Methods

    //Function: new
    //Constructor for monitor component
    //
    //Parameters:
    //  name - Component name
    //  parent - Parent component
    function new(string name = "nd_monitor", uvm_component parent = null);
      super.new(name, parent);
      m_transaction_count = 0;
    endfunction : new

    //Function: build_phase
    //UVM build phase - create analysis port
    //
    //Parameters:
    //  phase - UVM phase object
    virtual function void build_phase(uvm_phase phase);
      super.build_phase(phase);
      m_analysis_port = new("m_analysis_port", this);
      if (!uvm_config_db#(nd_config)::get(this, "", "config", m_config)) begin
        `uvm_info(get_type_name(), "Using default configuration", UVM_MEDIUM)
        m_config = nd_config::type_id::create("m_config");
      end
    endfunction : build_phase

    //Function: run_phase
    //UVM run phase - main monitor execution
    //
    //Parameters:
    //  phase - UVM phase object
    virtual task run_phase(uvm_phase phase);
      nd_transaction trans;

      `uvm_info(get_type_name(), "Monitor starting", UVM_MEDIUM)

      forever begin
        trans = nd_transaction::type_id::create("observed_trans");
        collect_transaction(trans);
        m_analysis_port.write(trans);
        m_transaction_count++;
      end
    endtask : run_phase

    //Function: collect_transaction
    //Collect a transaction from the interface
    //
    //Parameters:
    //  trans - Transaction object to fill with observed data
    virtual task collect_transaction(nd_transaction trans);
      // Simulate collecting transaction data
      @(posedge /* clk signal would go here */);
      trans.m_timestamp = $time;
      trans.m_valid = 1;
    endtask : collect_transaction

    //Function: report_phase
    //UVM report phase - print statistics
    //
    //Parameters:
    //  phase - UVM phase object
    virtual function void report_phase(uvm_phase phase);
      super.report_phase(phase);
      `uvm_info(get_type_name(),
                $sformatf("Monitor observed %0d transactions", m_transaction_count),
                UVM_MEDIUM)
    endfunction : report_phase

  endclass : nd_monitor

endpackage : nd_example_pkg

// ============================================================================
// Module and Interface examples (outside the package)
// ============================================================================

//Interface: nd_bus_if
//Simple bus interface used by the driver and monitor to communicate
//with the DUT. Contains clock, reset, address, data, and control signals.
interface nd_bus_if (input logic clk, input logic rst_n);

  //Variable: addr
  //Address bus for memory-mapped transactions
  logic [31:0] addr;

  //Variable: data
  //Bidirectional data bus
  logic [63:0] data;

  //Variable: wr_en
  //Write enable signal (1 = write, 0 = read)
  logic        wr_en;

  //Variable: valid
  //Transaction valid handshake signal
  logic        valid;

  //Variable: ready
  //Subordinate ready handshake signal
  logic        ready;

  modport manager     (output addr, data, wr_en, valid, input ready);
  modport subordinate (input  addr, data, wr_en, valid, output ready);

endinterface : nd_bus_if

//Module: nd_top_wrapper
//Top-level wrapper module that instantiates the bus interface and
//connects the DUT to the verification environment.
module nd_top_wrapper;

  //Variable: clk
  //System clock generated by the testbench
  logic clk;

  //Variable: rst_n
  //Active-low reset signal
  logic rst_n;

  //Variable: bus_if
  //Bus interface instance connecting DUT to the verification environment
  nd_bus_if bus_if (.clk(clk), .rst_n(rst_n));

  //process: clk_gen
  //Generates the system clock.
  initial begin : clk_gen
    clk = 0;
    forever #5 clk = ~clk;
  end

  //process: rst_gen
  //Generates the active-low reset signal.
  initial begin : rst_gen
    rst_n = 0;
    #20 rst_n = 1;
  end

endmodule : nd_top_wrapper

// ============================================================================
// Additional Examples (Checkers, Assertions, Processes, Assignments, Programs)
// ============================================================================

//checker: nd_protocol_checker
//Checker for protocol compliance. Ensures valid is low during reset.
checker nd_protocol_checker(logic clk, logic rst_n, logic valid);
  //assertion: valid_reset_a
  //Asserts that valid is never high while reset is active (low).
  valid_reset_a: assert property (@(posedge clk) !rst_n |-> !valid);
endchecker : nd_protocol_checker

//Module: nd_dut
//Dummy DUT module for demonstrating bindings and continuous assignments.
module nd_dut (
  input logic clk,
  input logic rst_n,
  input logic valid,
  output logic ready
);

  //Variable: internal_ready
  //Internal ready signal
  logic internal_ready;

  //process: ready_logic_p
  //Combinational process to drive internal ready
  always_comb begin : ready_logic_p
    internal_ready = rst_n ? 1'b1 : 1'b0;
  end

  //process: ready_ff_p
  //Sequential process for ready output
  always_ff @(posedge clk or negedge rst_n) begin : ready_ff_p
    if (!rst_n) begin
      ready <= 1'b0;
    end else begin
      ready <= internal_ready;
    end
  end

  wire dummy_wire;
  //assign: dummy_wire
  //Continuous assignment example.
  assign dummy_wire = valid & ready;

endmodule : nd_dut

//bind: chk_inst
//Binds the protocol checker to the DUT instances.
bind nd_dut nd_protocol_checker chk_inst (
  .clk(clk),
  .rst_n(rst_n),
  .valid(valid)
);

//program: nd_test_program
//Test program block for driving stimulus.
program nd_test_program(input logic clk, output logic rst_n, output logic valid);
  
  //process: stimulus_p
  //Initial block process for test stimulus
  initial begin : stimulus_p
    rst_n = 0;
    valid = 0;
    #10 rst_n = 1;
    #10 valid = 1;
    #10 valid = 0;
  end

endprogram : nd_test_program

`endif // EXAMPLE_SV

