# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class InterfaceNamingRule(BaseRule):
    """
    [WKL-004] Interface Naming Rule
    Interface declarations MUST end with '_if' suffix.
    """

    @property
    def rule_id(self) -> str:
        return "[WKL-004]"

    @property
    def description(self) -> str:
        return "Interface declarations MUST end with '_if' suffix."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # AST node driven check
        nodes = self._find_tree_nodes_by_tag(context, "kInterfaceDeclaration")
        if nodes:
            for node in nodes:
                intf_name = ""
                text = getattr(node, 'text', '') or ""
                m = re.search(r"interface\s+([a-zA-Z_][a-zA-Z0-9_]*)", text)
                if m:
                    intf_name = m.group(1)
                if intf_name and not intf_name.endswith("_if"):
                    line = self._node_start_line(node, file_content, context)
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=line,
                            message=f"Interface '{intf_name}' must end with '_if' suffix."
                        )
                    )
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            match = re.match(r"^\s*interface\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
            if match:
                intf_name = match.group(1)
                if not intf_name.endswith("_if"):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Interface '{intf_name}' must end with '_if' suffix."
                        )
                    )

        return violations
