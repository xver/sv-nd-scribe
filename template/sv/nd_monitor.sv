/******************************************************************************
 * File: nd_monitor.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Monitor component that observes pin activity and creates transactions.
 *              Implements protocol monitoring and coverage collection.
 *
 * Created: July 25, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

`ifndef ND_MONITOR_SV
`define ND_MONITOR_SV

  //Group: Monitor Classes

  //Class: nd_monitor
  //Monitor component that observes pin activity and creates transactions.
  //Implements protocol monitoring and coverage collection.
  class nd_monitor extends uvm_monitor;
    `uvm_component_utils(nd_monitor)

    //Group: Analysis Ports

    //Variable: m_analysis_port
    //Analysis port for broadcasting observed transactions
    uvm_analysis_port #(nd_transaction) m_analysis_port;

    //Group: Configuration

    //Variable: m_config
    //Configuration object reference
    nd_config m_config;

    //Group: Statistics

    //Variable: m_transaction_count
    //Total number of transactions observed
    int m_transaction_count;

    //Group: Methods

    //Function: new
    //Constructor for monitor component
    //
    //Parameters:
    //  name - Component name
    //  parent - Parent component
    extern function new(string name = "nd_monitor", uvm_component parent = null);

    //Function: build_phase
    //UVM build phase - create analysis port
    //
    //Parameters:
    //  phase - UVM phase object
    extern virtual function void build_phase(uvm_phase phase);

    //Task: run_phase
    //UVM run phase - main monitor execution
    //
    //Parameters:
    //  phase - UVM phase object
    extern virtual task run_phase(uvm_phase phase);

    //Task: collect_transaction
    //Collect a transaction from the interface
    //
    //Parameters:
    //  trans - Transaction object to fill with observed data
    extern virtual task collect_transaction(nd_transaction trans);

    //Function: report_phase
    //UVM report phase - print statistics
    //
    //Parameters:
    //  phase - UVM phase object
    extern virtual function void report_phase(uvm_phase phase);

  endclass : nd_monitor

  // Out-of-class implementation of new
  function nd_monitor::new(string name = "nd_monitor", uvm_component parent = null);
    super.new(name, parent);
    m_transaction_count = 0;
  endfunction : new

  // Out-of-class implementation of build_phase
  function void nd_monitor::build_phase(uvm_phase phase);
    super.build_phase(phase);
    m_analysis_port = new("m_analysis_port", this);
    if (!uvm_config_db#(nd_config)::get(this, "", "config", m_config)) begin
      `uvm_info(get_type_name(), "Using default configuration", UVM_MEDIUM)
      m_config = nd_config::type_id::create("m_config");
    end
  endfunction : build_phase

  // Out-of-class implementation of run_phase
  task nd_monitor::run_phase(uvm_phase phase);
    nd_transaction trans;

    `uvm_info(get_type_name(), "Monitor starting", UVM_MEDIUM)

    forever begin
      trans = nd_transaction::type_id::create("observed_trans");
      collect_transaction(trans);
      m_analysis_port.write(trans);
      m_transaction_count++;
    end
  endtask : run_phase

  // Out-of-class implementation of collect_transaction
  task nd_monitor::collect_transaction(nd_transaction trans);
    // Simulate collecting transaction data
    @(posedge /* clk signal would go here */);
    trans.m_timestamp = $time;
    trans.m_valid = 1;
  endtask : collect_transaction

  // Out-of-class implementation of report_phase
  function void nd_monitor::report_phase(uvm_phase phase);
    super.report_phase(phase);
    `uvm_info(get_type_name(),
              $sformatf("Monitor observed %0d transactions", m_transaction_count),
              UVM_MEDIUM)
  endfunction : report_phase

`endif // ND_MONITOR_SV
