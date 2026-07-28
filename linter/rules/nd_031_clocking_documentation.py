# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class ClockingDocumentationRule(BaseRule):
    """
    [ND-031] Clocking Block Documentation Rule
    Clocking block declarations MUST have a preceding NaturalDocs comment
    using the '//Clocking: <name>' keyword format.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-031]"

    @property
    def description(self) -> str:
        return "Clocking block declarations MUST have a preceding '//Clocking: <name>' NaturalDocs comment."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # AST node driven check
        nodes = self._find_tree_nodes_by_tag(context, "kClockingDeclaration")
        if nodes:
            for node in nodes:
                text = getattr(node, 'text', '') or ""
                m = re.search(r'\bclocking\s+([a-zA-Z_][a-zA-Z0-9_]*)', text)
                if not m:
                    lines_all = file_content.splitlines()
                    line_idx = line - 1
                    line_str = lines_all[line_idx] if 0 <= line_idx < len(lines_all) else ""
                    m_line = re.search(r'\bclocking\s+([a-zA-Z_][a-zA-Z0-9_]*)', line_str)
                    name = m_line.group(1) if m_line else "cb"
                else:
                    name = m.group(1)
                line = self._node_start_line(node, file_content, context)
                comments = self._comments_before_node(node, file_content, context)
                if not comments:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=line,
                            message=f"Clocking block '{name}' is missing a NaturalDocs comment ('//Clocking: {name}')."
                        )
                    )
                elif not self._has_naturaldocs_keyword(comments, ['Clocking', 'clocking']):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=line,
                            message=f"Clocking block '{name}' comment is missing the '//Clocking:' keyword."
                        )
                    )
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        pattern = re.compile(r'^\s*clocking\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*@')
        for i, line in enumerate(lines):
            m = pattern.match(line)
            if m:
                name = m.group(1)
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Clocking block '{name}' is missing a NaturalDocs comment ('//Clocking: {name}')."
                        )
                    )
                elif not self._has_naturaldocs_keyword(comments, ['Clocking', 'clocking']):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Clocking block '{name}' comment is missing the '//Clocking:' keyword."
                        )
                    )

        return violations
