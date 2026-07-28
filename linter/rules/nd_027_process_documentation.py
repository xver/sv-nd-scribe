# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class ProcessDocumentationRule(BaseRule):
    """
    [ND-027] Process Documentation Rule
    Process blocks (initial, always, always_ff, always_comb, always_latch, final) MUST have preceding NaturalDocs comments.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-027]"

    @property
    def description(self) -> str:
        return "Process blocks MUST have preceding NaturalDocs comments."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            match = re.match(r"^\s*(initial|always|always_ff|always_comb|always_latch|final)\b", line)
            if match:
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments:
                    proc_kind = match.group(1)
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Process block '{proc_kind}' is missing preceding NaturalDocs comment."
                        )
                    )
        return violations
