# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class InterfaceDocumentationRule(BaseRule):
    """
    [ND-013] Interface Documentation Rule
    Interface declaration MUST have a preceding NaturalDocs comment.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-013]"

    @property
    def description(self) -> str:
        return "Interface declaration MUST have a preceding NaturalDocs comment."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # AST node driven check
        nodes = self._find_tree_nodes_by_tag(context, "kInterfaceDeclaration")
        if nodes:
            for node in nodes:
                intf_name = ""
                if hasattr(node, 'find_all'):
                    try:
                        id_nodes = list(node.find_all(lambda n: getattr(n, 'tag', '') == 'SymbolIdentifier'))
                        if id_nodes:
                            intf_name = id_nodes[0].text
                    except Exception:
                        pass
                if not intf_name:
                    text = getattr(node, 'text', '') or ""
                    m = re.search(r"interface\s+([a-zA-Z_][a-zA-Z0-9_]*)", text)
                    if m:
                        intf_name = m.group(1)

                if intf_name:
                    line = self._node_start_line(node, file_content, context)
                    comments = self._comments_before_node(node, file_content, context)
                    if not comments or not any("interface" in c.lower() for c in comments):
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line,
                                message=f"Interface '{intf_name}' is missing preceding NaturalDocs documentation."
                            )
                        )
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            match = re.match(r"^\s*interface\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
            if match:
                intf_name = match.group(1)
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments or not any("interface" in c.lower() for c in comments):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Interface '{intf_name}' is missing preceding NaturalDocs documentation."
                        )
                    )

        return violations
