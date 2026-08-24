/*
 * Company: IC Verimeter
 * Author: Developer <dev@verimeter.com>
 * Description: Test sequence class
 */

`ifndef ND_SEQUENCE_SV
`define ND_SEQUENCE_SV

//Class: nd_sequence
//Sequence class description





  
class nd_sequence extends uvm_sequence;
  `uvm_object_utils(nd_sequence)

  rand int m_len;

  constraint c_len {
    m_len > 0;
  }

  function new(string name = "nd_sequence");
    super.new(name);
  endfunction : new
endclass : nd_sequence

module seq_runner;
  initial begin
    $display("Running sequence");
  end
endmodule : seq_runner

`endif // ND_SEQUENCE_SV
