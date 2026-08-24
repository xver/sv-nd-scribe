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
        file_match = re.search(r"^\s*(?:\*|//|/\*|)\s*File:\s*(.*)", header_text, re.IGNORECASE | re.MULTILINE)
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
            doc_file = file_match.group(1).strip()
            if doc_file and doc_file != file_basename:
                file_line = get_line_for_pattern(r"^\s*(?:\*|//|/\*|)\s*File:")
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
        author_match = re.search(r"^\s*(?:\*|//|/\*|)\s*Author:\s*(.*)", header_text, re.IGNORECASE | re.MULTILINE)
        if author_match:
            author_val = author_match.group(1).strip()
            if author_val and not re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", author_val):
                author_line = get_line_for_pattern(r"^\s*(?:\*|//|/\*|)\s*Author:")
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
                        message=f"File header {field_name} field contains unresolved placeholder 'TODO_AUTHOR'.",
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

        if not lines:
            return violations

        first_non_empty_idx = -1
        for idx, line in enumerate(lines):
            if line.strip():
                first_non_empty_idx = idx
                break

        if first_non_empty_idx == -1:
            return violations

        first_line = lines[first_non_empty_idx].strip()
        actual_line_num = first_non_empty_idx + 1

        if not first_line.startswith("/*"):
            violations.append(
                self.create_violation(
                    file_path=file_path,
                    line=actual_line_num,
                    message="Missing block comment file header (/* */). Every file must begin with a block comment header.",
                    severity=RuleSeverity.ERROR
                )
            )
            return violations

        header_lines = []
        in_header = False
        header_start_line = actual_line_num

        for idx in range(first_non_empty_idx, len(lines)):
            line = lines[idx]
            if not in_header:
                if "/*" in line:
                    in_header = True
                    header_lines.append(line)
                    if "*/" in line and line.find("*/") > line.find("/*"):
                        break
            else:
                header_lines.append(line)
                if "*/" in line:
                    break

        header_text = "\n".join(header_lines)
        violations.extend(self._check_header_content(header_text, file_path, header_start_line, context))

        return violations
