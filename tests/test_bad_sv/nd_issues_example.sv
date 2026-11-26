// File: nd_issues_example.sv
// Test fixture exercising issues #4, #5, #6, and #7 for sv-nd-scribe.

// Package: issue_pkg
// Verification package containing scoped configuration objects and utilities.
package issue_pkg;

  // Class: foo_config
  // Configuration object managing checks and verification control knobs.
  class foo_config;
    // Variable: m_checks_enable
    // Enables protocol checker assertions when set.
    bit m_checks_enable;

    // Function: new
    // Instantiates configuration object.
    function new();
      m_checks_enable = 1'b1;
    endfunction : new

    extern function void set_checks_enable(bit checks_enable);
  endclass : foo_config

  // Out-of-body implementation for issue #6 verification
  function void foo_config::set_checks_enable(bit checks_enable);
    m_checks_enable = checks_enable;
  endfunction

  // Class: issue_test_cls
  // Test class containing localparam arrays and unsigned functions.
  class issue_test_cls;

    localparam int FOO_1 [3] = '{0, 128, 64};
    localparam int FOO_2 [3] = '{0, 128, 526};

    // Issue #4: multi-word primitive type int unsigned
    // Variable: m_foo
    // Multi-cycle timeout counter.
    int unsigned m_foo;

    // Issue #7: static function with multi-word return type and arg
    // Function: foo
    // Computes checksum over input argument.
    //
    // Parameters:
    //   arg - Raw input packet word.
    //
    // Returns:
    //   Transformed checksum value.
    static function int unsigned foo(int unsigned arg);
      return arg;
    endfunction : foo
  endclass : issue_test_cls

endpackage : issue_pkg
