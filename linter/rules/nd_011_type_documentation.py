# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class TypeDocumentationRule(BaseRule):
    """
    [ND-011] Type Documentation Rule
    Typedef declarations MUST have a preceding NaturalDocs comment.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-011]"

    @property
    def description(self) -> str:
        return "Typedef declarations MUST have a preceding NaturalDocs comment."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # AST node driven check
        has_ast = context is not None and getattr(context, 'tree', None) is not None
        if has_ast:
            type_nodes = self._find_tree_nodes_by_tag(context, "kTypeDeclaration")
            for node in type_nodes:
                text = getattr(node, 'text', '') or ""
                if "enum" not in text:
                    comments = self._comments_before_node(node, file_content, context)
                    if not comments:
                        line = self._node_start_line(node, file_content, context)
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line,
                                message="Typedef declaration is missing preceding NaturalDocs documentation."
                            )
                        )
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("typedef") and "enum" not in stripped:
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message="Typedef declaration is missing preceding NaturalDocs documentation."
                        )
                    )

        return violations
