/******************************************************************************
 * File: nd_config.sv
 *
 * Company: IC Verimeter
 *
 * Author: icshunt.help@gmail.com
 *
 * Description: Configuration class for the verification environment.
 *              Contains all configuration parameters for the testbench components.
 *
 * Created: July 25, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/

`ifndef ND_CONFIG_SV
`define ND_CONFIG_SV

  //Group: Configuration Classes

  //Class: nd_config
  //Configuration class for the verification environment.
  //Contains all configuration parameters for the testbench components.
  class nd_config extends uvm_object;
    `uvm_object_utils(nd_config)

    //Group: Configuration Parameters

    //Variable: NUM_LANES
    //Number of data lanes supported by the DUT
    parameter int NUM_LANES = 4;

    //Variable: DEFAULT_TIMEOUT
    //Default timeout value used when no override is provided
    localparam int DEFAULT_TIMEOUT = 5000;

    //Variable: m_num_transactions
    //Number of transactions to generate
    rand int m_num_transactions;

    //Variable: m_timeout_cycles
    //Timeout value in clock cycles
    rand int m_timeout_cycles;

    //Variable: m_enable_coverage
    //Enable functional coverage collection
    bit m_enable_coverage;

    //Variable: m_verbosity
    //UVM verbosity level for reporting
    uvm_verbosity m_verbosity;

    //Group: Constraints

    //constraint: num_transactions_c
    //Constrains number of transactions to reasonable range
    constraint num_transactions_c {
      m_num_transactions inside {[1:1000]};
      m_num_transactions > 0;
    }

    //constraint: timeout_cycles_c
    //Constrains timeout to prevent simulation hangs
    constraint timeout_cycles_c {
      m_timeout_cycles inside {[100:10000]};
      m_timeout_cycles > m_num_transactions;
    }

    //Group: Coverage

    //covergroup: config_cg
    //Covergroup that samples configuration parameter combinations
    covergroup config_cg;
    // coverpoint: cp_num_trans
    //   Coverpoint that samples the number of transactions
      cp_num_trans: coverpoint m_num_transactions {
        bins low   = {[1:100]};
        bins mid   = {[101:500]};
        bins high  = {[501:1000]};
      }

      // coverpoint: cp_coverage_en
      //   Coverpoint that samples the coverage enable flag
      cp_coverage_en: coverpoint m_enable_coverage;
    endgroup : config_cg

    //Group: Methods

    //Function: new
    //Constructor for configuration object
    //
    //Parameters:
    //  name - Object name for UVM factory
    extern function new(string name = "nd_config");

    //Function: do_print
    //UVM print method override
    //
    //Parameters:
    //  printer - UVM printer object
    extern virtual function void do_print(uvm_printer printer);

    //Function: sample_config
    //Trigger covergroup sampling after configuration is finalized
    extern function void sample_config();

  endclass : nd_config

  // Out-of-class implementation of new
  function nd_config::new(string name = "nd_config");
    super.new(name);
    m_enable_coverage = 1;
    m_verbosity = UVM_MEDIUM;
    config_cg = new();
  endfunction : new

  // Out-of-class implementation of do_print
  function void nd_config::do_print(uvm_printer printer);
    super.do_print(printer);
    printer.print_field_int("m_num_transactions", m_num_transactions, $bits(m_num_transactions));
    printer.print_field_int("m_timeout_cycles", m_timeout_cycles, $bits(m_timeout_cycles));
    printer.print_field_int("m_enable_coverage", m_enable_coverage, 1);
  endfunction : do_print

  // Out-of-class implementation of sample_config
  function void nd_config::sample_config();
    config_cg.sample();
  endfunction : sample_config

`endif // ND_CONFIG_SV
