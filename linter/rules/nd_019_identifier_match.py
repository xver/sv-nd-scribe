# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class IdentifierMatchRule(BaseRule):
    """
    [ND-019] Identifier Match Rule
    The identifier in a NaturalDocs comment MUST match the code identifier.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-019]"

    @property
    def description(self) -> str:
        return "The identifier in a NaturalDocs comment MUST match the code identifier."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        tag_to_keyword = {
            "kClassDeclaration": "class",
            "kPackageDeclaration": "package",
            "kInterfaceDeclaration": "interface",
            "kModuleDeclaration": "module",
            "kFunctionDeclaration": "function",
            "kTaskDeclaration": "task",
            "kCovergroupDeclaration": "covergroup",
            "kCheckerDeclaration": "checker",
            "kClockingDeclaration": "clocking",
            "kModportDeclaration": "modport"
        }

        # AST node driven check
        has_ast = False
        for tag, c_kw in tag_to_keyword.items():
            nodes = self._find_tree_nodes_by_tag(context, tag)
            if nodes:
                has_ast = True
                for node in nodes:
                    text = getattr(node, 'text', '') or ""
                    m = re.search(r"\b" + c_kw + r"\s+([a-zA-Z_][a-zA-Z0-9_]*)", text)
                    if m:
                        actual_name = m.group(1)

                    if actual_name:
                        line = self._node_start_line(node, file_content, context)
                        comments = self._comments_before_node(node, file_content, context)
                        if comments:
                            doc_name = self._extract_documented_name(comments, [c_kw.capitalize(), c_kw])
                            if doc_name and doc_name != actual_name:
                                violations.append(
                                    self.create_violation(
                                        file_path=file_path,
                                        line=line,
                                        message=f"Documented identifier '{doc_name}' does not match code identifier '{actual_name}'."
                                    )
                                )

        if has_ast:
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        constructs = ["class", "package", "interface", "module", "function", "task", "covergroup", "checker", "modport", "clocking"]
        for i, line in enumerate(lines):
            for c in constructs:
                match = re.match(r"^\s*" + c + r"\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
                if match:
                    actual_name = match.group(1)
                    comments = self._extract_comments_from_text(file_content, i + 1)
                    if comments:
                        doc_name = self._extract_documented_name(comments, [c.capitalize(), c])
                        if doc_name and doc_name != actual_name:
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=i + 1,
                                    message=f"Documented identifier '{doc_name}' does not match code identifier '{actual_name}'."
                                )
                            )

        return violations
