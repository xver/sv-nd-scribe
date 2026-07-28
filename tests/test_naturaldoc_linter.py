# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os
import sys
import tempfile
import unittest

_project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_dir)

from linter.naturaldoc_linter import NaturalDocLinter


class NaturalDocLinterTests(unittest.TestCase):
    def test_prepare_context_handles_verible_parse_errors(self):
        linter = NaturalDocLinter()
        if not linter.is_available:
            self.skipTest("verible not available")

        with tempfile.NamedTemporaryFile("w", suffix=".sv", delete=False, encoding="utf-8") as handle:
            handle.write("`ifdef FOO\nmodule test;\nendmodule\n`endif\n`endif\n")
            path = handle.name

        try:
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
            context = linter.prepare_context(path, content)
            self.assertIsNotNone(context)
            self.assertTrue(hasattr(context, "file_bytes"))
        finally:
            os.unlink(path)


    def test_linter_result_to_dict_and_format_json(self):
        from linter.core.base_rule import RuleViolation, RuleSeverity
        from linter.core.base_linter import LinterResult
        import json

        result = LinterResult(linter_name="test_linter", files_checked=2, files_failed=0)
        v = RuleViolation(
            file="test.sv", line=10, column=0,
            severity=RuleSeverity.ERROR, message="Test violation", rule_id="[ND-001]"
        )
        result.add_violation(v)

        res_dict = result.to_dict()
        self.assertEqual(res_dict["linter_name"], "test_linter")
        self.assertEqual(res_dict["files_checked"], 2)
        self.assertEqual(res_dict["error_count"], 1)
        self.assertEqual(len(res_dict["violations"]), 1)
        self.assertEqual(res_dict["violations"][0]["rule_id"], "[ND-001]")

        json_str = result.format_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["linter_name"], "test_linter")
        self.assertEqual(parsed["violations"][0]["message"], "Test violation")


if __name__ == "__main__":
    unittest.main()
