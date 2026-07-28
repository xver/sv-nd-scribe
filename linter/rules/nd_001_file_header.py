# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os
import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class FileHeaderRule(BaseRule):
    """
    [ND-001] File Header Rule
    Every `.sv` file MUST begin with a block comment header using `/* */` syntax
    and contain a `File:` NaturalDocs keyword line matching the file basename.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-001]"

    @property
    def description(self) -> str:
        return "Every .sv file MUST begin with a block comment header using /* */ syntax containing 'File: <filename>'."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def _check_header_content(self, header_text: str, file_path: str, line_num: int) -> List[RuleViolation]:
        violations = []
        file_basename = os.path.basename(file_path)

        # Check File: keyword
        file_match = re.search(r"^\s*(?:\*|//|/\*|)\s*File:\s*(.*)", header_text, re.IGNORECASE | re.MULTILINE)
        if not file_match:
            violations.append(
                self.create_violation(
                    file_path=file_path,
                    line=line_num,
                    message=f"File header is missing 'File:' NaturalDocs keyword ('File: {file_basename}')."
                )
            )
        else:
            doc_file = file_match.group(1).strip()
            if doc_file and doc_file != file_basename:
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=line_num,
                        message=f"Documented file name '{doc_file}' in header does not match actual filename '{file_basename}'."
                    )
                )

        # Check Author format (email address required)
        author_match = re.search(r"^\s*(?:\*|//|/\*|)\s*Author:\s*(.*)", header_text, re.IGNORECASE | re.MULTILINE)
        if author_match:
            author_val = author_match.group(1).strip()
            email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
            if not re.search(email_pattern, author_val):
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=line_num,
                        message="File header Author field must contain a valid email address."
                    )
                )

        return violations

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        tokens = self._get_rawtokens(context)
        if tokens:
            first_comment = None
            source_bytes = self._source_bytes(file_content, context)
            for tok in tokens:
                if self._is_whitespace_token(tok):
                    continue
                if self._is_comment_token(tok):
                    first_comment = tok
                break

            if first_comment is None or not (getattr(first_comment, 'text', '').strip().startswith("/*")):
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=1,
                        message="Missing block comment file header (/* */)."
                    )
                )
                return violations

            header_text = getattr(first_comment, 'text', '') or ""
            start_offset = getattr(first_comment, 'start', 0)
            header_start_line = self._line_for_byte_offset(source_bytes, start_offset)

            return self._check_header_content(header_text, file_path, header_start_line)

        # Fallback text parsing
        lines = file_content.splitlines()
        header_start = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("/*"):
                header_start = i
                break
            else:
                break

        if header_start == -1:
            violations.append(
                self.create_violation(
                    file_path=file_path,
                    line=1,
                    message="Missing block comment file header (/* */)."
                )
            )
            return violations

        header_lines = []
        for line in lines[header_start:]:
            header_lines.append(line)
            if "*/" in line:
                break

        header_text = "\n".join(header_lines)
        return self._check_header_content(header_text, file_path, header_start + 1)
