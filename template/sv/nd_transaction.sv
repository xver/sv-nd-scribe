/******************************************************************************
 * File: nd_transaction.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Base transaction class for protocol transactions.
 *              Contains address, data, and control fields.
 *
 * Created: July 25, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

`ifndef ND_TRANSACTION_SV
`define ND_TRANSACTION_SV

  //Group: Transaction Classes

  //Class: nd_transaction
  //Base transaction class for protocol transactions.
  //Contains address, data, and control fields.
  class nd_transaction extends uvm_sequence_item;
    `uvm_object_utils(nd_transaction)

    //Group: Transaction Fields

    //Variable: m_addr
    //Transaction address
    rand addr_t m_addr;

    //Variable: m_data
    //Transaction data payload
    rand data_t m_data;

    //Variable: m_write
    //Write enable (1=write, 0=read)
    rand bit m_write;

    //Variable: m_valid
    //Transaction valid signal
    bit m_valid;

    //Variable: m_timestamp
    //Transaction timestamp in simulation time
    time m_timestamp;

    //Group: Constraints

    //constraint: addr_range_c
    //Constrains address to valid memory range
    constraint addr_range_c {
      m_addr inside {[32'h1000:32'h1FFF]};
      m_addr[1:0] == 2'b00;  // Word aligned
    }

    //constraint: data_non_zero_c
    //Constrains data to non-zero for testing
    constraint data_non_zero_c {
      m_data != 0;
    }

    //Group: Methods

    //Function: new
    //Constructor for transaction object
    //
    //Parameters:
    //  name - Object name for UVM factory
    extern function new(string name = "nd_transaction");

    //Function: do_copy
    //UVM copy method override
    //
    //Parameters:
    //  rhs - Right-hand side object to copy from
    extern virtual function void do_copy(uvm_object rhs);

    //Function: do_compare
    //UVM compare method override
    //
    //Parameters:
    //  rhs - Right-hand side object to compare with
    //  comparer - UVM comparer object
    //
    //Returns:
    //  1 if objects match, 0 otherwise
    extern virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);

    //Function: convert2string
    //Convert transaction to string for printing
    //
    //Returns:
    //  String representation of transaction
    extern virtual function string convert2string();

  endclass : nd_transaction

  // Out-of-class implementation of new
  function nd_transaction::new(string name = "nd_transaction");
    super.new(name);
    m_valid = 0;
    m_timestamp = 0;
  endfunction : new

  // Out-of-class implementation of do_copy
  function void nd_transaction::do_copy(uvm_object rhs);
    nd_transaction rhs_trans;
    super.do_copy(rhs);
    if (!$cast(rhs_trans, rhs)) begin
      `uvm_fatal("CAST", "Failed to cast rhs object")
    end
    m_addr = rhs_trans.m_addr;
    m_data = rhs_trans.m_data;
    m_write = rhs_trans.m_write;
    m_valid = rhs_trans.m_valid;
    m_timestamp = rhs_trans.m_timestamp;
  endfunction : do_copy

  // Out-of-class implementation of do_compare
  function bit nd_transaction::do_compare(uvm_object rhs, uvm_comparer comparer);
    nd_transaction rhs_trans;
    if (!$cast(rhs_trans, rhs)) return 0;
    return (super.do_compare(rhs, comparer) &&
            (m_addr == rhs_trans.m_addr) &&
            (m_data == rhs_trans.m_data) &&
            (m_write == rhs_trans.m_write));
  endfunction : do_compare

  // Out-of-class implementation of convert2string
  function string nd_transaction::convert2string();
    return $sformatf("addr=0x%08h data=0x%016h write=%0b valid=%0b",
                     m_addr, m_data, m_write, m_valid);
  endfunction : convert2string

`endif // ND_TRANSACTION_SV
