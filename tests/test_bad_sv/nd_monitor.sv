/*
 * Company: IC Verimeter
 * Author: Developer <dev@verimeter.com>
 * Description: Test monitor component
 */

`ifndef ND_MONITOR_SV
`define ND_MONITOR_SV


class nd_monitor extends uvm_monitor;
  `uvm_component_utils(nd_monitor)

  //Group:InvalidHeader

  function new(string name = "nd_monitor", uvm_component parent = null);
    super.new(name, parent);
  endfunction : new
endclass : nd_monitor

`endif // ND_MONITOR_SV
