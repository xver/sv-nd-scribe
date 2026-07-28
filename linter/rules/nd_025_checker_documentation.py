# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class CheckerDocumentationRule(BaseRule):
    """
    [ND-026] Checker Documentation Rule
    Checker constructs MUST have preceding NaturalDocs comments.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-025]"

    @property
    def description(self) -> str:
        return "Checker constructs MUST have preceding NaturalDocs comments."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        import re
        violations = []
        nodes = self._find_tree_nodes_by_tag(context, "kCheckerDeclaration")
        if nodes:
            for node in nodes:
                name = ""
                text = getattr(node, 'text', '') or ""
                m = re.search(r"checker\s+([a-zA-Z_][a-zA-Z0-9_]*)", text)
                if m:
                    name = m.group(1)
                line = self._node_start_line(node, file_content, context)
                comments = self._comments_before_node(node, file_content, context)
                has_kw = False
                if comments:
                    for c in comments:
                        if re.search(r"^\s*(?://|/\*|\*|)\s*checker\s*:", c, re.IGNORECASE):
                            has_kw = True
                            break
                if not has_kw:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=line,
                            message=f"Checker '{name}' is missing preceding NaturalDocs comment ('// Checker: {name}')."
                        )
                    )
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            match = re.match(r"^\s*checker\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
            if match:
                name = match.group(1)
                comments = self._extract_comments_from_text(file_content, i + 1)
                has_kw = False
                if comments:
                    for c in comments:
                        if re.search(r"^\s*(?://|/\*|\*|)\s*checker\s*:", c, re.IGNORECASE):
                            has_kw = True
                            break
                if not has_kw:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Checker '{name}' is missing preceding NaturalDocs comment ('// Checker: {name}')."
                        )
                    )

        return violations
