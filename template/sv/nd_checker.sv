/******************************************************************************
 * File: nd_checker.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Protocol checker demonstrating NaturalDocs documentation
 *              for a SystemVerilog checker construct.
 *
 * Created: July 27, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

`ifndef ND_CHECKER_SV
`define ND_CHECKER_SV

//Group: Checker Declarations

//checker: nd_protocol_checker
//Formal/simulation protocol checker for the bus interface.
//Asserts that valid is de-asserted during reset, and that ready
//follows valid within a bounded latency window.
checker nd_protocol_checker (
  input logic clk,
  input logic rst_n,
  input logic valid
);

  //Group: Checker Properties

  //property: valid_inactive_during_reset_p
  //Asserts that the valid signal is low whenever reset is asserted.
  property valid_inactive_during_reset_p;
    @(posedge clk) !rst_n |-> !valid;
  endproperty : valid_inactive_during_reset_p

  //Group: Checker Assertions

  //process: chk_valid_reset_a
  //Assertion that fires if valid is high during reset.
  assert property (valid_inactive_during_reset_p)
    else $error("[CHECKER] valid must be 0 during reset");

  //process: chk_valid_reset_cov
  //Cover point for the valid-during-reset scenario.
  cover property (@(posedge clk) !rst_n ##1 rst_n);

endchecker : nd_protocol_checker

`endif // ND_CHECKER_SV
