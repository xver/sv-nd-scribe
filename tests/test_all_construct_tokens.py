import unittest
from agent.fixer.rules.fix_nd028_assign_doc import FixNd028
from agent.fixer.rules.fix_nd023_variable_doc import FixNd023
from agent.fixer.rules.fix_nd017_function_task import FixNd017
from agent.fixer.rules.fix_nd009_class import FixNd009
from agent.fixer.rules.fix_nd014_module import FixNd014
from agent.fixer.rules.fix_nd013_interface_doc import FixNd013
from agent.fixer.rules.fix_nd010_enum_doc import FixNd010
from agent.fixer.rules.fix_nd011_type_doc import FixNd011
from agent.fixer.rules.fix_nd020_constraint_doc import FixNd020
from agent.fixer.rules.fix_nd021_covergroup_doc import FixNd021
from agent.fixer.rules.fix_nd022_coverpoint_doc import FixNd022
from agent.fixer.rules.fix_nd026_bind_doc import FixNd026
from agent.fixer.rules.fix_nd031_clocking_doc import FixNd031
from agent.fixer.rules.fix_nd032_modport_doc import FixNd032
from agent.fixer.rules.fix_nd004_documented_stmt import FixNd004
from agent.fixer.rules.fix_nd019_identifier_match import FixNd019


class TestAllFixerTokens(unittest.TestCase):

    def test_fix_nd028_assign_token(self):
        fixer = FixNd028()
        v = {"rule": "ND-028", "file": "test.sv", "line": 1, "message": "Continuous assignment ('assign') is missing preceding NaturalDocs comment."}
        lines = ["  assign a = b;\n"]
        p = fixer.propose(v, lines)
        self.assertIsNotNone(p)
        self.assertIn("// Assign: a\n", p.patch_lines[0])
        self.assertNotIn("Assign: assign", p.patch_lines[0])

    def test_fix_nd028_assign_complex(self):
        fixer = FixNd028()
        v = {"rule": "ND-028", "file": "test.sv", "line": 1}
        lines = ["  assign (strong1, pull0) #5 out_data = in_data;\n"]
        p = fixer.propose(v, lines)
        self.assertIsNotNone(p)
        self.assertIn("// Assign: out_data\n", p.patch_lines[0])

    def test_fix_nd019_mismatch_assign(self):
        fixer = FixNd019()
        v = {"rule": "ND-019", "file": "test.sv", "line": 1, "message": "Documented identifier 'assign' does not match code identifier 'a'."}
        lines = ["  // Assign: assign\n", "  // Description\n", "  assign a = b;\n"]
        p = fixer.propose(v, lines)
        self.assertIsNotNone(p)
        self.assertIn("// Assign: a\n", p.patch_lines[0])

    def test_fix_nd023_variable_tokens(self):
        fixer = FixNd023()
        test_cases = [
            ("wire a;\n", "a"),
            ("logic [31:0] data_bus;\n", "data_bus"),
            ("rand bit [7:0] payload;\n", "payload"),
            ("nd_driver m_driver;\n", "m_driver"),
            ("int count = 0;\n", "count"),
        ]
        for line, expected_name in test_cases:
            v = {"rule": "ND-023", "file": "test.sv", "line": 1}
            p = fixer.propose(v, [line])
            self.assertIsNotNone(p, f"Failed for line: {line}")
            self.assertIn(f"// Variable: {expected_name}\n", p.patch_lines[0])

    def test_fix_nd017_function_tokens_and_params(self):
        fixer = FixNd017()
        v = {"rule": "ND-017", "file": "test.sv", "line": 1}
        lines = ["  function new(string name = \"nd_monitor\", uvm_component parent = null);\n"]
        p = fixer.propose(v, lines)
        self.assertIsNotNone(p)
        self.assertIn("// Function: new\n", p.patch_lines[0])
        self.assertIn("name - Description for name", p.patch_lines[0])
        self.assertIn("parent - Description for parent", p.patch_lines[0])
        self.assertNotIn("nd_monitor", p.patch_lines[0])
        self.assertNotIn("null", p.patch_lines[0])

    def test_fix_nd009_parameterized_class(self):
        fixer = FixNd009()
        v = {"rule": "ND-009", "file": "test.sv", "line": 1}
        lines = [
            "class nd_param_driver #(\n",
            "    type REQ_T = uvm_sequence_item,\n",
            "    type RSP_T = REQ_T,\n",
            "    int DATA_WIDTH = 32\n",
            ") extends uvm_driver #(REQ_T, RSP_T);\n"
        ]
        p = fixer.propose(v, lines)
        self.assertIsNotNone(p)
        self.assertIn("// Class: nd_param_driver\n", p.patch_lines[0])
        self.assertIn("Parameters:\n", p.patch_lines[0])
        self.assertIn("REQ_T - Description for REQ_T", p.patch_lines[0])
        self.assertIn("RSP_T - Description for RSP_T", p.patch_lines[0])
        self.assertIn("DATA_WIDTH - Description for DATA_WIDTH", p.patch_lines[0])

    def test_fix_nd013_interface_params_and_ports(self):
        fixer = FixNd013()
        v = {"rule": "ND-013", "file": "test.sv", "line": 1}
        lines = [
            "interface nd_bus_interface #(\n",
            "    int ADDR_WIDTH = 32,\n",
            "    int DATA_WIDTH = 32\n",
            ") (\n",
            "    input logic clk,\n",
            "    input logic rst_n\n",
            ");\n"
        ]
        p = fixer.propose(v, lines)
        self.assertIsNotNone(p)
        self.assertIn("// Interface: nd_bus_interface\n", p.patch_lines[0])
        self.assertIn("Parameters:\n", p.patch_lines[0])
        self.assertIn("ADDR_WIDTH - Description for ADDR_WIDTH", p.patch_lines[0])
        self.assertIn("Ports:\n", p.patch_lines[0])
        self.assertIn("clk - Description for clk", p.patch_lines[0])
        self.assertIn("rst_n - Description for rst_n", p.patch_lines[0])

    def test_fix_nd014_module_params_and_ports(self):
        fixer = FixNd014()
        v = {"rule": "ND-014", "file": "test.sv", "line": 1}
        lines = [
            "module nd_alu #(\n",
            "    parameter int DATA_WIDTH = 32\n",
            ") (\n",
            "    input logic clk,\n",
            "    output logic [DATA_WIDTH-1:0] result\n",
            ");\n"
        ]
        p = fixer.propose(v, lines)
        self.assertIsNotNone(p)
        self.assertIn("// Module: nd_alu\n", p.patch_lines[0])
        self.assertIn("Parameters:\n", p.patch_lines[0])
        self.assertIn("DATA_WIDTH - Description for DATA_WIDTH", p.patch_lines[0])
        self.assertIn("Ports:\n", p.patch_lines[0])
        self.assertIn("clk - Description for clk", p.patch_lines[0])
        self.assertIn("result - Description for result", p.patch_lines[0])

    def test_fix_nd004_various_constructs(self):
        fixer = FixNd004()
        cases = [
            ("function void build_phase(uvm_phase phase);\n", "Function: build_phase"),
            ("task run_phase(uvm_phase phase);\n", "Task: run_phase"),
            ("class nd_driver extends uvm_driver;\n", "Class: nd_driver"),
            ("module nd_top_wrapper;\n", "Module: nd_top_wrapper"),
            ("interface nd_bus_if;\n", "Interface: nd_bus_if"),
        ]
        for line, expected_tag_name in cases:
            v = {"rule": "ND-004", "file": "test.sv", "line": 1}
            p = fixer.propose(v, [line])
            self.assertIsNotNone(p, f"Failed for line: {line}")
            self.assertIn(f"// {expected_tag_name}\n", p.patch_lines[0])


if __name__ == "__main__":
    unittest.main()
