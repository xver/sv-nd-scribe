/******************************************************************************
 * File: nd_bind.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Binds the protocol checker to the DUT instances.
 *
 * Created: July 25, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

`ifndef ND_BIND_SV
`define ND_BIND_SV

//bind: chk_inst
//Binds the protocol checker to the DUT instances.
bind nd_dut nd_protocol_checker chk_inst (
  .clk(clk),
  .rst_n(rst_n),
  .valid(valid)
);

`endif // ND_BIND_SV
