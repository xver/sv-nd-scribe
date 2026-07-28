/******************************************************************************
 * File: nd_driver.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Driver component that converts transactions to pin wiggles.
 *              Implements the UVM driver interface for the protocol.
 *
 * Created: July 25, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

`ifndef ND_DRIVER_SV
`define ND_DRIVER_SV

  //Group: Driver Classes

  //Class: nd_driver
  //Driver component that converts transactions to pin wiggles.
  //Implements the UVM driver interface for the protocol.
  class nd_driver extends uvm_driver #(nd_transaction);
    `uvm_component_utils(nd_driver)

    //Group: Configuration

    //Variable: m_config
    //Configuration object reference
    nd_config m_config;

    //Group: Internal State

    //Variable: m_current_state
    //Current state of the driver FSM
    state_e m_current_state;

    //Variable: m_cycle_count
    //Cycle counter for timing
    int m_cycle_count;

    //Group: Methods

    //Function: new
    //Constructor for driver component
    //
    //Parameters:
    //  name - Component name
    //  parent - Parent component
    extern function new(string name = "nd_driver", uvm_component parent = null);

    //Function: build_phase
    //UVM build phase - get configuration
    //
    //Parameters:
    //  phase - UVM phase object
    extern virtual function void build_phase(uvm_phase phase);

    //Task: run_phase
    //UVM run phase - main driver execution
    //
    //Parameters:
    //  phase - UVM phase object
    extern virtual task run_phase(uvm_phase phase);

    //Task: drive_transaction
    //Drive a single transaction on the interface
    //
    //Parameters:
    //  trans - Transaction to drive
    extern virtual task drive_transaction(nd_transaction trans);

    //Task: reset_driver
    //Reset the driver state machine and cycle counter to initial values
    extern task reset_driver();

  endclass : nd_driver

  // Out-of-class implementation of new
  function nd_driver::new(string name = "nd_driver", uvm_component parent = null);
    super.new(name, parent);
    m_current_state = IDLE_t;
    m_cycle_count = 0;
  endfunction : new

  // Out-of-class implementation of build_phase
  function void nd_driver::build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(nd_config)::get(this, "", "config", m_config)) begin
      `uvm_info(get_type_name(), "Using default configuration", UVM_MEDIUM)
      m_config = nd_config::type_id::create("m_config");
    end
  endfunction : build_phase

  // Out-of-class implementation of run_phase
  task nd_driver::run_phase(uvm_phase phase);
    nd_transaction trans;

    `uvm_info(get_type_name(), "Driver starting", UVM_MEDIUM)

    forever begin
      seq_item_port.get_next_item(trans);
      drive_transaction(trans);
      seq_item_port.item_done();
    end
  endtask : run_phase

  // Out-of-class implementation of drive_transaction
  task nd_driver::drive_transaction(nd_transaction trans);
    `uvm_info(get_type_name(),
              $sformatf("Driving transaction: %s", trans.convert2string()),
              UVM_HIGH)

    m_current_state = ACTIVE_t;

    // Simulate driving the transaction
    repeat (trans.m_write ? 1 : 2) @(posedge /* clk signal would go here */);

    m_cycle_count++;
    m_current_state = IDLE_t;
  endtask : drive_transaction

  // Out-of-class implementation of reset_driver
  task nd_driver::reset_driver();
    m_current_state = IDLE_t;
    m_cycle_count = 0;
  endtask : reset_driver

`endif // ND_DRIVER_SV
