# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os
import unittest
from linter.rules.nd_001_file_header import FileHeaderRule
from linter.core.base_rule import RuleSeverity
from agent.fixer.rules.fix_nd001_file_header import FixNd001
from agent.agent import ScribeAgent


class TestHeaderTemplateAndNd001(unittest.TestCase):

    def test_missing_file_keyword_is_error(self):
        rule = FileHeaderRule()
        code = """/*
 * Company: IC Verimeter
 * Author: dev@verimeter.com
 */
module my_mod;
endmodule
"""
        violations = rule.check("my_mod.sv", code, None)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].severity, RuleSeverity.ERROR)
        self.assertIn("File:", violations[0].message)

    def test_mismatched_filename_is_error(self):
        rule = FileHeaderRule()
        code = """/*
 * File: wrong_name.sv
 * Company: IC Verimeter
 * Author: dev@verimeter.com
 */
module my_mod;
endmodule
"""
        violations = rule.check("my_mod.sv", code, None)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].severity, RuleSeverity.ERROR)
        self.assertIn("does not match actual filename", violations[0].message)

    def test_todo_placeholder_is_warning(self):
        rule = FileHeaderRule()
        code = """/*
 * File: my_mod.sv
 * Company: TODO_COMPANY
 * Author: dev@verimeter.com
 */
module my_mod;
endmodule
"""
        violations = rule.check("my_mod.sv", code, None)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].severity, RuleSeverity.WARNING)
        self.assertIn("TODO_COMPANY", violations[0].message)

    def test_missing_optional_fields_are_ignored(self):
        rule = FileHeaderRule()
        code = """/*
 * File: my_mod.sv
 */
module my_mod;
endmodule
"""
        violations = rule.check("my_mod.sv", code, None)
        self.assertEqual(len(violations), 0)

    def test_custom_template_disables_field_warnings_but_enforces_file_error(self):
        rule = FileHeaderRule()
        context = {"config": {"agent": {"custom_header_template": "dummy_template_content"}}}
        
        # Valid header with custom template
        code_valid = """/*
 * File: my_mod.sv
 * MyCustomField: 123
 * TODO_WHATEVER
 */
module my_mod;
endmodule
"""
        violations = rule.check("my_mod.sv", code_valid, context)
        self.assertEqual(len(violations), 0)

        # Missing File keyword with custom template -> MUST BE ERROR
        code_missing_file = """/*
 * MyCustomField: 123
 */
module my_mod;
endmodule
"""
        violations_bad = rule.check("my_mod.sv", code_missing_file, context)
        self.assertEqual(len(violations_bad), 1)
        self.assertEqual(violations_bad[0].severity, RuleSeverity.ERROR)

    def test_fix_nd001_propose_missing_header_inserts(self):
        fixer = FixNd001()
        violation = {
            "rule_id": "[ND-001]",
            "file": "test_component.sv",
            "line": 1,
            "message": "Missing block comment file header (/* */)."
        }
        lines = ["module test_component;\n", "endmodule\n"]
        p = fixer.propose(violation, lines, config={"agent": {"header_company": "Verimeter", "header_author": "tester@verimeter.com"}})
        self.assertIsNotNone(p)
        joined_patch = "".join(p.patch_lines)
        self.assertIn("File:        test_component.sv", joined_patch)
        self.assertTrue(len(p.patch_lines) >= 5)

    def test_fix_nd001_single_field_fix_filename_mismatch(self):
        fixer = FixNd001()
        sample_lines = [
            "/******************************************************************************\n",
            " * File:        wrong_name.sv\n",
            " * Description: Important description to keep\n",
            " ******************************************************************************/\n",
        ]
        violation = {
            "file": "correct_name.sv",
            "line": 2,
            "message": "Documented file name 'wrong_name.sv' in header does not match actual filename 'correct_name.sv'."
        }
        proposal = fixer.propose(violation, sample_lines)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.replace_range, (2, 2))
        self.assertEqual(proposal.patch_lines, [" * File:        correct_name.sv\n"])

    def test_fix_nd001_single_field_fix_author_placeholder(self):
        fixer = FixNd001()
        sample_lines = [
            "/******************************************************************************\n",
            " * File:        correct_name.sv\n",
            " * Author:      TODO_AUTHOR\n",
            " * Description: Important description to keep\n",
            " ******************************************************************************/\n",
        ]
        violation = {
            "file": "correct_name.sv",
            "line": 3,
            "message": "File header Author field contains unresolved placeholder 'TODO_AUTHOR'."
        }
        config = {"agent": {"header_author": "developer@company.com"}}
        proposal = fixer.propose(violation, sample_lines, config=config)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.replace_range, (3, 3))
        self.assertIn("developer@company.com", proposal.patch_lines[0])
        self.assertNotIn("Description", "".join(proposal.patch_lines))

    def test_fix_nd001_overwrite_header_replaces_entire_header(self):
        fixer = FixNd001()
        sample_lines = [
            "/******************************************************************************\n",
            " * File:        correct_name.sv\n",
            " * Author:      TODO_AUTHOR\n",
            " * Description: Old description\n",
            " ******************************************************************************/\n",
        ]
        violation = {
            "file": "correct_name.sv",
            "line": 1,
            "message": "Overwrite request"
        }
        proposal = fixer.propose(violation, sample_lines, overwrite_header=True)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.replace_range, (1, 5))
        self.assertTrue(len(proposal.patch_lines) > 5)

    def test_agent_template_methods(self):
        agent = ScribeAgent()
        tpath = agent.get_header_template_path()
        self.assertTrue(os.path.exists(tpath))
        self.assertTrue(tpath.endswith("header_template.txt"))


if __name__ == "__main__":
    unittest.main()
