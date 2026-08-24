/*
 * File:        nd_driver.sv
 * Company: IC Verimeter
 * Author: Developer <dev@verimeter.com>
 * Description: Test driver component
 */

`ifndef ND_DRIVER_SV
`define ND_DRIVER_SV

// Class: nd_driver
// Driver class description

class nd_driver extends uvm_driver;
  `uvm_component_utils(nd_driver)


  function new(string name = "nd_driver", uvm_component parent = null);
    super.new(name, parent);
  endfunction : new

  
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
  endfunction : build_phase
endclass : nd_driver

`endif // ND_DRIVER_SV
