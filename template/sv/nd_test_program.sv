/******************************************************************************
 * File: nd_test_program.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Test program block for driving stimulus.
 *
 * Created: July 25, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

`ifndef ND_TEST_PROGRAM_SV
`define ND_TEST_PROGRAM_SV

//program: nd_test_program
//Test program block for driving stimulus.
program nd_test_program(input logic clk, output logic rst_n, output logic valid);

  //process: stimulus_p
  //Initial block process for test stimulus
  initial begin : stimulus_p
    rst_n = 0;
    valid = 0;
    #10 rst_n = 1;
    #10 valid = 1;
    #10 valid = 0;
  end

endprogram : nd_test_program

`endif // ND_TEST_PROGRAM_SV
