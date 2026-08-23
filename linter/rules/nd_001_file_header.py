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

    def _has_custom_template(self, file_path: str, context: Any = None) -> bool:
        cfg = {}
        if isinstance(context, dict):
            cfg = context.get("config", context)
        elif hasattr(context, "config"):
            cfg = getattr(context, "config", {}) or {}

        custom_template = (cfg.get("agent", {}) if isinstance(cfg.get("agent"), dict) else {}).get("custom_header_template") or cfg.get("custom_header_template") or cfg.get("header_template")
        if custom_template:
            return True

        candidates = ["header_template.sv", ".sv_header_template.sv", "template/header_template.sv"]
        file_dir = os.path.dirname(os.path.abspath(file_path)) if file_path else os.getcwd()
        curr = file_dir
        for _ in range(10):
            for cand in candidates:
                if os.path.exists(os.path.join(curr, cand)):
                    return True
            parent = os.path.dirname(curr)
            if parent == curr:
                break
            curr = parent

        return False

    def _check_header_content(self, header_text: str, file_path: str, line_num: int, context: Any = None) -> List[RuleViolation]:
        violations = []

        # If a custom user header template exists, bypass field-level header rules entirely
        if self._has_custom_template(file_path, context):
            return violations

        file_basename = os.path.basename(file_path)
        header_lines = header_text.splitlines()

        def get_line_for_pattern(pattern: str) -> int:
            for idx, l_str in enumerate(header_lines):
                if re.search(pattern, l_str, re.IGNORECASE):
                    return line_num + idx
            return line_num

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
                file_line = get_line_for_pattern(r"^\s*(?:\*|//|/\*|)\s*File:")
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=file_line,
                        message=f"Documented file name '{doc_file}' in header does not match actual filename '{file_basename}'."
                    )
                )

        # Check Author field presence & email format
        author_match = re.search(r"^\s*(?:\*|//|/\*|)\s*Author:\s*(.*)", header_text, re.IGNORECASE | re.MULTILINE)
        if not author_match or not author_match.group(1).strip():
            author_line = get_line_for_pattern(r"^\s*(?:\*|//|/\*|)\s*Author:")
            violations.append(
                self.create_violation(
                    file_path=file_path,
                    line=author_line,
                    message="File header is missing 'Author:' field."
                )
            )
        else:
            author_val = author_match.group(1).strip()
            if "TODO" not in author_val and not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", author_val):
                author_line = get_line_for_pattern(r"^\s*(?:\*|//|/\*|)\s*Author:")
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=author_line,
                        message="File header Author field must contain a valid email address."
                    )
                )

        # Check TODO placeholders in header fields
        for idx, l_str in enumerate(header_lines):
            todo_match = re.search(r"\b(TODO[A-Za-z0-9_]*)\b", l_str)
            if todo_match:
                todo_token = todo_match.group(1)
                actual_line = line_num + idx
                field_match = re.search(r"^\s*(?:\*|//|/\*|)\s*([A-Za-z]+):\s*(.*)", l_str)
                if field_match:
                    field_name = field_match.group(1)
                    msg = f"File header {field_name} field contains unresolved placeholder '{todo_token}'."
                else:
                    msg = f"File header contains unresolved placeholder '{todo_token}'."

                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=actual_line,
                        message=msg
                    )
                )

        return violations

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        tokens = self._get_rawtokens(context)
        if tokens:
            first_block_comment = None
            source_bytes = self._source_bytes(file_content, context)
            for tok in tokens:
                if self._is_whitespace_token(tok):
                    continue
                if self._is_comment_token(tok):
                    text = getattr(tok, 'text', '').strip() if hasattr(tok, 'text') else ""
                    if text.startswith("/*"):
                        first_block_comment = tok
                        break
                    continue
                break

            if first_block_comment is None:
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=1,
                        message="Missing block comment file header (/* */)."
                    )
                )
                return violations

            header_text = getattr(first_block_comment, 'text', '') or ""
            start_offset = getattr(first_block_comment, 'start', 0)
            header_start_line = self._line_for_byte_offset(source_bytes, start_offset)

            return self._check_header_content(header_text, file_path, header_start_line, context)

        lines = file_content.splitlines()
        header_start = -1
        for i, line in enumerate(lines[:50]):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
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
        return self._check_header_content(header_text, file_path, header_start + 1, context)
