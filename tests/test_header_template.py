# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os
import unittest
from linter.rules.nd_001_file_header import FileHeaderRule
from linter.core.base_rule import RuleSeverity
from agent.fixer.rules.fix_nd001_file_header import FixNd001
from agent.fixer.doc_helper import resolve_author
from linter.rules.nd_001_file_header import FileHeaderRule
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



    def test_resolve_author_explicit_config(self):
        config = {"agent": {"header_defaults": {"author": "Jane <jane@example.com>"}}}
        author, source = resolve_author(config=config)
        self.assertEqual(author, "Jane <jane@example.com>")
        self.assertEqual(source, "explicit_config")

    def test_resolve_author_env_var(self):
        old_env = os.environ.get("SV_ND_SCRIBE_AUTHOR")
        try:
            os.environ["SV_ND_SCRIBE_AUTHOR"] = "Env User <env@example.com>"
            author, source = resolve_author(config={})
            self.assertEqual(author, "Env User <env@example.com>")
            self.assertEqual(source, "env_var")
        finally:
            if old_env is not None:
                os.environ["SV_ND_SCRIBE_AUTHOR"] = old_env
            else:
                os.environ.pop("SV_ND_SCRIBE_AUTHOR", None)

    def test_resolve_author_vscode_settings(self):
        # Create a temporary directory with .vscode/settings.json
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as tmpdir:
            vscode_dir = os.path.join(tmpdir, ".vscode")
            os.makedirs(vscode_dir, exist_ok=True)
            with open(os.path.join(vscode_dir, "settings.json"), "w") as f:
                json.dump({"sv-nd-scribe.author": "VSCode User <vscode@example.com>"}, f)

            dummy_sv = os.path.join(tmpdir, "test.sv")
            old_env = os.environ.pop("SV_ND_SCRIBE_AUTHOR", None)
            try:
                author, source = resolve_author(file_path=dummy_sv, config={})
                self.assertEqual(author, "VSCode User <vscode@example.com>")
                self.assertEqual(source, "vscode_settings")
            finally:
                if old_env is not None:
                    os.environ["SV_ND_SCRIBE_AUTHOR"] = old_env

    def test_resolve_author_git_config(self):
        import tempfile
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "init"], cwd=tmpdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            subprocess.run(["git", "config", "user.name", "Git User"], cwd=tmpdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            subprocess.run(["git", "config", "user.email", "gituser@example.com"], cwd=tmpdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

            dummy_sv = os.path.join(tmpdir, "test.sv")
            old_env = os.environ.pop("SV_ND_SCRIBE_AUTHOR", None)
            try:
                author, source = resolve_author(file_path=dummy_sv, config={})
                self.assertEqual(author, "Git User <gituser@example.com>")
                self.assertEqual(source, "git_config")
            finally:
                if old_env is not None:
                    os.environ["SV_ND_SCRIBE_AUTHOR"] = old_env

    def test_resolve_author_fallback_todo(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            dummy_sv = os.path.join(tmpdir, "test.sv")
            old_env = os.environ.pop("SV_ND_SCRIBE_AUTHOR", None)
            try:
                # With mock git failing or empty config
                from unittest.mock import patch
                with patch("agent.fixer.doc_helper.get_git_config_author", return_value=None):
                    author, source = resolve_author(file_path=dummy_sv, config={})
                    self.assertEqual(author, "TODO_AUTHOR")
                    self.assertEqual(source, "fallback")
            finally:
                if old_env is not None:
                    os.environ["SV_ND_SCRIBE_AUTHOR"] = old_env

    def test_nd001_file_header_actionable_todo_warning(self):
        rule = FileHeaderRule()
        content = (
            "/*\n"
            " * File: sample.sv\n"
            " * Author: TODO_AUTHOR\n"
            " */\n"
        )
        violations = rule.check(file_path="sample.sv", content=content, context={"disable_custom_template": True})
        todo_viols = [v for v in violations if "TODO_AUTHOR" in v.message]
        self.assertTrue(todo_viols, "Should report violation for TODO_AUTHOR")
        self.assertIn("sv-nd-scribe.author", todo_viols[0].message)
        self.assertIn("git config", todo_viols[0].message)


    def test_resolve_author_rejects_name_without_email(self):
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmpdir:
            dummy_sv = os.path.join(tmpdir, "test.sv")
            old_env = os.environ.pop("SV_ND_SCRIBE_AUTHOR", None)
            try:
                with patch("agent.fixer.doc_helper.get_git_config_author", return_value=None):
                    # Passing author without email (e.g. "IAM")
                    config = {"agent": {"header_defaults": {"author": "IAM"}}}
                    author, source = resolve_author(file_path=dummy_sv, config=config)
                    self.assertEqual(author, "TODO_AUTHOR")
                    self.assertEqual(source, "fallback")
            finally:
                if old_env is not None:
                    os.environ["SV_ND_SCRIBE_AUTHOR"] = old_env

    def test_resolve_company_vscode_and_fallback(self):
        import tempfile, json
        from unittest.mock import patch
        from agent.fixer.doc_helper import resolve_company
        with tempfile.TemporaryDirectory() as tmpdir:
            # Fallback when unconfigured
            c_fb, s_fb = resolve_company(file_path=os.path.join(tmpdir, "test.sv"), config={})
            self.assertEqual(c_fb, "TODO_COMPANY")
            self.assertEqual(s_fb, "fallback")

            # VS Code settings
            vsc_dir = os.path.join(tmpdir, ".vscode")
            os.makedirs(vsc_dir, exist_ok=True)
            with open(os.path.join(vsc_dir, "settings.json"), "w") as f:
                json.dump({"sv-nd-scribe.company": "Acme Microelectronics"}, f)
            c_vsc, s_vsc = resolve_company(file_path=os.path.join(tmpdir, "test.sv"), config={})
            self.assertEqual(c_vsc, "Acme Microelectronics")
            self.assertEqual(s_vsc, "vscode_settings")

    def test_resolve_legal_vscode_and_fallback(self):
        import tempfile, json
        from agent.fixer.doc_helper import resolve_legal
        with tempfile.TemporaryDirectory() as tmpdir:
            # Fallback when unconfigured
            l_fb, s_fb = resolve_legal(file_path=os.path.join(tmpdir, "test.sv"), config={})
            self.assertEqual(l_fb, "TODO_LEGAL")
            self.assertEqual(s_fb, "fallback")

            # VS Code settings
            vsc_dir = os.path.join(tmpdir, ".vscode")
            os.makedirs(vsc_dir, exist_ok=True)
            with open(os.path.join(vsc_dir, "settings.json"), "w") as f:
                json.dump({"sv-nd-scribe.legal": "Copyright 2026 Acme. All rights reserved."}, f)
            l_vsc, s_vsc = resolve_legal(file_path=os.path.join(tmpdir, "test.sv"), config={})
            self.assertEqual(l_vsc, "Copyright 2026 Acme. All rights reserved.")
            self.assertEqual(s_vsc, "vscode_settings")

    def test_template_omits_fields_not_in_template(self):
        """Confirm that if a field does not exist in template, it will be ignored and not injected."""
        import tempfile
        fixer = FixNd001()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpl_file = os.path.join(tmpdir, "header_template.txt")
            with open(tmpl_file, "w") as f:
                f.write("/******************************************************************************\n"
                        " * File:        ${filename}\n"
                        " * Description: ${description}\n"
                        " ******************************************************************************/\n")
            
            src_file = os.path.join(tmpdir, "minimal.sv")
            lines = ["module minimal;\n", "endmodule\n"]
            violation = {"file": src_file, "line": 1, "message": "Missing block comment file header"}
            config = {
                "agent": {
                    "custom_header_template": tmpl_file,
                    "header_company": "ShouldBeIgnored Corp",
                    "header_author": "ignored@example.com",
                    "header_legal": "Ignored Legal Notice"
                }
            }
            proposal = fixer.propose(violation, lines, config=config, overwrite_header=True)
            self.assertIsNotNone(proposal)
            rendered = "".join(proposal.patch_lines)
            self.assertIn("File:        minimal.sv", rendered)
            self.assertIn("Description:", rendered)
            # Ensure fields NOT in the template are NOT present in rendered header
            self.assertNotIn("Author:", rendered)
            self.assertNotIn("Company:", rendered)
            self.assertNotIn("Legal:", rendered)
            self.assertNotIn("ShouldBeIgnored", rendered)
            self.assertNotIn("ignored@example.com", rendered)

    def test_fix_nd001_placeholder_noop_skipped(self):
        """If resolved company is TODO_COMPANY and line already has TODO_COMPANY, proposal should be skipped."""
        import tempfile
        fixer = FixNd001()
        with tempfile.TemporaryDirectory() as tmpdir:
            src_file = os.path.join(tmpdir, "test.sv")
            sample_lines = [
                "/*\n",
                " * File:    test.sv\n",
                " * Company: TODO_COMPANY\n",
                " */\n"
            ]
            violation = {
                "file": src_file,
                "line": 3,
                "message": "File header Company field contains unresolved placeholder 'TODO_COMPANY'."
            }
            # Unconfigured company -> resolves to TODO_COMPANY -> replacement is identical -> no proposal
            proposal = fixer.propose(violation, sample_lines, config={})
            self.assertIsNone(proposal)


    def test_fix_nd001_missing_header_with_later_block_comments(self):
        """Ensure that block comments later in the file are not mistaken for a file header."""
        fixer = FixNd001()
        sample_lines = [
            "\n",
            "`ifndef FOO_SV\n",
            "`define FOO_SV\n",
            "/*\n",
            " * Later block comment\n",
            " */\n",
            "module foo;\n",
            "endmodule\n"
        ]
        violation = {
            "file": "foo.sv",
            "line": 2,
            "message": "Missing block comment file header (/* */). Every file must begin with a block comment header."
        }
        proposal = fixer.propose(violation, sample_lines)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.rule_id, "ND-001")
        self.assertEqual(proposal.line, 1)
        self.assertEqual(proposal.replace_range, (1, 1))
        joined = "".join(proposal.patch_lines)
        self.assertIn("File:        foo.sv", joined)


if __name__ == "__main__":
    unittest.main()
