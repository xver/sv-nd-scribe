# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class CommentSpacingRule(BaseRule):
    """
    [ND-003] Comment Spacing Rule
    Every NaturalDocs comment line must begin with `//` followed by space or keyword token with proper spacing.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-003]"

    @property
    def description(self) -> str:
        return "Every NaturalDocs comment line must follow required spacing after // and keyword delimiters."

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
                is_block = text.startswith('/*')
                offset = getattr(token, 'start', 0)
                base_line = self._line_for_byte_offset(source_bytes, offset)
                token_lines = text.splitlines()

                for line_idx, line in enumerate(token_lines):
                    line_num = base_line + line_idx
                    stripped = line.strip()

                    # 1. Check keyword format (missing space after colon)
                    match = re.match(r"^\s*(?://|/\*|\*|)\s*([A-Za-z]+):([^\s\n/].*)", line)
                    if match and not match.group(2).startswith("/"):
                        if match.group(1).lower() not in ("http", "https", "file", "ftp"):
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line_num,
                                    message=f"Invalid keyword format in comment: missing space after colon in '{stripped}'."
                                )
                            )

                    # 2. Block comment checks
                    if is_block:
                        if line_idx > 0 and '/*' in line:
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line_num,
                                    message="Redundant nested block comment marker '/*' inside block comment."
                                )
                            )
                        m_nested = re.match(r"^\s*(?:\*\s*)?//\s*(.*)", line)
                        if m_nested:
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line_num,
                                    message="Redundant single-line comment marker '//' inside block comment."
                                )
                            )
                    else:
                        # 3. Single-line comment checks
                        if not re.search(r'[a-zA-Z0-9_]', line):
                            continue
                        if re.match(r"^\s*//\s*//", line):
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line_num,
                                    message="Redundant comment marker '//' in single-line comment."
                                )
                            )
                        elif re.match(r"^\s*/{4,}\s*[a-zA-Z0-9_]", line):
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line_num,
                                    message="Redundant comment marker '////' in single-line comment."
                                )
                            )
                        elif re.match(r"^\s*//\s*/\*", line):
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line_num,
                                    message="Redundant nested block comment marker '/*' inside single-line comment."
                                )
                            )
            return violations

        lines = file_content.splitlines()
        in_block_comment = False
        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()

            if in_block_comment:
                if '/*' in stripped and not stripped.startswith('/*'):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=line_num,
                            message="Redundant nested block comment marker '/*' inside block comment."
                        )
                    )
                m_nested = re.match(r"^\s*(?:\*\s*)?//\s*(.*)", line)
                if m_nested:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=line_num,
                            message="Redundant single-line comment marker '//' inside block comment."
                        )
                    )
                match = re.match(r"^\s*(?:\*|)\s*([A-Za-z]+):([^\s\n/].*)", line)
                if match and not match.group(2).startswith("/"):
                    if match.group(1).lower() not in ("http", "https", "file", "ftp"):
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line_num,
                                message=f"Invalid keyword format in comment: missing space after colon in '{stripped}'."
                            )
                        )
                if '*/' in stripped:
                    in_block_comment = False
            else:
                if stripped.startswith('/*'):
                    if '*/' not in stripped[2:]:
                        in_block_comment = True
                    else:
                        if re.search(r"/\*.*?\b//", stripped):
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line_num,
                                    message="Redundant single-line comment marker '//' inside block comment."
                                )
                            )
                    match = re.match(r"^\s*/\*\s*([A-Za-z]+):([^\s\n/].*)", line)
                    if match and not match.group(2).startswith("/"):
                        if match.group(1).lower() not in ("http", "https", "file", "ftp"):
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line_num,
                                    message=f"Invalid keyword format in comment: missing space after colon in '{stripped}'."
                                )
                            )
                elif stripped.startswith('//'):
                    match = re.match(r"^\s*//\s*([A-Za-z]+):([^\s\n/].*)", line)
                    if match and not match.group(2).startswith("/"):
                        if match.group(1).lower() not in ("http", "https", "file", "ftp"):
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line_num,
                                    message=f"Invalid keyword format in comment: missing space after colon in '{stripped}'."
                                )
                            )
                    if not re.search(r'[a-zA-Z0-9_]', line):
                        continue
                    if re.match(r"^\s*//\s*//", line):
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line_num,
                                message="Redundant comment marker '//' in single-line comment."
                            )
                        )
                    elif re.match(r"^\s*/{4,}\s*[a-zA-Z0-9_]", line):
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line_num,
                                message="Redundant comment marker '////' in single-line comment."
                            )
                        )
                    elif re.match(r"^\s*//\s*/\*", line):
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line_num,
                                message="Redundant nested block comment marker '/*' inside single-line comment."
                            )
                        )

        return violations
