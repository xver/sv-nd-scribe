# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os
import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity

DEFAULT_BUILTIN_HEADER_TEMPLATE = """/******************************************************************************
 * File:        ${filename}
 *
 * Company:     ${company}
 *
 * Author:      ${author}
 *
 * Description: ${description}
 *
 * Created:     ${created}
 *
 * Updated:     ${updated}
 *
 * Copyright (c) ${year} ${company}
 * ${legal}
 ******************************************************************************/"""


class FileHeaderRule(BaseRule):
    """
    [ND-001] File Header Rule
    Every `.sv` file MUST begin with a header comment using `/* */` or `//` syntax
    and contain a `File:` NaturalDocs keyword line matching the file basename.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-001]"

    @property
    def description(self) -> str:
        return "Every .sv file MUST begin with a header comment using /* */ or // syntax containing 'File: <filename>'."

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

        if context and isinstance(context, dict) and context.get("disable_custom_template"):
            return False

        if not file_path or not os.path.isabs(file_path):
            return False

        norm_default = re.sub(r"\s+", " ", DEFAULT_BUILTIN_HEADER_TEMPLATE.strip())

        candidates = [
            ".sv-nd-scribe/header_template.txt",
            ".sv-nd-scribe/header_template",
            "header_template.txt",
            "header_template",
            "agent/templates/header_template.txt",
            "agent/templates/header_template",
            "template/header_template.txt",
            "template/header_template"
        ]
        file_dir = os.path.dirname(os.path.abspath(file_path))
        curr = file_dir
        for _ in range(10):
            for cand in candidates:
                cand_path = os.path.join(curr, cand)
                if os.path.exists(cand_path):
                    try:
                        with open(cand_path, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                        norm_content = re.sub(r"\s+", " ", content)
                        if norm_content != norm_default:
                            return True
                    except Exception:
                        pass
            parent = os.path.dirname(curr)
            if parent == curr:
                break
            curr = parent

        return False

    def _check_header_content(self, header_text: str, file_path: str, line_num: int, context: Any = None) -> List[RuleViolation]:
        violations = []
        file_basename = os.path.basename(file_path)
        header_lines = header_text.splitlines()

        def get_line_for_pattern(pattern: str) -> int:
            for idx, l_str in enumerate(header_lines):
                if re.search(pattern, l_str, re.IGNORECASE):
                    return line_num + idx
            return line_num

        # 1. Check File: keyword (ALWAYS an ERROR)
        file_match = re.search(r"^\s*(?://|/\*|\*)?[\s*]*File:\s*(.*)", header_text, re.IGNORECASE | re.MULTILINE)
        if not file_match:
            violations.append(
                self.create_violation(
                    file_path=file_path,
                    line=line_num,
                    message=f"File header is missing 'File:' NaturalDocs keyword ('File: {file_basename}').",
                    severity=RuleSeverity.ERROR
                )
            )
        else:
            doc_file = re.sub(r"[\s*]+$", "", file_match.group(1)).strip()
            if doc_file and doc_file != file_basename:
                file_line = get_line_for_pattern(r"^\s*(?://|/\*|\*)?[\s*]*File:")
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=file_line,
                        message=f"Documented file name '{doc_file}' in header does not match actual filename '{file_basename}'.",
                        severity=RuleSeverity.ERROR
                    )
                )

        # If a custom user header template exists, disable ALL other field-level warnings and errors
        if self._has_custom_template(file_path, context):
            return violations

        # Check Author format if present
        author_match = re.search(r"^\s*(?://|/\*|\*)?[\s*]*Author:\s*(.*)", header_text, re.IGNORECASE | re.MULTILINE)
        if author_match:
            author_val = re.sub(r"[\s*]+$", "", author_match.group(1)).strip()
            if author_val and "TODO" not in author_val and not re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9_.-]+\.[a-zA-Z0-9-.]+", author_val):
                author_line = get_line_for_pattern(r"^\s*(?://|/\*|\*)?[\s*]*Author:")
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=author_line,
                        message=f"File header Author '{author_val}' should contain a valid email address.",
                        severity=RuleSeverity.WARNING
                    )
                )

        # 2. Check for TODO placeholders (WARNING severity)
        for idx, l_str in enumerate(header_lines):
            cur_line = line_num + idx
            if "TODO_COMPANY" in l_str or "TODO COMPANY" in l_str:
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=cur_line,
                        message="File header Company field contains unresolved placeholder 'TODO_COMPANY'.",
                        severity=RuleSeverity.WARNING
                    )
                )
            elif "TODO_AUTHOR" in l_str or "TODO AUTHOR" in l_str:
                field_name = "Author" if "Author:" in l_str else "Created" if "Created:" in l_str else "Updated" if "Updated:" in l_str else "Author"
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=cur_line,
                        message=(
                            f"File header {field_name} field contains unresolved placeholder 'TODO_AUTHOR'. "
                            "Please configure your author in VS Code Settings ('sv-nd-scribe.author'), "
                            "agent_config.json ('agent.header_defaults.author'), or Git "
                            "('git config --global user.name' and 'git config --global user.email')."
                        ),
                        severity=RuleSeverity.WARNING
                    )
                )
            elif "TODO_LEGAL" in l_str or "TODO LEGAL" in l_str:
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=cur_line,
                        message="File header contains unresolved placeholder 'TODO_LEGAL'.",
                        severity=RuleSeverity.WARNING
                    )
                )
            elif "TODO" in l_str:
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=cur_line,
                        message="File header contains unresolved placeholder 'TODO'.",
                        severity=RuleSeverity.WARNING
                    )
                )

        return violations

    def check(self, file_path: str, content: str, context: Any = None) -> List[RuleViolation]:
        violations = []
        lines = content.splitlines()

        if not lines or not content.strip():
            return violations

        tokens = self._get_rawtokens(context)
        if tokens:
            source_bytes = self._source_bytes(content, context)
            first_comment_idx = -1
            for idx, t in enumerate(tokens):
                if self._is_whitespace_token(t):
                    continue
                tag = getattr(t, 'tag', '') or ''
                text = getattr(t, 'text', '') or ''
                if tag.startswith('`') or tag.startswith('PP_') or text.startswith('`'):
                    # Skip preprocessor / compiler directives preceding file header (e.g. `ifndef, `define, `timescale)
                    continue
                if self._is_comment_token(t):
                    first_comment_idx = idx
                    break
                else:
                    # Encountered code token before any file header comment block
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=1,
                            message="Missing block comment file header (/* */ or //). Every file must begin with a block comment header.",
                            severity=RuleSeverity.ERROR
                        )
                    )
                    return violations

            if first_comment_idx == -1:
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=1,
                        message="Missing block comment file header (/* */ or //). Every file must begin with a block comment header.",
                        severity=RuleSeverity.ERROR
                    )
                )
                return violations

            header_tokens = []
            consecutive_newlines = 0
            for t in tokens[first_comment_idx:]:
                if self._is_comment_token(t):
                    header_tokens.append(t)
                    consecutive_newlines = 0
                elif self._is_whitespace_token(t):
                    nl_count = getattr(t, 'text', '').count('\n')
                    consecutive_newlines += nl_count
                    if consecutive_newlines > 1:
                        # Blank line separates header block from subsequent comments/code
                        break
                else:
                    # Non-comment, non-whitespace token reached
                    break

            if not header_tokens:
                return violations

            header_start_line = self._line_for_byte_offset(source_bytes, header_tokens[0].start)
            header_end_line = self._line_for_byte_offset(source_bytes, header_tokens[-1].end)
            header_text = "\n".join(lines[header_start_line - 1 : header_end_line])
            violations.extend(self._check_header_content(header_text, file_path, header_start_line, context))
            return violations

        # Fallback when AST tokens are unavailable (e.g. standalone unit tests)
        first_candidate_idx = -1
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("`"):
                # Skip blank lines and preprocessor directives (e.g. `ifndef, `define, `timescale)
                continue
            first_candidate_idx = idx
            break

        if first_candidate_idx == -1:
            violations.append(
                self.create_violation(
                    file_path=file_path,
                    line=1,
                    message="Missing block comment file header (/* */ or //). Every file must begin with a block comment header.",
                    severity=RuleSeverity.ERROR
                )
            )
            return violations

        first_line = lines[first_candidate_idx].strip()
        actual_line_num = first_candidate_idx + 1

        if not (first_line.startswith("/*") or first_line.startswith("//")):
            violations.append(
                self.create_violation(
                    file_path=file_path,
                    line=1,
                    message="Missing block comment file header (/* */ or //). Every file must begin with a block comment header.",
                    severity=RuleSeverity.ERROR
                )
            )
            return violations

        header_lines = []
        in_block = False
        for idx in range(first_candidate_idx, len(lines)):
            line = lines[idx]
            stripped = line.strip()
            if in_block:
                header_lines.append(line)
                if "*/" in stripped:
                    in_block = False
            else:
                if not stripped:
                    # Blank line outside block comment terminates header block
                    break
                if stripped.startswith("/*"):
                    header_lines.append(line)
                    if not ("*/" in stripped and stripped.find("*/") > stripped.find("/*")):
                        in_block = True
                elif stripped.startswith("//"):
                    header_lines.append(line)
                else:
                    # Non-comment line terminates header
                    break

        header_text = "\n".join(header_lines)
        violations.extend(self._check_header_content(header_text, file_path, actual_line_num, context))
        return violations
