/******************************************************************************
 * File: nd_program.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Test program block demonstrating NaturalDocs documentation
 *              for a SystemVerilog program construct.
 *
 * Created: July 27, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

`ifndef ND_PROGRAM_SV
`define ND_PROGRAM_SV

//Program: nd_test_program
//Top-level test program block for the UVM verification environment.
//Provides the simulation entry point that runs the UVM test.
program nd_test_program (
  input logic clk,
  input logic rst_n
);

  //Group: Program Parameters

  //Variable: TIMEOUT_CYCLES
  //Maximum number of cycles before the watchdog fires
  localparam int TIMEOUT_CYCLES = 10_000;

  //Group: Test Entry Point

  //process: main_p
  //Main test entry process. Waits for reset release then starts the UVM run.
  initial begin : main_p
    // Wait for reset de-assertion
    @(posedge rst_n);
    @(posedge clk);

    // Run the UVM test
    run_test();

    // Guard against runaway simulations
    #(TIMEOUT_CYCLES * 10);
    $fatal(1, "[nd_test_program] Simulation timed out after %0d cycles", TIMEOUT_CYCLES);
  end

endprogram : nd_test_program

`endif // ND_PROGRAM_SV
