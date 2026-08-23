/*
 * Company: IC Verimeter
 * Author: Jane Doe
 * Description: Bus interface with invalid author email and documentation violations
 */

`ifndef ND_BUS_IF_SV
`define ND_BUS_IF_SV

interface nd_bus_interface #(
  parameter int ADDR_WIDTH = 32,
  parameter int DATA_WIDTH = 32
) (
  input logic clk,
  input logic rst_n
);
  logic [ADDR_WIDTH-1:0] paddr;
  logic [DATA_WIDTH-1:0] pwdata;

  clocking manager_cb @(posedge clk);
    default input #1step output #2ns;
    output paddr;
    output pwdata;
  endclocking : manager_cb

  modport manager (
    clocking manager_cb,
    output   rst_n
  );
endinterface : nd_bus_interface

`endif // ND_BUS_IF_SV
