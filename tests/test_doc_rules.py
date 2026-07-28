# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os
import sys
import unittest

_project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_dir)

from linter.rules import (
    FileHeaderRule,
    IncludeGuardRule,
    KeywordDescriptionRule,
    CommentSpacingRule,
    GroupHeadingRule,
    InterfaceDocumentationRule,
    ModuleDocumentationRule,
    PropertyAssertionRule,
    CheckerDocumentationRule,
    BindDocumentationRule,
    ProcessDocumentationRule,
    AssignDocumentationRule,
    ProgramDocumentationRule,
    EndLabelRule,
    DocumentedStatementRule,
    FunctionTaskDocumentationRule,
    AdditionalCommentKindRule,
    IdentifierMatchRule,
    NaturalDocKeywordRule,
    ConstraintDocumentationRule,
    CovergroupDocumentationRule,
    CoverpointDocumentationRule,
    VariableDocumentationRule,
    ExternImplementationRule,
    InlineDocumentationRule,
    InterfaceNamingRule,
    LineLengthRule,
    MacroDocumentationRule,
    PackageDocumentationRule,
    ClockingDocumentationRule,
    ModportDocumentationRule,
)


class DocRulesTests(unittest.TestCase):
    def test_file_header_rule_flags_missing_header(self):
        rule = FileHeaderRule()
        violations = rule.check("sample.sv", "module sample();\nendmodule\n", None)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].rule_id, "[ND-001]")

    def test_include_guard_rule_flags_missing_guard(self):
        rule = IncludeGuardRule()
        violations = rule.check("sample.sv", "module sample();\nendmodule\n", None)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].rule_id, "[ND-002]")

    def test_file_header_rule_allows_any_border_width(self):
        rule = FileHeaderRule()
        content = "/*\n * File: sample.sv\n * Company: Demo\n * Author: demo@example.com\n * Description: Sample\n * Created: 2026-01-01 (demo@example.com)\n * Updated: 2026-01-01 (demo@example.com)\n */\n"
        violations = rule.check("sample.sv", content, None)

        self.assertFalse(any("border" in v.message.lower() for v in violations))

    def test_include_guard_rule_flags_missing_trailing_comment(self):
        rule = IncludeGuardRule()
        content = "`ifndef SAMPLE_SV\n`define SAMPLE_SV\nmodule sample();\nendmodule\n`endif\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("trailing comment" in v.message.lower() for v in violations))

    def test_file_header_rule_flags_invalid_author_format(self):
        rule = FileHeaderRule()
        content = "/*\n * File: sample.sv\n * Company: Demo\n * Author: not-an-email\n * Description: Sample\n * Created: 2026-01-01 (demo@example.com)\n * Updated: 2026-01-01 (demo@example.com)\n */\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("author" in v.message.lower() for v in violations))

    def test_keyword_description_rule_flags_missing_description(self):
        rule = KeywordDescriptionRule()
        content = "// Package: demo_pkg\npackage demo_pkg;\n"
        violations = rule.check("sample.sv", content, None)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].rule_id, "[ND-012]")

    def test_macro_rule_allows_include_guard_defines(self):
        rule = MacroDocumentationRule()
        content = "`ifndef SAMPLE_SV\n`define SAMPLE_SV\nmodule sample();\nendmodule\n`endif\n"
        violations = rule.check("sample.sv", content, None)

        self.assertEqual(violations, [])

    def test_comment_spacing_rule_flags_missing_space_after_keyword(self):
        rule = CommentSpacingRule()
        content = "//Package:demo_pkg\npackage demo_pkg;\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("keyword format" in v.message.lower() or "start with" in v.message.lower() for v in violations))

    def test_comment_spacing_rule_allows_keyword_line_without_space_after_delimiter(self):
        rule = CommentSpacingRule()
        content = "//Group: Preprocessor Defines\n//Maximum burst length supported by the DUT (decimal)\n"
        violations = rule.check("sample.sv", content, None)

        self.assertEqual(violations, [])

    def test_naturaldoc_keyword_rule_allows_keyword_without_space_after_slashes(self):
        rule = NaturalDocKeywordRule()
        content = "//Package: demo_pkg\n"
        violations = rule.check("sample.sv", content, None)

        self.assertEqual(violations, [])

    def test_naturaldoc_keyword_rule_flags_missing_space_after_colon(self):
        rule = NaturalDocKeywordRule()
        content = "//Package:demo_pkg\n"
        violations = rule.check("sample.sv", content, None)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].rule_id, "[ND-005]")

    def test_group_heading_rule_flags_malformed_group_heading(self):
        rule = GroupHeadingRule()
        content = "class demo;\n//Group:Methods\nint x;\nendclass : demo\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("group" in v.message.lower() for v in violations))

    def test_interface_rule_flags_missing_comment(self):
        rule = InterfaceDocumentationRule()
        content = "interface demo_if;\nendinterface : demo_if\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("interface" in v.message.lower() for v in violations))

    def test_module_rule_flags_missing_comment(self):
        rule = ModuleDocumentationRule()
        content = "module demo_mod;\nendmodule : demo_mod\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("module" in v.message.lower() for v in violations))

    def test_property_assertion_rule_flags_missing_comment(self):
        rule = PropertyAssertionRule()
        content = "property p1;\nendproperty : p1\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("property" in v.message.lower() for v in violations))

    def test_package_rule_flags_missing_comment(self):
        rule = PackageDocumentationRule()
        content = "package demo_pkg;\nendpackage : demo_pkg\n"
        violations = rule.check("sample.sv", content, None)
        self.assertTrue(any("package" in v.message.lower() for v in violations))

    def test_package_rule_allows_commented_package(self):
        rule = PackageDocumentationRule()
        content = "// Package: demo_pkg\n// A demo package.\npackage demo_pkg;\nendpackage : demo_pkg\n"
        violations = rule.check("sample.sv", content, None)
        self.assertEqual(violations, [])

    def test_bind_rule_flags_missing_comment(self):
        rule = BindDocumentationRule()
        content = "bind nd_dut nd_checker chk_inst (.clk(clk));\n"
        violations = rule.check("sample.sv", content, None)
        self.assertTrue(any(v.rule_id == "[ND-026]" for v in violations))

    def test_process_rule_flags_missing_comment(self):
        rule = ProcessDocumentationRule()
        content = "always_ff @(posedge clk) begin : ff_p\n  q <= d;\nend\n"
        violations = rule.check("sample.sv", content, None)
        self.assertTrue(any(v.rule_id == "[ND-027]" for v in violations))

    def test_process_rule_allows_commented_process(self):
        rule = ProcessDocumentationRule()
        content = "//process: ff_p\n//Sequential flip-flop.\nalways_ff @(posedge clk) begin : ff_p\n  q <= d;\nend\n"
        violations = rule.check("sample.sv", content, None)
        self.assertEqual(violations, [])

    def test_assign_rule_flags_missing_comment(self):
        rule = AssignDocumentationRule()
        content = "assign out = a & b;\n"
        violations = rule.check("sample.sv", content, None)
        self.assertTrue(any(v.rule_id == "[ND-028]" for v in violations))

    def test_assign_rule_allows_commented_assign(self):
        rule = AssignDocumentationRule()
        content = "//assign: out\n//AND reduction.\nassign out = a & b;\n"
        violations = rule.check("sample.sv", content, None)
        self.assertEqual(violations, [])

    def test_program_rule_flags_missing_comment(self):
        rule = ProgramDocumentationRule()
        content = "program nd_test_program;\nendprogram : nd_test_program\n"
        violations = rule.check("sample.sv", content, None)
        self.assertTrue(any(v.rule_id == "[ND-029]" for v in violations))

    def test_program_rule_allows_commented_program(self):
        rule = ProgramDocumentationRule()
        content = "//Program: nd_test_program\n//Main test program.\nprogram nd_test_program;\nendprogram : nd_test_program\n"
        violations = rule.check("sample.sv", content, None)
        self.assertEqual(violations, [])

    def test_end_label_rule_flags_missing_label(self):
        rule = EndLabelRule()
        content = "class demo;\nendclass\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("labeled end statement" in v.message.lower() for v in violations))

    def test_function_task_rule_flags_missing_comment(self):
        rule = FunctionTaskDocumentationRule()
        content = "function void demo();\nendfunction\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("missing a naturaldocs comment" in v.message.lower() for v in violations))

    def test_documented_statement_rule_allows_blank_line_between_comment_and_statement(self):
        rule = DocumentedStatementRule()
        content = "// Class: demo_cls\n\nclass demo_cls;\nendclass : demo_cls\n"
        violations = rule.check("sample.sv", content, None)

        self.assertEqual(len(violations), 0)

    def test_documented_statement_rule_uses_ast_comment_block_without_false_blank_line(self):
        from linter.naturaldoc_linter import ASTContext

        class FakeToken:
            def __init__(self, tag, text, start):
                self.tag = tag
                self.text = text
                self.start = start

        class FakeNode:
            def __init__(self, text, start):
                self.text = text
                self.start = start

        class FakeTree:
            def __init__(self, nodes):
                self._nodes = nodes

            def find_all(self, filter_, max_count=0, iter_=None, **kwargs):
                return [node for node in self._nodes if filter_(node)]

        sample = "// Class: demo_cls\nclass demo_cls;\nendclass : demo_cls\n"
        tokens = [
            FakeToken('TK_COMMENT', '// Class: demo_cls', 0),
            FakeToken('TK_NEWLINE', '\n', sample.index('\n')),
            FakeToken('TK_KEYWORD', 'class', sample.index('class')),
        ]
        node = FakeNode('class demo_cls;\nendclass : demo_cls\n', sample.index('class'))
        context = ASTContext(tree=FakeTree([node]), file_bytes=sample.encode('utf-8'), rawtokens=tokens)

        rule = DocumentedStatementRule()
        violations = rule.check('sample.sv', sample, context)

        self.assertEqual(violations, [])

    def test_additional_comment_kind_rule_flags_missing_comment(self):
        rule = AdditionalCommentKindRule()
        content = "checker demo_chk();\nendchecker : demo_chk\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("checker" in v.message.lower() for v in violations))

    def test_identifier_match_rule_flags_mismatch(self):
        rule = IdentifierMatchRule()
        content = "// Class: wrong_name\nclass demo_class;\nendclass : demo_class\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("identifier" in v.message.lower() for v in violations))

    def test_identifier_match_rule_uses_ast_comments_for_package(self):
        from linter.naturaldoc_linter import ASTContext

        class FakeNode:
            def __init__(self, text, start):
                self.text = text
                self.start = start

        class FakeTree:
            def __init__(self, nodes):
                self._nodes = nodes

            def find_all(self, filter_, max_count=0, iter_=None, **kwargs):
                return [node for node in self._nodes if filter_(node)]

        sample = "// Package: demo_pkg\npackage demo_pkg;\nendpackage : demo_pkg\n"
        start = sample.index("package")
        node = FakeNode("package demo_pkg;\nendpackage : demo_pkg\n", start)
        context = ASTContext(tree=FakeTree([node]), file_bytes=sample.encode('utf-8'), rawtokens=None)

        rule = IdentifierMatchRule()
        violations = rule.check("sample.sv", sample, context)

        self.assertEqual(violations, [])

    def test_identifier_match_supports_modport_and_clocking(self):
        rule = IdentifierMatchRule()
        sample_modport = "// Modport: wrong_name\nmodport manager (input clk);\n"
        violations = rule.check("sample.sv", sample_modport, None)
        self.assertTrue(any("wrong_name" in v.message for v in violations))

        sample_clocking = "// Clocking: wrong_cb\nclocking manager_cb @(posedge clk);\nendclocking : manager_cb\n"
        violations_cb = rule.check("sample.sv", sample_clocking, None)
        self.assertTrue(any("wrong_cb" in v.message for v in violations_cb))

    def test_constraint_rule_flags_missing_comment(self):
        rule = ConstraintDocumentationRule()
        content = "constraint addr_range_c {\n  m_addr inside {[32'h1000:32'h1FFF]};\n}\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("constraint" in v.message.lower() for v in violations))

    def test_covergroup_rule_flags_missing_comment(self):
        rule = CovergroupDocumentationRule()
        content = "covergroup config_cg;\nendgroup\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("covergroup" in v.message.lower() for v in violations))

    def test_coverpoint_rule_flags_missing_comment(self):
        rule = CoverpointDocumentationRule()
        content = "coverpoint cp_num_trans {\n  bins low = {[1:100]};\n}\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("coverpoint" in v.message.lower() for v in violations))

    def test_variable_rule_flags_missing_comment(self):
        rule = VariableDocumentationRule()
        content = "logic [31:0] addr;\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("variable" in v.message.lower() for v in violations))

    def test_variable_rule_flags_missing_instance_comment(self):
        rule = VariableDocumentationRule()
        content = "module demo_mod;\nnd_bus_if bus_if();\nendmodule : demo_mod\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("variable" in v.message.lower() for v in violations))

    def test_variable_rule_flags_missing_typedef_comment(self):
        rule = VariableDocumentationRule()
        content = "typedef logic [31:0] addr_t;\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("variable" in v.message.lower() for v in violations))

    def test_variable_rule_skips_enum_typedefs(self):
        rule = VariableDocumentationRule()
        content = "// enum: state_e\ntypedef enum { IDLE, ACTIVE } state_e;\n"
        violations = rule.check("sample.sv", content, None)

        self.assertEqual(violations, [])

    def test_variable_rule_skips_modport_declarations(self):
        rule = VariableDocumentationRule()
        content = "modport manager (output addr, data, wr_en, valid, input ready);\n"
        violations = rule.check("sample.sv", content, None)

        self.assertEqual(violations, [])

    def test_variable_rule_skips_inside_clocking_and_modport_structures(self):
        rule = VariableDocumentationRule()
        content = (
            "clocking cb @(posedge clk);\n"
            "  default input #1step output #1step;\n"
            "  output addr, data;\n"
            "  input ready;\n"
            "endclocking : cb\n"
            "modport mp (\n"
            "  output addr,\n"
            "  input ready\n"
            ");\n"
        )
        violations = rule.check("sample.sv", content, None)

        self.assertEqual(violations, [])

    def test_variable_rule_allows_typedef_with_matching_comment(self):
        rule = VariableDocumentationRule()
        content = "// Typedef: addr_t\ntypedef logic [31:0] addr_t;\n"
        violations = rule.check("sample.sv", content, None)

        self.assertEqual(violations, [])

    def test_function_task_rule_flags_bad_parameter_and_return_format(self):
        rule = FunctionTaskDocumentationRule()
        content = "// Function: demo\n// Example\n// Parameters:\n//   arg\n// Returns:\n//   value\nfunction bit demo(int arg);\nendfunction : demo\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("parameters" in v.message.lower() or "returns" in v.message.lower() for v in violations))

    def test_inline_documentation_rule_flags_missing_inline_comments(self):
        rule = InlineDocumentationRule()
        content = "typedef enum { IDLE, ACTIVE } state_e;\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("inline" in v.message.lower() for v in violations))

    def test_additional_comment_kind_rule_allows_optional_process_blocks(self):
        rule = AdditionalCommentKindRule()
        content = "module demo_mod;\nalways_ff @(posedge clk) begin\n  foo <= 1;\nend\nendmodule : demo_mod\n"
        violations = rule.check("sample.sv", content, None)

        self.assertEqual(violations, [])

    def test_extern_rule_flags_missing_comment(self):
        rule = ExternImplementationRule()
        content = "class demo_cls;\nextern function void sample();\nendclass : demo_cls\nfunction void demo_cls::sample();\nendfunction : sample\n"
        violations = rule.check("sample.sv", content, None)

        self.assertTrue(any("extern" in v.message.lower() or "implementation" in v.message.lower() for v in violations))


    def test_interface_naming_rule(self):
        rule = InterfaceNamingRule()
        content = "interface my_invalid_interface;\nendinterface : my_invalid_interface\n"
        violations = rule.check("sample.sv", content, None)
        self.assertTrue(any("must end with '_if'" in v.message.lower() for v in violations))


    def test_line_length_rule(self):
        rule = LineLengthRule({"max_line_length": 50})
        content = "logic short_line;\n// This is a very long comment line that exceeds the fifty character limit.\n"
        violations = rule.check("sample.sv", content, None)
        self.assertTrue(any("exceeds maximum length" in v.message.lower() for v in violations))


    def test_clocking_rule_flags_missing_comment(self):
        rule = ClockingDocumentationRule()
        content = "clocking manager_cb @(posedge clk);\n  output addr;\nendclocking : manager_cb\n"
        violations = rule.check("sample.sv", content, None)
        self.assertTrue(any("clocking" in v.message.lower() for v in violations))
        self.assertTrue(any(v.rule_id == "[ND-031]" for v in violations))

    def test_clocking_rule_allows_commented_clocking(self):
        rule = ClockingDocumentationRule()
        content = "//Clocking: manager_cb\n//Driver clocking block.\nclocking manager_cb @(posedge clk);\n  output addr;\nendclocking : manager_cb\n"
        violations = rule.check("sample.sv", content, None)
        self.assertEqual(violations, [])

    def test_clocking_rule_flags_wrong_keyword(self):
        rule = ClockingDocumentationRule()
        content = "//Variable: manager_cb\n//Wrong keyword.\nclocking manager_cb @(posedge clk);\n  output addr;\nendclocking : manager_cb\n"
        violations = rule.check("sample.sv", content, None)
        self.assertTrue(any("clocking" in v.message.lower() for v in violations))

    def test_modport_rule_flags_missing_comment(self):
        rule = ModportDocumentationRule()
        content = "modport manager (output addr, data, input ready);\n"
        violations = rule.check("sample.sv", content, None)
        self.assertTrue(any("modport" in v.message.lower() for v in violations))
        self.assertTrue(any(v.rule_id == "[ND-032]" for v in violations))

    def test_modport_rule_allows_commented_modport(self):
        rule = ModportDocumentationRule()
        content = "//Modport: manager\n//Manager driver port.\nmodport manager (output addr, data, input ready);\n"
        violations = rule.check("sample.sv", content, None)
        self.assertEqual(violations, [])

    def test_modport_rule_flags_wrong_keyword(self):
        rule = ModportDocumentationRule()
        content = "//Variable: manager\n//Wrong keyword.\nmodport manager (output addr, input ready);\n"
        violations = rule.check("sample.sv", content, None)
        self.assertTrue(any("modport" in v.message.lower() for v in violations))

    def test_variable_rule_flags_missing_parameter_comment(self):
        rule = VariableDocumentationRule()
        content = "parameter int NUM_LANES = 4;\n"
        violations = rule.check("sample.sv", content, None)
        self.assertTrue(any("variable" in v.message.lower() or "missing" in v.message.lower() for v in violations))

    def test_variable_rule_allows_documented_parameter(self):
        rule = VariableDocumentationRule()
        content = "//Variable: NUM_LANES\n//Number of lanes.\nparameter int NUM_LANES = 4;\n"
        violations = rule.check("sample.sv", content, None)
        self.assertEqual(violations, [])


class IntegrationTests(unittest.TestCase):
    """Integration tests running the linter against actual project files."""

    _project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _template_dir = os.path.join(_project_dir, "template", "sv")
    _bad_dir = os.path.join(_project_dir, "tests", "test_bad_sv")

    def _lint_files(self, paths):
        """Run linter (text-only, no Verible) on a list of files."""
        from linter.naturaldoc_linter import NaturalDocLinter
        linter = NaturalDocLinter()
        if not linter.is_available:
            self.skipTest("verible not available — skipping integration tests")
        return linter.lint_files(paths)

    def _sv_files(self, directory):
        return sorted(
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if f.endswith(".sv")
        )

    def test_templates_produce_zero_violations(self):
        """All production template files must lint clean."""
        result = self._lint_files(self._sv_files(self._template_dir))
        error_msgs = [f"{v.file}:{v.line}: {v.rule_id} {v.message}" for v in result.violations if v.severity.name == "ERROR"]
        self.assertEqual(result.error_count, 0, "\n" + "\n".join(error_msgs))

    def test_bad_sv_produces_violations(self):
        """Negative test files must produce at least one violation."""
        result = self._lint_files(self._sv_files(self._bad_dir))
        total = result.error_count + result.warning_count
        self.assertGreater(total, 0, "Expected violations from test_bad_sv but got none")


if __name__ == "__main__":
    unittest.main()
