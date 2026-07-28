# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class ExternImplementationRule(BaseRule):
    """
    [ND-030] Extern Implementation Rule
    Out-of-body implementation of an extern method MUST have preceding NaturalDocs comment.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-030]"

    @property
    def description(self) -> str:
        return "Extern method implementations outside class body MUST have preceding NaturalDocs comment."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # AST node driven check
        fn_nodes = self._find_tree_nodes_by_tag(context, "kFunctionDeclaration")
        task_nodes = self._find_tree_nodes_by_tag(context, "kTaskDeclaration")
        nodes = fn_nodes + task_nodes

        if nodes:
            for node in nodes:
                text = getattr(node, 'text', '') or ""
                match = re.search(r"(function|task)\s+(?:[a-zA-Z_0-9_]+\s+)?([a-zA-Z_][a-zA-Z0-9_]*::[a-zA-Z_][a-zA-Z0-9_]*)", text)
                if match:
                    method_name = match.group(2)
                    line = self._node_start_line(node, file_content, context)
                    comments = self._comments_before_node(node, file_content, context)
                    if not comments:
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line,
                                message=f"Extern method implementation '{method_name}' is missing documentation comment."
                            )
                        )
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            match = re.match(r"^\s*(function|task)\s+(?:[a-zA-Z_0-9_]+\s+)?([a-zA-Z_][a-zA-Z0-9_]*::[a-zA-Z_][a-zA-Z0-9_]*)", line)
            if match:
                method_name = match.group(2)
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Extern method implementation '{method_name}' is missing documentation comment."
                        )
                    )

        return violations
