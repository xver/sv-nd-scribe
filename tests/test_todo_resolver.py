# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os
import tempfile
import unittest
from agent.fixer.todo_resolver import TodoResolver


class TestTodoResolver(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_temp_file(self, content: str) -> str:
        fpath = os.path.join(self.temp_dir.name, "test_sample.sv")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        return fpath

    def test_resolve_targeted_line(self):
        content = (
            "class tb_env extends uvm_env;\n"
            "  // Variable: cfg\n"
            "  // TODO [SVND]: Add description for variable 'cfg'\n"
            "  tb_config cfg;\n"
            "\n"
            "  // Function: build_phase\n"
            "  // TODO [SVND]: Add description for function 'build_phase'\n"
            "  function void build_phase(uvm_phase phase);\n"
            "  endfunction\n"
            "endclass\n"
        )
        fpath = self._create_temp_file(content)
        resolver = TodoResolver()

        # Target line 3 (cfg)
        res = resolver.resolve_file(fpath, target_line=3, no_backup=True)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["resolved_count"], 1)

        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Line 3 should now have description and NO "TODO [SVND]"
        self.assertNotIn("TODO [SVND]", lines[2])
        self.assertIn("cfg", lines[2])

        # Line 7 should still have its TODO [SVND] marker
        self.assertIn("TODO [SVND]", lines[6])

    def test_resolve_all_markers(self):
        content = (
            "class tb_env extends uvm_env;\n"
            "  // Variable: cfg\n"
            "  // TODO [SVND]: Add description for variable 'cfg'\n"
            "  tb_config cfg;\n"
            "\n"
            "  // Function: build_phase\n"
            "  // TODO [SVND]: Add description for function 'build_phase'\n"
            "  function void build_phase(uvm_phase phase);\n"
            "  endfunction\n"
            "endclass\n"
        )
        fpath = self._create_temp_file(content)
        resolver = TodoResolver()

        # No target line resolves all
        res = resolver.resolve_file(fpath, target_line=None, no_backup=True)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["resolved_count"], 2)

        with open(fpath, "r", encoding="utf-8") as f:
            new_content = f.read()

        self.assertNotIn("TODO [SVND]", new_content)
        self.assertIn("build_phase", new_content)

    def test_resolve_nearest_line(self):
        content = (
            "class tb_env extends uvm_env;\n"
            "  // Function: build_phase\n"
            "  // TODO [SVND]: Add description for function 'build_phase'\n"
            "  function void build_phase(uvm_phase phase);\n"
            "  endfunction\n"
            "endclass\n"
        )
        fpath = self._create_temp_file(content)
        resolver = TodoResolver()

        # Target line 4 (code line), cursor is on the function definition
        res = resolver.resolve_file(fpath, target_line=4, no_backup=True)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["resolved_count"], 1)

        with open(fpath, "r", encoding="utf-8") as f:
            new_content = f.read()

        self.assertNotIn("TODO [SVND]", new_content)

    def test_resolve_dry_run(self):
        content = (
            "// Class: packet\n"
            "// TODO [SVND]: Add description for class 'packet'\n"
            "class packet;\n"
            "endclass\n"
        )
        fpath = self._create_temp_file(content)
        resolver = TodoResolver()

        res = resolver.resolve_file(fpath, target_line=2, no_backup=True, dry_run=True)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["resolved_count"], 1)

        # File on disk should remain unmodified
        with open(fpath, "r", encoding="utf-8") as f:
            disk_content = f.read()
        self.assertEqual(disk_content, content)

    def test_no_markers_clean_status(self):
        content = (
            "// Class: packet\n"
            "// Network packet transaction.\n"
            "class packet;\n"
            "endclass\n"
        )
        fpath = self._create_temp_file(content)
        resolver = TodoResolver()

        res = resolver.resolve_file(fpath, target_line=2, no_backup=True)
        self.assertEqual(res["status"], "clean")
        self.assertEqual(res["resolved_count"], 0)

    def test_resolve_rejects_and_replaces_description_for_item(self):
        content = (
            "class tb_env extends uvm_env;\n"
            "  // Variable: cfg\n"
            "  // Description for variable 'cfg'\n"
            "  tb_config cfg;\n"
            "endclass\n"
        )
        fpath = self._create_temp_file(content)
        resolver = TodoResolver()

        res = resolver.resolve_file(fpath, target_line=3, no_backup=True)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["resolved_count"], 1)

        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.assertNotIn("Description for", lines[2])
        self.assertIn("Configuration object for cfg.", lines[2])

    def test_resolve_process_block_never_uses_item_boilerplate(self):
        content = (
            "interface tb_template_abs_agent0_link_if;\n"
            "  // Process: item\n"
            "  // TODO [SVND]: Add description for process 'item'\n"
            "  initial begin\n"
            "    `uvm_info(\"TB_TEMPLATE_ABS_AGENT0_LINK_IF\", \"START ABS_AGENT0 connect\", UVM_HIGH);\n"
            "    tb_template_sys_get_m_config(m_config);\n"
            "    if (m_config.m_connection[tb_template_defines_dv_pkg::TB_TEMPLATE_ABS_AGENT0] == CONNECT_ACTIVE) begin\n"
            "      m_config.m_abs_agent0_config.set_vif(top_tb.th.top_if.m_tb_template_if.m_abs_agent0_if);\n"
            "    end\n"
            "  end\n"
            "endinterface\n"
        )
        fpath = self._create_temp_file(content)
        resolver = TodoResolver()

        res = resolver.resolve_file(fpath, target_line=3, no_backup=True)
        self.assertEqual(res["status"], "success")

        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Both the tag line and description line must NEVER contain "item"
        self.assertNotIn("// Process: item", lines[1])
        self.assertIn("Process: abs_agent0_connect", lines[1])
        self.assertNotIn("definition for item", "".join(lines))
        self.assertIn("virtual interface", "".join(lines))
        # Verify comment lines stay below 80 characters
        for line in lines:
            if line.strip().startswith("//"):
                self.assertLessEqual(len(line.rstrip("\r\n")), 80)

    def test_resolve_hierarchical_assign_never_uses_tb_if_boilerplate(self):
        content = (
            "module tb_template_dummy_dut;\n"
            "  // Assign: tb_if\n"
            "  // TODO [SVND]: Add description for assignment 'tb_if'\n"
            "  assign tb_if.m_abs_agent1_if.ready = 1'b1;\n"
            "endmodule\n"
        )
        fpath = self._create_temp_file(content)
        resolver = TodoResolver()

        res = resolver.resolve_file(fpath, target_line=3, no_backup=True)
        self.assertEqual(res["status"], "success")

        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Identifier must be updated from tb_if to full hierarchical path
        self.assertNotIn("// Assign: tb_if\n", lines[1])
        self.assertIn("Assign: tb_if.m_abs_agent1_if.ready", lines[1])
        # Description must NOT be common-sense boilerplate
        self.assertNotIn("definition for tb if", lines[2])
        self.assertIn("ready handshake", lines[2])

    def test_resolve_replaces_existing_definition_for_tb_if(self):
        content = (
            "module tb_template_dummy_dut;\n"
            "  // Assign: tb_if\n"
            "  //   SystemVerilog assignment definition for tb if.\n"
            "  assign tb_if.m_abs_agent1_if.ready = 1'b1;\n"
            "endmodule\n"
        )
        fpath = self._create_temp_file(content)
        resolver = TodoResolver()

        res = resolver.resolve_file(fpath, target_line=3, no_backup=True)
        self.assertEqual(res["status"], "success")

        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.assertNotIn("SystemVerilog assignment definition for tb if.", lines[2])
        self.assertIn("ready handshake", lines[2])
        self.assertIn("Assign: tb_if.m_abs_agent1_if.ready", lines[1])

    def test_resolve_interface_container_block_comment_never_uses_element_boilerplate(self):
        content = (
            "/*\n"
            "  Interface: tb_template_if\n"
            "  SystemVerilog element definition for tb template if.\n"
            "*/\n"
            "interface tb_template_if(input logic clk_i);\n"
            "  tb_template_abs_agent0_link_if m_abs_agent0_link_if();\n"
            "endinterface : tb_template_if\n"
        )
        fpath = self._create_temp_file(content)
        resolver = TodoResolver()

        res = resolver.resolve_file(fpath, target_line=3, no_backup=True)
        self.assertEqual(res["status"], "success")

        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.assertNotIn("element definition", "".join(lines))
        self.assertNotIn("SystemVerilog element definition for tb template if.", "".join(lines))
        self.assertIn("Top-level project interface container bundling abstract agent pin", "".join(lines))
        # Ensure all comment lines strictly <= 80 characters
        for line in lines:
            if line.strip().startswith("//") or "/*" in line or "*/" in line or line.startswith("  "):
                self.assertLessEqual(len(line.rstrip("\r\n")), 80)


if __name__ == "__main__":
    unittest.main()


