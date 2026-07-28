# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class GroupHeadingRule(BaseRule):
    """
    [ND-006] Group Heading Rule
    Use `// Group:` to create logical sections within a scope.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-006]"

    @property
    def description(self) -> str:
        return "Group headings must use standard '// Group: Section Name' format."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        tokens = self._get_rawtokens(context)
        if tokens:
            comment_tokens = [t for t in tokens if self._is_comment_token(t)]
            source_bytes = self._source_bytes(file_content, context)
            for token in comment_tokens:
                text = getattr(token, 'text', '') or ''
                for line_idx, line in enumerate(text.splitlines()):
                    if re.match(r"^\s*(?://|/\*|\*|)\s*Group:([^\s].*)", line, re.IGNORECASE):
                        offset = getattr(token, 'start', 0)
                        line_num = self._line_for_byte_offset(source_bytes, offset) + line_idx
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line_num,
                                message="Malformed group heading. Expected format: '// Group: Section Name'."
                            )
                        )
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            if re.match(r"^\s*//\s*Group:([^\s].*)", line, re.IGNORECASE):
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=i + 1,
                        message="Malformed group heading. Expected format: '// Group: Section Name'."
                    )
                )

        return violations
