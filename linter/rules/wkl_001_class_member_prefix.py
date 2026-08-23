# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import List, Any
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class ClassMemberPrefixRule(BaseRule):
    """
    [WKL-001] Class Member Prefix Rule
    Checks that class members have the 'm_' or 'is_' prefix, with standard exceptions.
    Uses purely Verible AST syntax tree parsing.
    """

    @property
    def rule_id(self) -> str:
        return "[WKL-001]"

    @property
    def description(self) -> str:
        return "Class members should have 'm_' prefix (with exceptions)."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        EXCEPTIONS = {'is_active', 'coverage_enable', 'checks_enable', 'regmodel'}

        # AST node driven check only
        class_nodes = self._find_tree_nodes_by_tag(context, "kClassDeclaration")
        if not class_nodes:
            return []

        for class_node in class_nodes:
            data_nodes = []
            if hasattr(class_node, 'find_all'):
                try:
                    data_nodes = list(class_node.find_all(lambda n: getattr(n, 'tag', '') == 'kDataDeclaration'))
                except Exception:
                    pass

            for dnode in data_nodes:
                text = getattr(dnode, 'text', '') or ""
                # Exclude non-variable member constructs (typedef, methods, covergroups, constraints, parameters, etc.)
                if re.search(r"\b(typedef|function|task|const|covergroup|coverpoint|constraint|cross|localparam|parameter|checker|property|sequence|import|export)\b", text):
                    continue

                vars_found = []
                if hasattr(dnode, 'find_all'):
                    vars_found = list(dnode.find_all(
                        lambda sub: getattr(sub, 'tag', '') in {'kVariableDeclarationAssignment', 'kRegisterVariable', 'kNetVariable'}
                    ))

                if vars_found:
                    for v in vars_found:
                        v_text = getattr(v, 'text', '').strip()
                        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)", v_text)
                        var_name = m.group(1) if m else v_text.split("=")[0].split("[")[0].strip()
                        if self._is_invalid_member_name(var_name, EXCEPTIONS):
                            line = self._node_start_line(dnode, file_content, context)
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line,
                                    message=f"Class member '{var_name}' does not have required 'm_' prefix."
                                )
                            )
                else:
                    m = re.match(
                        r"^\s*(?:(?:rand|randc|protected|local|static|const|virtual|automatic)\s+)*"
                        r"(?:(?:logic|bit|byte|shortint|int|longint|integer|time|shortreal|real|realtime|string|[a-zA-Z_][a-zA-Z0-9_]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)*)\s*)"
                        r"(?:\s*\[[^\]]+\])*\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                        text.strip()
                    )
                    if m:
                        var_name = m.group(1)
                        if self._is_invalid_member_name(var_name, EXCEPTIONS):
                            line = self._node_start_line(dnode, file_content, context)
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line,
                                    message=f"Class member '{var_name}' does not have required 'm_' prefix."
                                )
                            )

        return violations

    def _is_invalid_member_name(self, var_name: str, exceptions: set) -> bool:
        if not var_name:
            return False
        if var_name in exceptions:
            return False
        if var_name.startswith("m_") or var_name.startswith("is_"):
            return False
        if var_name.endswith('_port') or var_name.endswith('_export') or var_name == 'vif' or var_name.endswith('_vif'):
            return False
        return True
