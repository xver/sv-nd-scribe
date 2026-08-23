/*
 * File: nd_param_driver.sv
 * Company: IC Verimeter
 * Author: Developer <dev@verimeter.com>
 * Description: Parameterized UVM driver with external virtual tasks and functions
 */

`ifndef ND_PARAM_DRIVER_SV
`define ND_PARAM_DRIVER_SV

class nd_param_driver #(
    type REQ_T = uvm_sequence_item,
    type RSP_T = REQ_T,
    int DATA_WIDTH = 32
) extends uvm_driver #(REQ_T, RSP_T);

  `uvm_component_param_utils(nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH))

  int m_packet_count;

  // Constructor with parameters
  function new(string name = "nd_param_driver", uvm_component parent = null);
    super.new(name, parent);
  endfunction : new

  // External virtual functions with parameters
  extern virtual function void configure(string cfg_name, int timeout_us = 1000);

  // External virtual functions without parameters
  extern virtual function void reset_stats();
  extern virtual function bit [DATA_WIDTH-1:0] get_status();

  // External virtual tasks with parameters
  extern virtual task send_packet(REQ_T req, output RSP_T rsp);
  external virtual task delay_cycles(int unsigned cycles, time step = 1ns);

  // External virtual tasks without parameters
  extern virtual task flush_pipeline();
  extern virtual task wait_for_idle();

endclass : nd_param_driver

function void nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::configure(string cfg_name, int timeout_us = 1000);
  m_packet_count = 0;
endfunction : configure

function void nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::reset_stats();
  m_packet_count = 0;
endfunction : reset_stats

function bit [DATA_WIDTH-1:0] nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::get_status();
  return m_packet_count[DATA_WIDTH-1:0];
endfunction : get_status

task nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::send_packet(REQ_T req, output RSP_T rsp);
  m_packet_count++;
endtask : send_packet

task nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::delay_cycles(int unsigned cycles, time step = 1ns);
  #(cycles * step);
endtask : delay_cycles

task nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::flush_pipeline();
  // Flush logic
endtask : flush_pipeline

task nd_param_driver#(REQ_T, RSP_T, DATA_WIDTH)::wait_for_idle();
  // Wait for idle logic
endtask : wait_for_idle

`endif // ND_PARAM_DRIVER_SV
