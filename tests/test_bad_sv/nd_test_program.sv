/*
 * Company: IC Verimeter
 * Author: Developer <dev@verimeter.com>
 * Description: Test program block
 */

`ifndef ND_TEST_PROGRAM_SV
`define ND_TEST_PROGRAM_SV

program nd_test_program(input logic clk);
  initial begin    
    $display("Test program started");
  end
endprogram : nd_test_program

`endif // ND_TEST_PROGRAM_SV
