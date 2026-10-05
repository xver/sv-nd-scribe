# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import unittest
from agent.fixer.doc_helper import extract_comment_from_context, build_naturaldocs_comment, clean_all_nested_comments
from agent.fixer.rules.fix_nd003_comment_spacing import FixNd003
from agent.fixer.rules.fix_nd004_documented_stmt import FixNd004
from agent.fixer.rules.fix_nd007_macro_doc import FixNd007
from agent.fixer.rules.fix_nd008_package_doc import FixNd008
from agent.fixer.rules.fix_nd009_class import FixNd009
from agent.fixer.rules.fix_nd010_enum_doc import FixNd010
from agent.fixer.rules.fix_nd011_type_doc import FixNd011
from agent.fixer.rules.fix_nd012_keyword_desc import FixNd012
from agent.fixer.rules.fix_nd013_interface_doc import FixNd013
from agent.fixer.rules.fix_nd014_module import FixNd014
from agent.fixer.rules.fix_nd015_property_doc import FixNd015
from agent.fixer.rules.fix_nd017_function_task import FixNd017
from agent.fixer.rules.fix_nd019_identifier_match import FixNd019
from agent.fixer.rules.fix_nd023_variable_doc import FixNd023
from agent.fixer.rules.fix_nd026_bind_doc import FixNd026
from agent.fixer.rules.fix_nd028_assign_doc import FixNd028
from linter.rules.nd_019_identifier_match import IdentifierMatchRule


class TestDocFixers(unittest.TestCase):
    def test_extract_trailing_comment(self):
        lines = ["  int m_timeout = 10; // Timeout limit in ms\n"]
        desc = extract_comment_from_context(lines, 0)
        self.assertEqual(desc, "Timeout limit in ms")

    def test_extract_block_comment(self):
        lines = ["  module my_mod (); /* Core ALU logic */\n"]
        desc = extract_comment_from_context(lines, 0)
        self.assertEqual(desc, "Core ALU logic")

    def test_extract_previous_line_comment(self):
        lines = [
            "  // Handles interrupt requests\n",
            "  task handle_irq();\n"
        ]
        desc = extract_comment_from_context(lines, 1)
        self.assertEqual(desc, "Handles interrupt requests")

    def test_fix_nd009_with_existing_comment(self):
        fixer = FixNd009()
        violation = {"rule": "ND-009", "file": "test.sv", "line": 1}
        lines = ["class packet; // Network packet container\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("// Class: packet\n", proposal.patch_lines[0])
        self.assertIn("// Network packet container\n", proposal.patch_lines[0])

    def test_fix_nd009_without_comment_fallback_todo(self):
        fixer = FixNd009()
        violation = {"rule": "ND-009", "file": "test.sv", "line": 1}
        lines = ["class packet;\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("// Class: packet\n", proposal.patch_lines[0])
        self.assertIn("// TODO [SVND]: Add description for class 'packet'\n", proposal.patch_lines[0])

    def test_fix_nd014_module_fallback_todo(self):
        fixer = FixNd014()
        violation = {"rule": "ND-014", "file": "test.sv", "line": 1}
        lines = ["module alu;\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("// Module: alu\n", proposal.patch_lines[0])
        self.assertIn("// TODO [SVND]: Add description for module 'alu'\n", proposal.patch_lines[0])

    def test_fix_nd017_function_with_params(self):
        fixer = FixNd017()
        violation = {"rule": "ND-017", "file": "test.sv", "line": 1}
        lines = ["function int compute(int a, int b); // Computes sum\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("// Function: compute\n", proposal.patch_lines[0])
        self.assertIn("// Computes sum\n", proposal.patch_lines[0])
        self.assertIn("Parameters:\n", proposal.patch_lines[0])
        self.assertIn("a - First operand input.", proposal.patch_lines[0])
        self.assertIn("b - Second operand input.", proposal.patch_lines[0])
        self.assertNotIn("Description for", proposal.patch_lines[0])

    def test_fix_nd023_variable_fallback_todo(self):
        fixer = FixNd023()
        violation = {"rule": "ND-023", "file": "test.sv", "line": 1}
        lines = ["  int m_status;\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("  // Variable: m_status\n", proposal.patch_lines[0])
        self.assertIn("  // TODO [SVND]: Add description for variable 'm_status'\n", proposal.patch_lines[0])

    def test_fix_nd026_bind_generates_bind_tag(self):
        fixer = FixNd026()
        violation = {"rule": "ND-026", "file": "test.sv", "line": 1}
        lines = ["bind nd_dut nd_checker checker_inst (.clk(clk));\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("// Bind: checker_inst\n", proposal.patch_lines[0])
        self.assertIn("// TODO [SVND]: Add description for bind 'checker_inst'\n", proposal.patch_lines[0])

    def test_fix_nd028_assign_generates_assign_tag(self):
        fixer = FixNd028()
        violation = {"rule": "ND-028", "file": "test.sv", "line": 1}
        lines = ["assign data_out = data_in;\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("// Assign: data_out\n", proposal.patch_lines[0])
        self.assertIn("// TODO [SVND]: Add description for assignment 'data_out'\n", proposal.patch_lines[0])

    def test_fix_nd028_hierarchical_assign_preserves_full_signal_path(self):
        fixer = FixNd028()
        violation = {"rule": "ND-028", "file": "test.sv", "line": 1, "message": "Continuous assignment 'tb_if' is missing preceding NaturalDocs comment."}
        lines = ["  assign tb_if.m_abs_agent1_if.ready = 1'b1;\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("// Assign: tb_if.m_abs_agent1_if.ready\n", proposal.patch_lines[0])
        self.assertNotIn("// Assign: tb_if\n", proposal.patch_lines[0])

    def test_fix_nd028_deep_synth_generates_detailed_handshake_comment(self):
        fixer = FixNd028()
        violation = {"rule": "ND-028", "file": "test.sv", "line": 1}
        lines = ["  assign tb_if.m_abs_agent1_if.ready = 1'b1;\n"]
        proposal = fixer.propose(violation, lines, config={"deep_synth": True})
        self.assertIsNotNone(proposal)
        self.assertIn("// Assign: tb_if.m_abs_agent1_if.ready\n", proposal.patch_lines[0])
        self.assertIn("ready handshake", proposal.patch_lines[0])
        self.assertNotIn("definition for tb if", proposal.patch_lines[0])

    def test_nd019_linter_rule_flags_class_mismatch(self):
        rule = IdentifierMatchRule()
        content = (
            "// Class: old_class\n"
            "// Description\n"
            "class new_class;\n"
            "endclass\n"
        )
        viols = rule.check("sample.sv", content, None)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].rule_id, "[ND-019]")
        self.assertIn("Documented identifier 'old_class' does not match code identifier 'new_class'", viols[0].message)

    def test_nd019_linter_rule_flags_variable_mismatch(self):
        rule = IdentifierMatchRule()
        content = (
            "class a;\n"
            "  // Variable: his_is_a_very_long_line\n"
            "  // TODO: Add description for variable 'his_is_a_very_long_line'\n"
            "  int m_this_is_a_very_long_line;\n"
            "endclass\n"
        )
        viols = rule.check("sample.sv", content, None)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].rule_id, "[ND-019]")
        self.assertIn("Documented identifier 'his_is_a_very_long_line' does not match code identifier 'm_this_is_a_very_long_line'", viols[0].message)

    def test_nd019_linter_rule_flags_bind_mismatch(self):
        rule = IdentifierMatchRule()
        content = (
            "// Bind: checker_inst\n"
            "// Description\n"
            "bind nd_dut nd_checker m_checker_inst (\n"
            "  .clk(clk)\n"
            ");\n"
        )
        viols = rule.check("sample.sv", content, None)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].rule_id, "[ND-019]")
        self.assertIn("Documented identifier 'checker_inst' does not match code identifier 'm_checker_inst'", viols[0].message)

    def test_nd019_linter_rule_flags_assign_mismatch(self):
        rule = IdentifierMatchRule()
        content = (
            "// Assign: old_signal\n"
            "// Description\n"
            "assign new_signal = 1'b0;\n"
        )
        viols = rule.check("sample.sv", content, None)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].rule_id, "[ND-019]")
        self.assertIn("Documented identifier 'old_signal' does not match code identifier 'new_signal'", viols[0].message)

    def test_nd019_linter_rule_flags_typedef_mismatch(self):
        rule = IdentifierMatchRule()
        content = (
            "// Type: old_state_t\n"
            "// Description\n"
            "typedef enum { IDLE, RUN } new_state_t;\n"
        )
        viols = rule.check("sample.sv", content, None)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].rule_id, "[ND-019]")
        self.assertIn("Documented identifier 'old_state_t' does not match code identifier 'new_state_t'", viols[0].message)

    def test_nd019_linter_rule_flags_macro_mismatch(self):
        rule = IdentifierMatchRule()
        content = (
            "// define: OLD_MACRO\n"
            "// Description\n"
            "`define NEW_MACRO 100\n"
        )
        viols = rule.check("sample.sv", content, None)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].rule_id, "[ND-019]")
        self.assertIn("Documented identifier 'OLD_MACRO' does not match code identifier 'NEW_MACRO'", viols[0].message)

    def test_nd019_linter_rule_flags_function_mismatch(self):
        rule = IdentifierMatchRule()
        content = (
            "// Function: old_func\n"
            "// Description\n"
            "function void new_func();\n"
            "endfunction\n"
        )
        viols = rule.check("sample.sv", content, None)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].rule_id, "[ND-019]")
        self.assertIn("Documented identifier 'old_func' does not match code identifier 'new_func'", viols[0].message)

    def test_nd019_linter_rule_flags_module_mismatch(self):
        rule = IdentifierMatchRule()
        content = (
            "// Module: old_mod\n"
            "// Description\n"
            "module new_mod ();\n"
            "endmodule\n"
        )
        viols = rule.check("sample.sv", content, None)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].rule_id, "[ND-019]")
        self.assertIn("Documented identifier 'old_mod' does not match code identifier 'new_mod'", viols[0].message)

    def test_fix_nd019_multi_line_comment_update(self):
        fixer = FixNd019()
        violation = {
            "rule": "ND-019",
            "file": "test.sv",
            "line": 3,
            "message": "Documented identifier 'old_var' does not match code identifier 'm_new_var'."
        }
        lines = [
            "  // Variable: old_var\n",
            "  // TODO: Add description for variable 'old_var'\n",
            "  int m_new_var;\n"
        ]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.replace_range, (1, 2))
        self.assertEqual(proposal.patch_lines[0], "  // Variable: m_new_var\n")
        self.assertEqual(proposal.patch_lines[1], "  // TODO: Add description for variable 'm_new_var'\n")

    def test_fix_nd019_bind_update(self):
        fixer = FixNd019()
        violation = {
            "rule": "ND-019",
            "file": "nd_bind.sv",
            "line": 3,
            "message": "Documented identifier 'checker_inst' does not match code identifier 'm_checker_inst'."
        }
        lines = [
            "// Bind: checker_inst\n",
            "// TODO: Add description for bind 'checker_inst'\n",
            "bind nd_dut nd_checker m_checker_inst (\n",
            "  .clk(clk)\n",
            ");\n"
        ]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.replace_range, (1, 2))
        self.assertEqual(proposal.patch_lines[0], "// Bind: m_checker_inst\n")
        self.assertEqual(proposal.patch_lines[1], "// TODO: Add description for bind 'm_checker_inst'\n")

    def test_fix_nd019_long_identifier_update(self):
        fixer = FixNd019()
        old_name = "his_is_a_very_long_line_that_definitely_exceeds_the_eighty_character_limit_specified_by_wkl_007_tail________________tail"
        new_name = "m_this_is_a_very_long_line_that_definitely_exceeds_the_eighty_character_limit_specified_by_wkl_007_tail________________tail"
        violation = {
            "rule": "ND-019",
            "file": "test.sv",
            "line": 3,
            "message": f"Documented identifier '{old_name}' does not match code identifier '{new_name}'."
        }
        lines = [
            f"  // Variable: {old_name}\n",
            f"  // TODO: Add description for variable '{old_name}'\n",
            f"  int {new_name};\n"
        ]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.replace_range, (1, 2))
        self.assertEqual(proposal.patch_lines[0], f"  // Variable: {new_name}\n")
        self.assertEqual(proposal.patch_lines[1], f"  // TODO: Add description for variable '{new_name}'\n")

    def test_fix_nd019_block_comment_without_asterisks(self):
        fixer = FixNd019()
        violation = {
            "rule": "ND-019",
            "file": "test_tb_template_sanity.sv",
            "line": 5,
            "message": "Documented identifier 'test_tb_template_sanity' does not match code identifier 'test_tb_template_sanity_config'."
        }
        lines = [
            "/*\n",
            "  Class: test_tb_template_sanity\n",
            "  SystemVerilog element definition for tb template test config.\n",
            "*/\n",
            "class test_tb_template_sanity_config extends tb_template_test_config;\n"
        ]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.replace_range, (2, 2))
        self.assertEqual(proposal.patch_lines[0], "  Class: test_tb_template_sanity_config\n")


    def test_fix_nd017_void_function(self):
        fixer = FixNd017()
        violation = {"rule": "ND-017", "file": "test.sv", "line": 1}
        lines = ["  function void build_phase(uvm_phase phase);\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("  // Function: build_phase\n", proposal.patch_lines[0])
        self.assertIn("  // TODO [SVND]: Add description for function 'build_phase'\n", proposal.patch_lines[0])
        self.assertIn("phase - UVM phase object governing test execution flow.", proposal.patch_lines[0])
        self.assertNotIn("Description for", proposal.patch_lines[0])

    def test_fix_nd017_ast_violation_message_reuse(self):
        fixer = FixNd017()
        violation = {
            "rule": "ND-017",
            "file": "test.sv",
            "line": 1,
            "message": "Function 'build_phase' is missing a NaturalDocs comment ('// Function: build_phase')."
        }
        lines = ["  virtual function void build_phase(uvm_phase phase);\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("  // Function: build_phase\n", proposal.patch_lines[0])

    def test_fix_nd003_nested_slash_inside_block_comment(self):
        fixer = FixNd003()
        violation = {
            "rule": "ND-003",
            "file": "tb_template_reg_adapter.sv",
            "line": 3,
            "message": "Redundant single-line comment marker '//' inside block comment."
        }
        lines = [
            "/*\n",
            "  Class: tb_template_reg_adapter\n",
            "//   SystemVerilog element definition for uvm reg adapter.\n",
            "*/\n",
            "class tb_template_reg_adapter extends uvm_reg_adapter;\n"
        ]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.patch_lines[0], "  SystemVerilog element definition for uvm reg adapter.\n")

    def test_fix_nd003_redundant_single_line_markers(self):
        fixer = FixNd003()
        lines = [
            "// // Double slash line\n",
            "//// Four slashes line with text\n",
            "// /* Block inside line */\n",
            "// Class:my_class\n"
        ]
        # Line 1: // //
        p1 = fixer.propose({"rule": "ND-003", "file": "test.sv", "line": 1, "message": ""}, lines)
        self.assertIsNotNone(p1)
        self.assertEqual(p1.patch_lines[0], "// Double slash line\n")

        # Line 2: ////
        p2 = fixer.propose({"rule": "ND-003", "file": "test.sv", "line": 2, "message": ""}, lines)
        self.assertIsNotNone(p2)
        self.assertEqual(p2.patch_lines[0], "// Four slashes line with text\n")

        # Line 3: // /* ... */
        p3 = fixer.propose({"rule": "ND-003", "file": "test.sv", "line": 3, "message": ""}, lines)
        self.assertIsNotNone(p3)
        self.assertEqual(p3.patch_lines[0], "// Block inside line\n")

        # Line 4: space after colon
        p4 = fixer.propose({"rule": "ND-003", "file": "test.sv", "line": 4, "message": ""}, lines)
        self.assertIsNotNone(p4)
        self.assertEqual(p4.patch_lines[0], "// Class: my_class\n")

    def test_clean_all_nested_comments_helper(self):
        from agent.fixer.doc_helper import clean_all_nested_comments
        lines = [
            "/*\n",
            "  Class: tb_template_reg_adapter\n",
            "//   SystemVerilog element definition for uvm reg adapter.\n",
            "*/\n",
            "class tb_template_reg_adapter extends uvm_reg_adapter;\n",
            "  /*\n",
            "    Function: new\n",
            "    //   SystemVerilog element definition for new.\n",
            "  */\n",
            "  // Function: new\n",
            "  //   Constructor creates and initializes new.\n",
            "  function new(string name = \"tb_template_reg_adapter\");\n",
            "  endfunction : new\n",
            "endclass : tb_template_reg_adapter\n"
        ]
        modified, changes = clean_all_nested_comments(lines)
        self.assertGreater(changes, 0)
        # Verify nested // stripped from class comment
        self.assertIn("  SystemVerilog element definition for uvm reg adapter.\n", modified)
        # Verify duplicate stub comment for new was removed
        mod_text = "".join(modified)
        self.assertNotIn("SystemVerilog element definition for new.", mod_text)
        self.assertIn("// Function: new\n", mod_text)

    def test_fix_nd017_missing_parameters_in_block_comment(self):
        fixer = FixNd017()
        violation = {
            "rule": "ND-017",
            "file": "test.sv",
            "line": 5,
            "message": "Function 'new' has parameters but is missing a 'Parameters:' section."
        }
        lines = [
            "  /*\n",
            "    Function: new\n",
            "    SystemVerilog element definition for new.\n",
            "  */\n",
            "  function new(string name = \"tb_template_reg_adapter\");\n",
            "  endfunction : new\n",
        ]
        proposal = fixer.propose(violation, lines)
        # Should replace lines 1..4 (the block comment) in-place with Parameters block added
        self.assertEqual(proposal.replace_range, (1, 4))
        patch_text = "".join(proposal.patch_lines)
        self.assertIn("Parameters:\n", patch_text)
        self.assertIn("name - Instance name for UVM factory registration and hierarchy.", patch_text)
        self.assertNotIn("//", patch_text)  # Block comments should NOT have nested //

    def test_fix_nd017_keyword_from_function_declaration(self):
        fixer = FixNd017()
        violation = {
            "rule": "ND-017",
            "file": "test.sv",
            "line": 1,
            "message": "Function/Task 'reg2bus' has parameters but is missing a 'Parameters:' section."
        }
        lines = [
            "  extern virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);\n"
        ]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("// Function: reg2bus\n", proposal.patch_lines[0])
        self.assertNotIn("Task:", proposal.patch_lines[0])

    def test_clean_all_nested_comments_fixes_mismatched_function_task_tag(self):
        lines = [
            "  // Task: reg2bus\n",
            "  //   TODO [SVND]: Add description for task 'reg2bus'\n",
            "  //\n",
            "  // Parameters:\n",
            "  //   rw - Input parameter rw.\n",
            "  extern virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);\n"
        ]
        modified, changes = clean_all_nested_comments(lines)
        self.assertGreater(changes, 0)
        mod_text = "".join(modified)
        self.assertIn("// Function: reg2bus\n", mod_text)
        self.assertNotIn("// Task: reg2bus", mod_text)
        self.assertIn("description for function 'reg2bus'", mod_text)

    def test_fix_nd017_fixes_tag_mismatch_and_empty_parameters(self):
        fixer = FixNd017()
        violation = {
            "rule": "ND-017",
            "file": "test.sv",
            "line": 7,
            "message": "Task 'body' is missing a NaturalDocs comment ('// Task: body')."
        }
        lines = [
            "  /*\n",
            "    Function: body\n",
            "    SystemVerilog element definition for body.\n",
            "\n",
            "    Parameters:\n",
            "  */\n",
            "  extern virtual task body();\n"
        ]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.replace_range, (1, 6))
        patch_text = "".join(proposal.patch_lines)
        self.assertIn("Task: body", patch_text)
        self.assertNotIn("Function: body", patch_text)
        self.assertNotIn("Parameters:", patch_text)

    def test_fix_nd027_process_deep_analysis(self):
        from agent.fixer.rules.fix_nd027_process_doc import FixNd027
        fixer = FixNd027()
        violation = {
            "rule": "ND-027",
            "file": "tb_template_abs_agent0_link_if.sv",
            "line": 4,
            "message": "Process block 'initial' is missing preceding NaturalDocs comment."
        }
        lines = [
            "interface tb_template_abs_agent0_link_if;\n",
            "  tb_template_config m_config;\n",
            "\n",
            "  initial begin\n",
            "    `uvm_info(\"TB_TEMPLATE_ABS_AGENT0_LINK_IF\", \"START ABS_AGENT0 connect\", UVM_HIGH);\n",
            "    tb_template_sys_get_m_config(m_config);\n",
            "    m_config.m_abs_agent0_config.set_vif(top_tb.th.top_if.m_tb_template_if.m_abs_agent0_if);\n",
            "  end\n",
            "endinterface\n",
        ]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("// Process: abs_agent0_connect\n", proposal.patch_lines[0])
        self.assertNotIn("item", proposal.patch_lines[0])
        self.assertIn("binds virtual interface", proposal.patch_lines[0])

    def test_fix_nd027_avoids_generic_descriptions_for_common_links(self):
        from agent.fixer.rules.fix_nd027_process_doc import FixNd027
        fixer = FixNd027()

        # 1. Reset VIF binding inside generate block
        lines_rst = [
            "  for (genvar idx = 0; idx < `TB_TEMPLATE_N_RSTS; idx++) begin : gen_rst\n",
            "    initial begin\n",
            "      tb_template_sys_get_m_config(m_config);\n",
            "      m_config.m_rst_config[idx].vif = top_tb.th.top_if.rst_if[idx];\n",
            "    end\n",
            "  end\n",
        ]
        proposal_rst = fixer.propose({"rule": "ND-027", "file": "common_if.sv", "line": 2}, lines_rst)
        self.assertIsNotNone(proposal_rst)
        text_rst = "".join(proposal_rst.patch_lines)
        self.assertIn("Process: rst_vif_connect", text_rst)
        self.assertIn("rst_if", text_rst)
        self.assertNotIn("startup initialization and configuration setup", text_rst)

        # 2. Watchdog VIF binding with clock force
        lines_wd = [
            "  initial begin : watchdog\n",
            "    tb_template_sys_get_m_config(m_config);\n",
            "    m_config.m_watchdog_config.vif = top_tb.th.top_if.watchdog_if;\n",
            "    force top_tb.th.top_if.watchdog_if.clk = top_tb.th.top_if.clk_if[0].clk;\n",
            "  end\n",
        ]
        proposal_wd = fixer.propose({"rule": "ND-027", "file": "common_if.sv", "line": 1}, lines_wd)
        self.assertIsNotNone(proposal_wd)
        text_wd = "".join(proposal_wd.patch_lines)
        self.assertIn("Process: watchdog", text_wd)
        self.assertIn("watchdog virtual interface", text_wd)
        self.assertIn("Forces watchdog clock", text_wd)
        self.assertNotIn("startup initialization and configuration setup", text_wd)


if __name__ == "__main__":
    unittest.main()


