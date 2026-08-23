# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class VariableDocumentationRule(BaseRule):
    """
    [ND-023] Variable Documentation Rule
    Variable and interface instance declarations MUST have preceding NaturalDocs comments.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-023]"

    @property
    def description(self) -> str:
        return "Variable declarations and interface instances MUST have preceding NaturalDocs comments."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # AST node driven check
        data_nodes = self._find_tree_nodes_by_tag(context, "kDataDeclaration")
        if data_nodes:
            for node in data_nodes:
                parent = getattr(node, 'parent', None)
                in_excl = False
                p = parent
                while p is not None:
                    tag = getattr(p, 'tag', '')
                    if tag in {'kClockingDeclaration', 'kModportDeclaration', 'kFunctionDeclaration', 'kTaskDeclaration', 'kStructSpecifier', 'kUnionSpecifier', 'kStructUnionMember', 'kDataTypeStruct', 'kDataTypeUnion'}:
                        in_excl = True
                        break
                    p = getattr(p, 'parent', None)

                if in_excl:
                    continue

                text = getattr(node, 'text', '') or ""
                if any(kw in text for kw in ["typedef", "struct", "union", "enum"]):
                    continue

                vars_found = []
                if hasattr(node, 'find_all'):
                    vars_found = list(node.find_all(
                        lambda sub: getattr(sub, 'tag', '') in {'kVariableDeclarationAssignment', 'kRegisterVariable', 'kNetVariable'}
                    ))
                var_name = None
                if vars_found:
                    idents = list(vars_found[0].find_all(lambda sub: getattr(sub, 'tag', '') == 'SymbolIdentifier'))
                    if idents:
                        var_name = idents[0].text.strip()
                if not var_name:
                    m = re.search(
                        r"^\s*(?:(?:rand|randc|protected|local|static|const|virtual|automatic)\s+)*"
                        r"(?:(?:logic|bit|byte|shortint|int|longint|integer|time|shortreal|real|realtime|string|[a-zA-Z_][a-zA-Z0-9_]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)*)\s*)"
                        r"(?:\s*\[[^\]]+\])*\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                        text.strip()
                    )
                    if m:
                        var_name = m.group(1)

                if var_name and var_name not in ["module", "package", "class", "function", "task", "interface", "covergroup", "checker", "end", "begin", "assign", "property", "clocking", "modport"]:
                    line = self._node_start_line(node, file_content, context)
                    comments = self._comments_before_node(node, file_content, context)
                    if not comments:
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line,
                                message=f"Variable or instance '{var_name}' is missing documentation."
                            )
                        )
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        in_clocking = False
        in_modport = False
        in_struct = False
        in_function_or_task = False
        in_param_header = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                continue

            # Track struct/union/enum block scope
            if any(kw in stripped for kw in ["struct", "union", "enum"]) and "{" in stripped and not stripped.endswith("};"):
                in_struct = True
                continue
            if in_struct:
                if "}" in stripped:
                    in_struct = False
                continue

            # Track function / task body scope (skip local variables)
            if re.search(r"^\s*(?:pure\s+|virtual\s+|protected\s+|local\s+|static\s+|extern\s+|external\s+)*(?:function|task)\b", line):
                if not re.search(r"\b(extern|external|pure\s+virtual)\b", line):
                    in_function_or_task = True
                continue
            if stripped.startswith("endfunction") or stripped.startswith("endtask"):
                in_function_or_task = False
                continue

            # Track clocking block scope
            if stripped.startswith("clocking"):
                in_clocking = True
                continue
            if stripped.startswith("endclocking"):
                in_clocking = False
                continue

            # Track modport scope
            if stripped.startswith("modport"):
                if not stripped.endswith(";"):
                    in_modport = True
                continue
            if in_modport:
                if ";" in stripped:
                    in_modport = False
                continue

            # Track class / module parameter port list #(...)
            if re.search(r"\b(class|module|interface)\s+.*#\(", stripped) and not stripped.endswith(";"):
                in_param_header = True
                continue
            if in_param_header:
                if ";" in stripped:
                    in_param_header = False
                continue

            # Skip documentation requirements inside clocking, modport, struct/union/enum structures, function/task bodies, or parameter lists
            if in_clocking or in_modport or in_struct or in_function_or_task or in_param_header:
                continue

            # Skip typedef declarations (handled by ND-011) and return statements
            if stripped.startswith("typedef") or stripped.startswith(("return ", "return;", "return(")):
                continue

            # Skip non-variable SystemVerilog construct keywords
            first_word = stripped.split()[0] if stripped.split() else ""
            if first_word in [
                "modport", "clocking", "module", "package", "class", "interface", "function", "task",
                "covergroup", "checker", "property", "sequence", "import", "export",
                "initial", "always", "always_comb", "always_ff", "always_latch",
                "assign", "bind", "program", "constraint", "end", "begin", "endclocking",
                "input", "output", "inout", "ref", "default"
            ]:
                continue

            # Plain variable or interface instance (e.g. logic [31:0] addr; or nd_bus_if bus_if();)
            # Also matches parameter/localparam declarations.
            match = re.match(
                r"^\s*(?:rand\s+|randc\s+)?(?:parameter\s+|localparam\s+)?(?:logic|bit|int|byte|string|time|real|[a-zA-Z_][a-zA-Z0-9_]*)\s+(?:\[[^\]]+\]\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:;|=|\([^)]*\)\s*;)?",
                line
            )
            if match:
                var_name = match.group(1)
                if var_name in ["module", "package", "class", "function", "task", "interface", "covergroup", "checker", "end", "begin", "assign", "property", "clocking", "modport"]:
                    continue
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Variable or instance '{var_name}' is missing documentation."
                        )
                    )

        return violations
