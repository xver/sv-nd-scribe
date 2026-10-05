# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


_PLACEHOLDER_DESC_RE = re.compile(
    r"^\s*(?:TODO(?:\s*\[.*?\])?:?|(?:add\s+)?description\s+(?:for|of)\b|<.*?>)",
    re.IGNORECASE,
)


class KeywordDescriptionRule(BaseRule):
    """
    [ND-012] Keyword Description Rule
    NaturalDocs keyword block MUST contain a valid description following the keyword line.
    Generic placeholders such as 'Description for item' or 'TODO' are not acceptable.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-012]"

    @property
    def description(self) -> str:
        return "NaturalDocs comment block must include a valid description following the keyword line."

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
                        is_block = text.lstrip().startswith("/*")
                        if line_idx + 1 < len(sublines):
                            for follow_idx in range(line_idx + 1, len(sublines)):
                                follow_line = sublines[follow_idx].strip()
                                if is_block:
                                    if follow_line == "*/" or follow_line.startswith("*/"):
                                        break
                                    clean_l = re.sub(r"^\*+\s*", "", follow_line).strip()
                                    if clean_l.endswith("*/"):
                                        clean_l = clean_l[:-2].strip()
                                else:
                                    clean_l = follow_line.lstrip("/").strip()
                                if not clean_l:
                                    continue
                                if re.match(no_kw_pattern, follow_line, re.IGNORECASE):
                                    break
                                if _PLACEHOLDER_DESC_RE.search(clean_l):
                                    continue
                                has_desc = True
                                break
                        if not has_desc:
                            curr_tok_end_line = self._line_for_byte_offset(source_bytes, getattr(token, 'start', 0)) + len(sublines) - 1
                            for next_idx in range(idx + 1, len(comment_tokens)):
                                next_tok = comment_tokens[next_idx]
                                next_tok_start_line = self._line_for_byte_offset(source_bytes, getattr(next_tok, 'start', 0))
                                if next_tok_start_line > curr_tok_end_line + 1:
                                    break
                                curr_tok_end_line = next_tok_start_line + max(1, len((getattr(next_tok, 'text', '') or '').splitlines())) - 1
                                next_text = getattr(next_tok, 'text', '') or ''
                                found_stop = False
                                for follow_line in next_text.splitlines():
                                    follow_line = follow_line.strip()
                                    clean_l = follow_line.lstrip("/*").rstrip("*/").strip()
                                    if not clean_l:
                                        continue
                                    if re.match(no_kw_pattern, follow_line, re.IGNORECASE):
                                        found_stop = True
                                        break
                                    if _PLACEHOLDER_DESC_RE.search(clean_l):
                                        continue
                                    has_desc = True
                                    found_stop = True
                                    break
                                if found_stop:
                                    break
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
        in_block = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if "/*" in stripped:
                in_block = True
            match = re.match(r"^\s*(?://|/\*|\*|)\s*(Package|Class|Function|Task|Interface|Module|Define|Enum|Type|Variable|Modport|Clocking):\s*\w+", line, re.IGNORECASE)
            if match:
                has_desc = False
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if in_block:
                        if next_line == "*/" or next_line.startswith("*/"):
                            break
                        clean_l = re.sub(r"^\*+\s*", "", next_line).strip()
                        if clean_l.endswith("*/"):
                            clean_l = clean_l[:-2].strip()
                    else:
                        if not next_line.startswith("//"):
                            break
                        clean_l = next_line.lstrip("/").strip()
                    if not clean_l:
                        continue
                    if re.match(r"^\s*(?://|/\*|\*|)\s*(Package|Class|Function|Task|Interface|Module|Define|Enum|Type|Variable|Modport|Clocking):", next_line, re.IGNORECASE):
                        break
                    if _PLACEHOLDER_DESC_RE.search(clean_l):
                        continue
                    has_desc = True
                    break
                if not has_desc:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Comment for '{match.group(1)}' is missing a description following the keyword line."
                        )
                    )
            if "*/" in stripped:
                in_block = False

        return violations
