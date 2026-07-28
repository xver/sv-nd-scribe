# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class InlineDocumentationRule(BaseRule):
    """
    [ND-024] Inline Documentation Rule
    Enum values and struct members should have inline trailing comments (`//`).
    """

    @property
    def rule_id(self) -> str:
        return "[ND-024]"

    @property
    def description(self) -> str:
        return "Enum elements and struct members require inline comments."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # AST node driven check for enum items and struct/union members
        enum_item_nodes = self._find_tree_nodes_by_tag(context, "kEnumMemberControl")
        struct_member_nodes = self._find_tree_nodes_by_tag(context, "kStructUnionMember")
        member_nodes = enum_item_nodes + struct_member_nodes

        if member_nodes:
            lines = file_content.splitlines()
            has_rawtokens = context and hasattr(context, 'rawtokens') and context.rawtokens
            for node in member_nodes:
                line_num = self._node_start_line(node, file_content, context)
                has_inline = False
                if has_rawtokens:
                    has_inline = self._has_inline_comment_in_rawtokens(context, line_num, file_content)
                else:
                    idx = line_num - 1
                    if 0 <= idx < len(lines):
                        line_str = lines[idx].strip()
                        has_inline = ("//" in line_str or "/*" in line_str or line_str.startswith("*"))

                if not has_inline:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=line_num,
                            message=f"Missing inline documentation comment ('//') for enum item or struct field."
                        )
                    )
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        in_block = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if any(kw in stripped for kw in ["enum", "struct", "union"]) and "{" in stripped:
                if "}" in stripped:
                    if "//" not in stripped and "/*" not in stripped:
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=i + 1,
                                message="Missing inline documentation comment ('//') for enum item or struct field."
                            )
                        )
                    continue
                else:
                    in_block = True
                    continue
            if in_block:
                if "}" in stripped:
                    in_block = False
                    continue
                if stripped and "//" not in stripped and "/*" not in stripped and not stripped.startswith("*"):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message="Missing inline documentation comment ('//') for enum item or struct field."
                        )
                    )

        return violations
