# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import unittest
from agent.fixer.doc_helper import extract_comment_from_context, build_naturaldocs_comment
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
        self.assertIn("// TODO: Add description for class 'packet'\n", proposal.patch_lines[0])

    def test_fix_nd014_module_fallback_todo(self):
        fixer = FixNd014()
        violation = {"rule": "ND-014", "file": "test.sv", "line": 1}
        lines = ["module alu;\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("// Module: alu\n", proposal.patch_lines[0])
        self.assertIn("// TODO: Add description for module 'alu'\n", proposal.patch_lines[0])

    def test_fix_nd017_function_with_params(self):
        fixer = FixNd017()
        violation = {"rule": "ND-017", "file": "test.sv", "line": 1}
        lines = ["function int compute(int a, int b); // Computes sum\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("// Function: compute\n", proposal.patch_lines[0])
        self.assertIn("// Computes sum\n", proposal.patch_lines[0])
        self.assertIn("Parameters:\n", proposal.patch_lines[0])
        self.assertIn("a - <description>", proposal.patch_lines[0])
        self.assertIn("b - <description>", proposal.patch_lines[0])

    def test_fix_nd023_variable_fallback_todo(self):
        fixer = FixNd023()
        violation = {"rule": "ND-023", "file": "test.sv", "line": 1}
        lines = ["  int m_status;\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("  // Variable: m_status\n", proposal.patch_lines[0])
        self.assertIn("  // TODO: Add description for variable 'm_status'\n", proposal.patch_lines[0])

    def test_fix_nd026_bind_generates_bind_tag(self):
        fixer = FixNd026()
        violation = {"rule": "ND-026", "file": "test.sv", "line": 1}
        lines = ["bind nd_dut nd_checker checker_inst (.clk(clk));\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("// Bind: checker_inst\n", proposal.patch_lines[0])
        self.assertIn("// TODO: Add description for bind 'checker_inst'\n", proposal.patch_lines[0])

    def test_fix_nd028_assign_generates_assign_tag(self):
        fixer = FixNd028()
        violation = {"rule": "ND-028", "file": "test.sv", "line": 1}
        lines = ["assign data_out = data_in;\n"]
        proposal = fixer.propose(violation, lines)
        self.assertIsNotNone(proposal)
        self.assertIn("// Assign: data_out\n", proposal.patch_lines[0])
        self.assertIn("// TODO: Add description for assignment 'data_out'\n", proposal.patch_lines[0])

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


if __name__ == "__main__":
    unittest.main()
