/*
 * File:        nd_dut.sv
 * Company: IC Verimeter
 * Author: Developer <dev@verimeter.com>
 * Description: Test DUT module
 */

`ifndef ND_DUT_SV
`define ND_DUT_SV


module nd_dut #(
  parameter int DATA_WIDTH = 32,
  parameter int ADDR_WIDTH = 16
) (
  input  logic                   clk,
  input  logic                   rst_n,
  input  logic [ADDR_WIDTH-1:0]  addr,
  input  logic [DATA_WIDTH-1:0]  wdata,
  output logic [DATA_WIDTH-1:0]  rdata
);

  // Variable: dummy_wire
  // TODO: Add description for variable 'dummy_wire'
  wire dummy_wire;

endmodule : nd_dut

`endif // ND_DUT_SV
