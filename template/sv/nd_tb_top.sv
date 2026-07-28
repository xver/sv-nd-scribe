/******************************************************************************
 * File: nd_tb_top.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Top-level testbench module demonstrating correct NaturalDocs
 *              documentation for a complete UVM testbench environment.
 *
 * Created: July 27, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

`ifndef ND_TB_TOP_SV
`define ND_TB_TOP_SV

//Module: nd_tb_top
//Top-level testbench module for the UVM verification environment.
//Instantiates the DUT, connects the bus interface, and starts UVM.
module nd_tb_top;

  //Group: Clock and Reset

  //Variable: clk
  //Primary clock for the testbench and DUT
  logic clk;

  //Variable: rst_n
  //Active-low reset signal
  logic rst_n;

  //Group: Interface Instances

  //Variable: bus_if
  //Bus interface instance connecting the driver and monitor to the DUT
  nd_bus_if bus_if (.clk(clk), .rst_n(rst_n));

  //Group: DUT Instance

  //Variable: dut
  //Device Under Test instance
  nd_dut dut (
    .clk   (clk),
    .rst_n (rst_n),
    .valid (bus_if.valid),
    .ready (bus_if.ready)
  );

  //Group: Clock Generation

  //process: clk_gen_p
  //Clock generation process. Generates a 10 ns period clock.
  initial begin : clk_gen_p
    clk = 0;
    forever #5 clk = ~clk;
  end

  //Group: Reset Sequence

  //process: reset_p
  //Reset sequencing process. Asserts reset for 20 ns then de-asserts.
  initial begin : reset_p
    rst_n = 0;
    #20;
    rst_n = 1;
  end

  //Group: UVM Kickoff

  //process: uvm_start_p
  //Main UVM test kickoff process. Configures the virtual interface and runs the test.
  initial begin : uvm_start_p
    uvm_config_db #(virtual nd_bus_if)::set(null, "uvm_test_top.*", "vif", bus_if);
    run_test("nd_base_test");
  end

endmodule : nd_tb_top

`endif // ND_TB_TOP_SV
