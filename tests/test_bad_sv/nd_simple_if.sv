/*
 * File: nd_simple_if.sv
 * Company: IC Verimeter
 * Author: Developer <dev@verimeter.com>
 * Description: Non-parameterized interface without port list
 */

`ifndef ND_SIMPLE_IF_SV
`define ND_SIMPLE_IF_SV

interface nd_simple_if;
  logic clk;
  logic rst_n;
  logic [7:0] data;
endinterface : nd_simple_if

`endif // ND_SIMPLE_IF_SV
