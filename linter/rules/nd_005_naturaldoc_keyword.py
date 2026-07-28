# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class NaturalDocKeywordRule(BaseRule):
    """
    [ND-005] NaturalDocs Keyword Rule
    All NaturalDocs keywords are not case-sensitive. Space is required after colon.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-005]"

    @property
    def description(self) -> str:
        return "NaturalDocs keywords require a space after the colon."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        keywords = ["package", "class", "function", "task", "group", "define", "enum", "typedef", "struct", "union", "interface", "module", "modport", "clocking"]
        pattern = r"^\s*(?://|/\*|\*|)\s*(" + "|".join(keywords) + r"):([^\s\n].*)"
        
        tokens = self._get_rawtokens(context)
        if tokens:
            comment_tokens = [t for t in tokens if self._is_comment_token(t)]
            source_bytes = self._source_bytes(file_content, context)
            for token in comment_tokens:
                text = getattr(token, 'text', '') or ''
                for line_idx, line in enumerate(text.splitlines()):
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        offset = getattr(token, 'start', 0)
                        line_num = self._line_for_byte_offset(source_bytes, offset) + line_idx
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line_num,
                                message=f"Missing space after colon in keyword '{match.group(1)}:'."
                            )
                        )
            return violations

        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=i + 1,
                        message=f"Missing space after colon in keyword '{match.group(1)}:'."
                    )
                )

        return violations
