/*
 * Company: IC Verimeter
 * Author: Developer <dev@verimeter.com>
 * Description: Protocol checker block
 */

`ifndef ND_PROTOCOL_CHECKER_SV
`define ND_PROTOCOL_CHECKER_SV

checker nd_protocol_checker (
  input logic clk,
  input logic rst_n,
  input logic valid
);

  property p_valid;
    @(posedge clk) disable iff (!rst_n) valid |=> !valid;
  endproperty

  assert property (p_valid);

endchecker : nd_protocol_checker

`endif // ND_PROTOCOL_CHECKER_SV
