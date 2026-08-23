# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class DocumentedStatementRule(BaseRule):
    """
    [ND-004] Documented Statement Rule
    Every documentable SystemVerilog statement MUST have a NaturalDocs comment block preceding it (blank lines permitted).
    """

    @property
    def rule_id(self) -> str:
        return "[ND-004]"

    @property
    def description(self) -> str:
        return "Every documentable SystemVerilog statement MUST have a NaturalDocs comment block preceding it."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # AST node driven check
        tags = [
            "kClassDeclaration", "kPackageDeclaration", "kInterfaceDeclaration", "kModuleDeclaration",
            "kFunctionDeclaration", "kTaskDeclaration", "kFunctionPrototype", "kTaskPrototype",
            "kClassConstructorDeclaration", "kClassConstructorPrototype"
        ]
        has_ast = False
        for tag in tags:
            nodes = self._find_tree_nodes_by_tag(context, tag)
            if nodes:
                has_ast = True
                for node in nodes:
                    text = getattr(node, 'text', '') or ""
                    first_l = text.splitlines()[0].strip() if text else tag
                    if tag in ["kFunctionDeclaration", "kTaskDeclaration", "kFunctionPrototype", "kTaskPrototype", "kClassConstructorDeclaration", "kClassConstructorPrototype"] and "::" in first_l:
                        continue

                    comment_lines = self._comments_before_node(node, file_content, context)
                    if not comment_lines:
                        line = self._node_start_line(node, file_content, context)
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line,
                                message=f"Documented statement '{first_l}' is missing a preceding NaturalDocs comment block."
                            )
                        )
        if has_ast:
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        for i, line_str in enumerate(lines):
            stripped = line_str.strip()
            if any(stripped.startswith(kw) for kw in [
                "class ", "package ", "interface ", "module ", "function ", "task ",
                "extern function ", "extern task ", "virtual function ", "virtual task ",
                "protected function ", "protected task ", "local function ", "local task ",
                "pure virtual function ", "pure virtual task "
            ]):
                if "::" in stripped:
                    continue
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Documented statement '{stripped}' is missing a preceding NaturalDocs comment block."
                        )
                    )

        return violations
