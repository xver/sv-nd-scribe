/******************************************************************************
 * File: nd_dut.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Dummy DUT module for demonstrating bindings and continuous assignments.
 *
 * Created: July 25, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

`ifndef ND_DUT_SV
`define ND_DUT_SV

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

  //Variable: dummy_wire
  //Wire used to demonstrate a continuous assignment.
  wire dummy_wire;
  //assign: dummy_wire
  //Continuous assignment example.
  assign dummy_wire = valid & ready;

endmodule : nd_dut

`endif // ND_DUT_SV
