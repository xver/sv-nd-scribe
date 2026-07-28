# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class ClassDocumentationRule(BaseRule):
    """
    [ND-009] Class Documentation Rule
    The class name MUST match the code identifier and have a preceding NaturalDocs comment.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-009]"

    @property
    def description(self) -> str:
        return "Class MUST have a preceding NaturalDocs comment matching class identifier."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # AST node driven check
        nodes = self._find_tree_nodes_by_tag(context, "kClassDeclaration")
        if nodes:
            for node in nodes:
                class_name = ""
                if hasattr(node, 'find_all'):
                    try:
                        id_nodes = list(node.find_all(lambda n: getattr(n, 'tag', '') == 'SymbolIdentifier'))
                        if id_nodes:
                            class_name = id_nodes[0].text
                    except Exception:
                        pass
                if not class_name:
                    text = getattr(node, 'text', '') or ""
                    m = re.search(r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)", text)
                    if m:
                        class_name = m.group(1)

                if class_name:
                    line = self._node_start_line(node, file_content, context)
                    comments = self._comments_before_node(node, file_content, context)
                    if not comments or not any("class" in c.lower() for c in comments):
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line,
                                message=f"Class '{class_name}' is missing NaturalDocs comment ('// Class: {class_name}')."
                            )
                        )
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            match = re.match(r"^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
            if match:
                class_name = match.group(1)
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments or not any("class" in c.lower() for c in comments):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Class '{class_name}' is missing NaturalDocs comment ('// Class: {class_name}')."
                        )
                    )

        return violations
