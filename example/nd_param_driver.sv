/******************************************************************************
 * File:        nd_param_driver.sv
 *
 * Company:     IC Verimeter
 *
 * Author:      Developer <dev@verimeter.com>
 *
 * Description: Parameterized UVM driver demonstrating external virtual tasks
 *              and functions with and without parameters.
 *
 * Created:     August 23, 2026 (Developer)
 *
 * Updated:     August 23, 2026 (Developer)
 *
 * Copyright (c) 2026 IC Verimeter. All rights reserved.
 * Licensed under the MIT License. See LICENSE in the project root for details.
 ******************************************************************************/

`ifndef ND_PARAM_DRIVER_SV
`define ND_PARAM_DRIVER_SV

// Class: nd_param_driver
// Parameterized driver class handling request and response transactions.
class nd_param_driver #(
    type REQ_T = uvm_sequence_item,
    type RSP_T = REQ_T,
    int DATA_WIDTH = 32
) extends uvm_driver #(REQ_T, RSP_T);

  `uvm_component_param_utils(nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH))

  // Variable: m_packet_count
  // Total number of packets processed by this driver instance.
  int m_packet_count;

  // Group: Constructors

  // Function: new
  // Creates and initializes the parameterized driver instance.
  //
  // Parameters:
  //   name - Component name in the UVM hierarchy.
  //   parent - Parent UVM component.
  function new(string name = "nd_param_driver", uvm_component parent = null);
    super.new(name, parent);
    m_packet_count = 0;
  endfunction : new

  // Group: Configuration & Status Methods

  // Function: configure
  // Configures the driver parameters and timeout.
  //
  // Parameters:
  //   cfg_name - Name of configuration object.
  //   timeout_us - Timeout threshold in microseconds.
  extern virtual function void configure(string cfg_name, int timeout_us = 1000);

  // Function: reset_stats
  // Resets driver internal counters and statistics.
  extern virtual function void reset_stats();

  // Function: get_status
  // Returns the current status register mask.
  extern virtual function bit [DATA_WIDTH-1:0] get_status();

  // Group: Transaction Execution Methods

  // Task: send_packet
  // Drives a sequence item request and collects the response.
  //
  // Parameters:
  //   req - Sequence item request to transmit.
  //   rsp - Sequence item response returned from DUT.
  extern virtual task send_packet(REQ_T req, output RSP_T rsp);

  // Task: delay_cycles
  // Waits for a specified number of clock step cycles.
  //
  // Parameters:
  //   cycles - Number of clock cycles to delay.
  //   step - Duration of each step unit.
  external virtual task delay_cycles(int unsigned cycles, time step = 1ns);

  // Task: flush_pipeline
  // Flushes pending transactions from the driver pipeline.
  extern virtual task flush_pipeline();

  // Task: wait_for_idle
  // Blocks until the driver has completed all active transactions.
  extern virtual task wait_for_idle();

endclass : nd_param_driver

// Function: configure
// Implementation of configure method.
//
// Parameters:
//   cfg_name - Name of configuration object.
//   timeout_us - Timeout threshold in microseconds.
function void nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::configure(string cfg_name, int timeout_us = 1000);
  `uvm_info(get_type_name(), $sformatf("Configuring driver with %s (timeout: %0d us)", cfg_name, timeout_us), UVM_LOW)
endfunction : configure

// Function: reset_stats
// Implementation of reset_stats method.
function void nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::reset_stats();
  m_packet_count = 0;
endfunction : reset_stats

// Function: get_status
// Implementation of get_status method.
function bit [DATA_WIDTH-1:0] nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::get_status();
  return m_packet_count[DATA_WIDTH-1:0];
endfunction : get_status

// Task: send_packet
// Implementation of send_packet task.
//
// Parameters:
//   req - Sequence item request to transmit.
//   rsp - Sequence item response returned from DUT.
task nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::send_packet(REQ_T req, output RSP_T rsp);
  m_packet_count++;
  #10ns;
endtask : send_packet

// Task: delay_cycles
// Implementation of delay_cycles task.
//
// Parameters:
//   cycles - Number of clock cycles to delay.
//   step - Duration of each step unit.
task nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::delay_cycles(int unsigned cycles, time step = 1ns);
  #(cycles * step);
endtask : delay_cycles

// Task: flush_pipeline
// Implementation of flush_pipeline task.
task nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::flush_pipeline();
  #5ns;
endtask : flush_pipeline

// Task: wait_for_idle
// Implementation of wait_for_idle task.
task nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::wait_for_idle();
  #1ns;
endtask : wait_for_idle

`endif // ND_PARAM_DRIVER_SV
