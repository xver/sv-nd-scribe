# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import unittest
from linter.rules.nd_019_identifier_match import IdentifierMatchRule
from agent.fixer.rules.fix_nd019_identifier_match import FixNd019


class TestAllNDIdentifierConsistency(unittest.TestCase):
    """
    Exhaustive unit test suite verifying name consistency across ALL NaturalDocs rules.
    Every construct type is tested for:
      1. Detection of mismatched documented name vs code identifier ([ND-019]).
      2. Automated fix ([FixNd019]) which updates the ND comments to match the code identifier.
      3. Clean re-lint verification after the fix.
    """

    def setUp(self):
        self.rule = IdentifierMatchRule()
        self.fixer = FixNd019()

    def _verify_mismatch_and_fix(self, construct_kind, old_name, new_name, code_snippet, expected_tag):
        # 1. Check mismatch is flagged by linter rule
        viols = self.rule.check("test.sv", code_snippet, None)
        self.assertTrue(
            len(viols) >= 1,
            f"Expected [ND-019] violation for {construct_kind}, but got none.\nCode:\n{code_snippet}"
        )
        nd019_viols = [v for v in viols if v.rule_id == "[ND-019]"]
        self.assertTrue(
            len(nd019_viols) >= 1,
            f"Expected [ND-019] rule_id for {construct_kind}, got: {[v.rule_id for v in viols]}"
        )
        self.assertIn(old_name, nd019_viols[0].message)
        self.assertIn(new_name, nd019_viols[0].message)

        # 2. Check fixer proposes update to new_name
        lines = code_snippet.splitlines(keepends=True)
        v_dict = {
            "rule": "ND-019",
            "file": "test.sv",
            "line": nd019_viols[0].line,
            "message": nd019_viols[0].message,
        }
        proposal = self.fixer.propose(v_dict, lines)
        self.assertIsNotNone(proposal, f"Fixer failed to propose fix for {construct_kind}")
        
        # Verify patch contains new_name and not isolated old_name
        patch_text = "".join(proposal.patch_lines)
        self.assertIn(new_name, patch_text)
        self.assertNotIn(f": {old_name}\n", patch_text)
        self.assertNotIn(f"'{old_name}'", patch_text)

        # 3. Apply patch and verify re-lint has 0 ND-019 violations
        start_idx = proposal.replace_range[0] - 1
        end_idx = proposal.replace_range[1] - 1
        fixed_lines = lines[:start_idx] + proposal.patch_lines + lines[end_idx + 1:]
        fixed_content = "".join(fixed_lines)

        re_viols = self.rule.check("test.sv", fixed_content, None)
        re_nd019 = [v for v in re_viols if v.rule_id == "[ND-019]"]
        self.assertEqual(
            len(re_nd019), 0,
            f"Expected 0 [ND-019] violations after fix for {construct_kind}, got:\n{re_nd019}\nFixed code:\n{fixed_content}"
        )

    def test_nd007_macro_define(self):
        code = (
            "// define: OLD_MACRO\n"
            "// TODO: Add description for macro 'OLD_MACRO'\n"
            "`define NEW_MACRO 100\n"
        )
        self._verify_mismatch_and_fix("macro", "OLD_MACRO", "NEW_MACRO", code, "define")

    def test_nd008_package(self):
        code = (
            "// Package: old_pkg\n"
            "// TODO: Add description for package 'old_pkg'\n"
            "package new_pkg;\n"
            "endpackage : new_pkg\n"
        )
        self._verify_mismatch_and_fix("package", "old_pkg", "new_pkg", code, "Package")

    def test_nd009_class(self):
        code = (
            "// Class: old_class\n"
            "// TODO: Add description for class 'old_class'\n"
            "class new_class;\n"
            "endclass : new_class\n"
        )
        self._verify_mismatch_and_fix("class", "old_class", "new_class", code, "Class")

    def test_nd010_enum(self):
        code = (
            "// enum: old_enum_t\n"
            "// TODO: Add description for enum 'old_enum_t'\n"
            "typedef enum { S0, S1 } new_enum_t;\n"
        )
        self._verify_mismatch_and_fix("enum", "old_enum_t", "new_enum_t", code, "enum")

    def test_nd011_typedef(self):
        code = (
            "// Type: old_type_t\n"
            "// TODO: Add description for type 'old_type_t'\n"
            "typedef logic [31:0] new_type_t;\n"
        )
        self._verify_mismatch_and_fix("typedef", "old_type_t", "new_type_t", code, "Type")

    def test_nd013_interface(self):
        code = (
            "// Interface: old_bus_if\n"
            "// TODO: Add description for interface 'old_bus_if'\n"
            "interface new_bus_if (input logic clk);\n"
            "endinterface : new_bus_if\n"
        )
        self._verify_mismatch_and_fix("interface", "old_bus_if", "new_bus_if", code, "Interface")

    def test_nd014_module(self):
        code = (
            "// Module: old_alu\n"
            "// TODO: Add description for module 'old_alu'\n"
            "module new_alu ();\n"
            "endmodule : new_alu\n"
        )
        self._verify_mismatch_and_fix("module", "old_alu", "new_alu", code, "Module")

    def test_nd015_property(self):
        code = (
            "// Property: p_old_req\n"
            "// TODO: Add description for property 'p_old_req'\n"
            "property p_new_req;\n"
            "  @(posedge clk) req |-> ack;\n"
            "endproperty : p_new_req\n"
        )
        self._verify_mismatch_and_fix("property", "p_old_req", "p_new_req", code, "Property")

    def test_nd017_function(self):
        code = (
            "// Function: old_calc\n"
            "// TODO: Add description for function 'old_calc'\n"
            "function int new_calc(int a, int b);\n"
            "  return a + b;\n"
            "endfunction\n"
        )
        self._verify_mismatch_and_fix("function", "old_calc", "new_calc", code, "Function")

    def test_nd017_task(self):
        code = (
            "// Task: old_send\n"
            "// TODO: Add description for task 'old_send'\n"
            "task new_send(input int pkt);\n"
            "  #10;\n"
            "endtask\n"
        )
        self._verify_mismatch_and_fix("task", "old_send", "new_send", code, "Task")

    def test_nd018_nd025_checker(self):
        code = (
            "// Checker: old_checker\n"
            "// TODO: Add description for checker 'old_checker'\n"
            "checker new_checker (input logic clk, input logic rst_n);\n"
            "endchecker : new_checker\n"
        )
        self._verify_mismatch_and_fix("checker", "old_checker", "new_checker", code, "Checker")

    def test_nd020_constraint(self):
        code = (
            "// Constraint: c_old_len\n"
            "// TODO: Add description for constraint 'c_old_len'\n"
            "constraint c_new_len { len inside {[1:100]}; }\n"
        )
        self._verify_mismatch_and_fix("constraint", "c_old_len", "c_new_len", code, "Constraint")

    def test_nd021_covergroup(self):
        code = (
            "// Covergroup: old_cg\n"
            "// TODO: Add description for covergroup 'old_cg'\n"
            "covergroup new_cg;\n"
            "endgroup : new_cg\n"
        )
        self._verify_mismatch_and_fix("covergroup", "old_cg", "new_cg", code, "Covergroup")

    def test_nd022_coverpoint(self):
        code = (
            "// Coverpoint: cp_old_addr\n"
            "// TODO: Add description for coverpoint 'cp_old_addr'\n"
            "cp_new_addr : coverpoint m_addr;\n"
        )
        self._verify_mismatch_and_fix("coverpoint", "cp_old_addr", "cp_new_addr", code, "Coverpoint")

    def test_nd023_variable(self):
        code = (
            "// Variable: old_timeout\n"
            "// TODO: Add description for variable 'old_timeout'\n"
            "int m_new_timeout = 100;\n"
        )
        self._verify_mismatch_and_fix("variable", "old_timeout", "m_new_timeout", code, "Variable")

    def test_nd026_bind(self):
        code = (
            "// Bind: old_bind_inst\n"
            "// TODO: Add description for bind 'old_bind_inst'\n"
            "bind nd_dut nd_checker m_new_bind_inst (\n"
            "  .clk(clk)\n"
            ");\n"
        )
        self._verify_mismatch_and_fix("bind", "old_bind_inst", "m_new_bind_inst", code, "Bind")

    def test_nd028_assign(self):
        code = (
            "// Assign: old_data\n"
            "// TODO: Add description for assign 'old_data'\n"
            "assign new_data = in_data;\n"
        )
        self._verify_mismatch_and_fix("assign", "old_data", "new_data", code, "Assign")

    def test_nd029_program(self):
        code = (
            "// Program: old_prog\n"
            "// TODO: Add description for program 'old_prog'\n"
            "program new_prog;\n"
            "endprogram : new_prog\n"
        )
        self._verify_mismatch_and_fix("program", "old_prog", "new_prog", code, "Program")

    def test_nd031_clocking(self):
        code = (
            "// Clocking: old_cb\n"
            "// TODO: Add description for clocking 'old_cb'\n"
            "clocking new_cb @(posedge clk);\n"
            "endclocking : new_cb\n"
        )
        self._verify_mismatch_and_fix("clocking", "old_cb", "new_cb", code, "Clocking")

    def test_nd032_modport(self):
        code = (
            "// Modport: manager\n"
            "// TODO: Add description for modport 'manager'\n"
            "modport m_manager (\n"
            "  clocking manager_cb,\n"
            "  output rst_n\n"
            ");\n"
        )
        self._verify_mismatch_and_fix("modport", "manager", "m_manager", code, "Modport")


if __name__ == "__main__":
    unittest.main()
