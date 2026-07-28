/*
 * File: wrong_filename.sv
 * Company: IC Verimeter
 * Author: Developer <dev@verimeter.com>
 * Description: Test configuration class with missing documentation and style violations
 */

`ifndef ND_CONFIG_SV
`define ND_CONFIG_SV

class nd_config extends uvm_object;
  `uvm_object_utils(nd_config)

  int raw_timeout;

  function new(string name = "nd_config");
    super.new(name);
  endfunction : new

  extern function void do_print(uvm_printer printer);
endclass : nd_config

function void nd_config::do_print(uvm_printer printer);
  super.do_print(printer);
endfunction : do_print

`endif // ND_CONFIG_SV
