/******************************************************************************
 * File: nd_sequence.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Base sequence class for generating transactions.
 *              Generates a configurable number of random transactions.
 *
 * Created: July 25, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

`ifndef ND_SEQUENCE_SV
`define ND_SEQUENCE_SV

  //Group: Sequence Classes

  //Class: nd_sequence
  //Base sequence class for generating transactions.
  //Generates a configurable number of random transactions.
  class nd_sequence extends uvm_sequence #(nd_transaction);
    `uvm_object_utils(nd_sequence)

    //Group: Sequence Parameters

    //Variable: m_num_items
    //Number of transactions to generate
    rand int m_num_items;

    //Group: Constraints

    //constraint: num_items_range_c
    //Constrains sequence length to reasonable range
    constraint num_items_range_c {
      m_num_items inside {[1:100]};
    }

    //Group: Methods

    //Function: new
    //Constructor for sequence object
    //
    //Parameters:
    //  name - Object name for UVM factory
    extern function new(string name = "nd_sequence");

    //Task: body
    //Main sequence body that generates transactions.
    //Creates and randomizes the specified number of transactions.
    extern virtual task body();

  endclass : nd_sequence

  // Out-of-class implementation of new
  function nd_sequence::new(string name = "nd_sequence");
    super.new(name);
    m_num_items = 10;
  endfunction : new

  // Out-of-class implementation of body
  task nd_sequence::body();
    nd_transaction trans;

    `uvm_info(get_type_name(),
              $sformatf("Starting sequence with %0d transactions", m_num_items),
              UVM_MEDIUM)

    for (int i = 0; i < m_num_items; i++) begin
      trans = nd_transaction::type_id::create($sformatf("trans_%0d", i));
      start_item(trans);
      if (!trans.randomize()) begin
        `uvm_error(get_type_name(), "Failed to randomize transaction")
      end
      finish_item(trans);
    end

    `uvm_info(get_type_name(), "Sequence completed", UVM_MEDIUM)
  endtask : body

`endif // ND_SEQUENCE_SV
