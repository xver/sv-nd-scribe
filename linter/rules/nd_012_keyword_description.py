# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class KeywordDescriptionRule(BaseRule):
    """
    [ND-012] Keyword Description Rule
    NaturalDocs keyword block MUST contain a description following the keyword line.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-012]"

    @property
    def description(self) -> str:
        return "NaturalDocs comment block must include a description following the keyword line."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        kw_pattern = r"^\s*(?://|/\*|\*|)\s*(Package|Class|Function|Task|Interface|Module|Define|Enum|Type|Variable|Modport|Clocking):\s*\w+"
        no_kw_pattern = r"^\s*(?://|/\*|\*|)\s*(Package|Class|Function|Task|Interface|Module|Define|Enum|Type|Variable|Modport|Clocking):"

        tokens = self._get_rawtokens(context)
        if tokens:
            comment_tokens = [t for t in tokens if self._is_comment_token(t)]
            source_bytes = self._source_bytes(file_content, context)
            for idx, token in enumerate(comment_tokens):
                text = getattr(token, 'text', '') or ''
                sublines = text.splitlines()
                for line_idx, line in enumerate(sublines):
                    match = re.match(kw_pattern, line, re.IGNORECASE)
                    if match:
                        has_desc = False
                        if line_idx + 1 < len(sublines):
                            next_l = sublines[line_idx + 1].strip()
                            if self._line_is_comment_line(next_l) and not re.match(no_kw_pattern, next_l, re.IGNORECASE):
                                has_desc = True
                        elif idx + 1 < len(comment_tokens):
                            next_tok = comment_tokens[idx + 1]
                            next_text = getattr(next_tok, 'text', '') or ''
                            next_l = next_text.splitlines()[0].strip() if next_text else ""
                            if self._line_is_comment_line(next_l) and not re.match(no_kw_pattern, next_l, re.IGNORECASE):
                                has_desc = True
                        if not has_desc:
                            offset = getattr(token, 'start', 0)
                            line_num = self._line_for_byte_offset(source_bytes, offset) + line_idx
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line_num,
                                    message=f"Comment for '{match.group(1)}' is missing a description following the keyword line."
                                )
                            )
            return violations

        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            match = re.match(r"^\s*//\s*(Package|Class|Function|Task|Interface|Module|Define|Enum|Type|Variable|Modport|Clocking):\s*\w+", line, re.IGNORECASE)
            if match:
                has_desc = False
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith("//") and not re.match(r"^\s*//\s*(Package|Class|Function|Task|Interface|Module|Define|Enum|Type|Variable|Modport|Clocking):", next_line, re.IGNORECASE):
                        has_desc = True
                if not has_desc:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Comment for '{match.group(1)}' is missing a description following the keyword line."
                        )
                    )

        return violations
