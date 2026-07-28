/******************************************************************************
 * File: nd_protocol_checker.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Checker for protocol compliance. Ensures valid is low during reset.
 *
 * Created: July 25, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

`ifndef ND_PROTOCOL_CHECKER_SV
`define ND_PROTOCOL_CHECKER_SV

//checker: nd_protocol_checker
//Checker for protocol compliance. Ensures valid is low during reset.
checker nd_protocol_checker(logic clk, logic rst_n, logic valid);
  //assertion: valid_reset_a
  //Asserts that valid is never high while reset is active (low).
  valid_reset_a: assert property (@(posedge clk) !rst_n |-> !valid);
endchecker : nd_protocol_checker

`endif // ND_PROTOCOL_CHECKER_SV
