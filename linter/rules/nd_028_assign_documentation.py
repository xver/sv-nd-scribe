# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity

_ASSIGN_NAME_RE = re.compile(
    r'\bassign\s+(?:(?:\([^)]*\)|#[0-9a-zA-Z_]+)\s+)*\{?\s*([a-zA-Z_][a-zA-Z0-9_]*)'
)


class AssignDocumentationRule(BaseRule):
    """
    [ND-028] Assign Documentation Rule
    Continuous assignments MUST have preceding NaturalDocs documentation.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-028]"

    @property
    def description(self) -> str:
        return "Continuous assignments MUST have preceding NaturalDocs documentation."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("assign ") or re.match(r"^\s*assign\s+[a-zA-Z_]", line):
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments:
                    m = _ASSIGN_NAME_RE.search(stripped)
                    sig_name = m.group(1) if m else "item"
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Continuous assignment '{sig_name}' is missing preceding NaturalDocs comment ('// Assign: {sig_name}')."
                        )
                    )
        return violations
