# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class ProgramDocumentationRule(BaseRule):
    """
    [ND-030] Program Documentation Rule
    Testbench program blocks MUST have preceding NaturalDocs comments.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-029]"

    @property
    def description(self) -> str:
        return "Testbench program blocks MUST have preceding NaturalDocs comments."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        import re
        violations = []
        nodes = self._find_tree_nodes_by_tag(context, "kProgramDeclaration")
        if nodes:
            for node in nodes:
                name = ""
                text = getattr(node, 'text', '') or ""
                m = re.search(r"program\s+([a-zA-Z_][a-zA-Z0-9_]*)", text)
                if m:
                    name = m.group(1)
                line = self._node_start_line(node, file_content, context)
                comments = self._comments_before_node(node, file_content, context)
                if not comments or not any("program" in c.lower() for c in comments):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=line,
                            message=f"Program '{name}' is missing preceding NaturalDocs comment."
                        )
                    )
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        pattern = re.compile(r'^\s*program\s+([a-zA-Z_][a-zA-Z0-9_]*)')
        for i, line in enumerate(lines):
            m = pattern.match(line)
            if m:
                name = m.group(1)
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments or not any("program" in c.lower() for c in comments):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Program '{name}' is missing preceding NaturalDocs comment."
                        )
                    )
        return violations
