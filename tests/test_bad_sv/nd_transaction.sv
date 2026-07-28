/*
 * Company: IC Verimeter
 * Author: Developer <dev@verimeter.com>
 * Description: Transaction class with missing coverage documentation
 */

`ifndef ND_TRANSACTION_SV
`define ND_TRANSACTION_SV

`define MAX_TRANSACTIONS 100

//Class: nd_transaction
//Transaction class description
class nd_transaction extends uvm_sequence_item;
  `uvm_object_utils(nd_transaction)

  rand bit [31:0] m_addr;

  covergroup trans_cg;
    cp_addr: coverpoint m_addr;
  endgroup : trans_cg

  function new(string name = "nd_transaction");
    super.new(name);
  endfunction : new
endclass : nd_transaction

`endif // ND_TRANSACTION_SV


