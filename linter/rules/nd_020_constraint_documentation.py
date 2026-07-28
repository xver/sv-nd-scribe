# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class ConstraintDocumentationRule(BaseRule):
    """
    [ND-020] Constraint Documentation Rule
    Constraint blocks MUST have preceding NaturalDocs comments.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-020]"

    @property
    def description(self) -> str:
        return "Constraint blocks MUST have preceding NaturalDocs comments."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # AST node driven check
        nodes = self._find_tree_nodes_by_tag(context, "kConstraintDeclaration")
        if nodes:
            for node in nodes:
                name = ""
                if hasattr(node, 'find_all'):
                    try:
                        id_nodes = list(node.find_all(lambda n: getattr(n, 'tag', '') == 'SymbolIdentifier'))
                        if id_nodes:
                            name = id_nodes[0].text
                    except Exception:
                        pass
                if not name:
                    text = getattr(node, 'text', '') or ""
                    m = re.search(r"constraint\s+([a-zA-Z_][a-zA-Z0-9_]*)", text)
                    if m:
                        name = m.group(1)

                if name:
                    line = self._node_start_line(node, file_content, context)
                    comments = self._comments_before_node(node, file_content, context)
                    if not comments or not any("constraint" in c.lower() for c in comments):
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line,
                                message=f"Constraint '{name}' is missing preceding NaturalDocs comment."
                            )
                        )
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            match = re.match(r"^\s*constraint\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
            if match:
                name = match.group(1)
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments or not any("constraint" in c.lower() for c in comments):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Constraint '{name}' is missing preceding NaturalDocs comment."
                        )
                    )

        return violations
