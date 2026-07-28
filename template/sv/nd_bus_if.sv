/******************************************************************************
 * File: nd_bus_if.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Simple bus interface used by the driver and monitor to communicate
 *              with the DUT. Contains clock, reset, address, data, and control signals.
 *
 * Created: July 25, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

`ifndef ND_BUS_IF_SV
`define ND_BUS_IF_SV

//Interface: nd_bus_if
//Simple bus interface used by the driver and monitor to communicate
//with the DUT. Contains clock, reset, address, data, and control signals.
interface nd_bus_if (input logic clk, input logic rst_n);

  //Variable: addr
  //Address bus for memory-mapped transactions
  logic [31:0] addr;

  //Variable: data
  //Bidirectional data bus
  logic [63:0] data;

  //Variable: wr_en
  //Write enable signal (1 = write, 0 = read)
  logic        wr_en;

  //Variable: valid
  //Transaction valid handshake signal
  logic        valid;

  //Variable: ready
  //Subordinate ready handshake signal
  logic        ready;

  //Clocking: manager_cb
  //Manager driver clocking block synchronized to posedge clk
  clocking manager_cb @(posedge clk);
    default input #1step output #1step;
    output addr, data, wr_en, valid;
    input  ready;
  endclocking : manager_cb

  //Clocking: subordinate_cb
  //Subordinate monitor clocking block synchronized to posedge clk
  clocking subordinate_cb @(posedge clk);
    default input #1step output #1step;
    input  addr, data, wr_en, valid;
    output ready;
  endclocking : subordinate_cb

  //Modport: manager
  //Manager driver interface modport using manager_cb
  modport manager (clocking manager_cb, input rst_n);

  //Modport: subordinate
  //Subordinate monitor interface modport using subordinate_cb
  modport subordinate (clocking subordinate_cb, input rst_n);

endinterface : nd_bus_if

`endif // ND_BUS_IF_SV
