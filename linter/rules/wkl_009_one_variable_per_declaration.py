# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class OneVariablePerDeclarationRule(BaseRule):
    """
    [WKL-009] One Variable Per Declaration Rule
    Each data/net declaration statement must declare only one variable.
    """

    @property
    def rule_id(self) -> str:
        return "[WKL-009]"

    @property
    def description(self) -> str:
        return "Each data/net declaration statement must declare only one variable."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # 1. AST node driven check using Verible AST
        data_nodes = self._find_tree_nodes_by_tag(context, "kDataDeclaration")
        net_nodes = self._find_tree_nodes_by_tag(context, "kNetDeclaration")
        decl_nodes = data_nodes + net_nodes

        if decl_nodes:
            for node in decl_nodes:
                # Exclude type declarations, typedefs, or package imports
                parent = getattr(node, 'parent', None)
                is_excluded = False
                p = parent
                while p is not None:
                    if getattr(p, 'tag', '') in {'kTypeDeclaration', 'kPackageImportDeclaration'}:
                        is_excluded = True
                        break
                    p = getattr(p, 'parent', None)
                if is_excluded:
                    continue

                text = getattr(node, 'text', '') or ""
                if text.strip().startswith("typedef"):
                    continue

                # Find all declared variable subnodes in this declaration
                vars_found = []
                if hasattr(node, 'find_all'):
                    vars_found = list(node.find_all(
                        lambda sub: getattr(sub, 'tag', '') in {'kRegisterVariable', 'kNetVariable', 'kVariableDeclarationAssignment'}
                    ))

                if len(vars_found) > 1:
                    var_names = []
                    for v in vars_found:
                        v_text = getattr(v, 'text', '').strip()
                        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)", v_text)
                        if m:
                            var_names.append(m.group(1))
                        else:
                            var_names.append(v_text.split("=")[0].split("[")[0].strip())

                    var_list_str = ", ".join(var_names) if var_names else text.strip()
                    line = self._node_start_line(node, file_content, context)
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=line,
                            message=f"Multiple variables declared in a single statement ('{var_list_str}'). Declare each variable on a separate statement."
                        )
                    )
            return violations

        # 2. Fallback text parsing (when Verible AST is unavailable)
        lines = file_content.splitlines()

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                continue

            if stripped.startswith("typedef"):
                continue

            # Skip construct definitions and headers
            if stripped.startswith(("module", "interface", "function", "task", "import", "export", "class", "package", "covergroup", "checker", "property", "sequence", "macromodule", "program")):
                continue

            code_part = stripped.split("//")[0].split("/*")[0].strip()
            if not code_part.endswith(";"):
                continue

            m = re.match(
                r"^(?:rand\s+|randc\s+|const\s+|static\s+|automatic\s+|local\s+|protected\s+|public\s+)*"
                r"(?:wire|tri|tri0|tri1|wand|wor|supply0|supply1|logic|bit|int|integer|byte|shortint|longint|time|shortreal|real|realtime|string|[a-zA-Z_][a-zA-Z0-9_]*)"
                r"(?:\s*\[[^\]]+\])*\s+(.+);$",
                code_part
            )
            if m:
                rest = m.group(1).strip()
                vars_in_line = []
                current = []
                depth = 0
                for ch in rest:
                    if ch in "([{'\"":
                        depth += 1
                        current.append(ch)
                    elif ch in ")]}'\"":
                        depth -= 1
                        current.append(ch)
                    elif ch == "," and depth == 0:
                        vars_in_line.append("".join(current).strip())
                        current = []
                    else:
                        current.append(ch)
                if current:
                    vars_in_line.append("".join(current).strip())

                if len(vars_in_line) > 1:
                    var_names = [v.split("=")[0].split("[")[0].strip() for v in vars_in_line]
                    var_list_str = ", ".join(var_names)
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Multiple variables declared in a single statement ('{var_list_str}'). Declare each variable on a separate statement."
                        )
                    )

        return violations
