# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class LineLengthRule(BaseRule):
    """
    [WKL-007] Line Length Rule
    Checks that lines do not exceed the maximum allowed line length (default 120 characters).
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.max_line_length = self.config.get("max_line_length", 120)

    @property
    def rule_id(self) -> str:
        return "[WKL-007]"

    @property
    def description(self) -> str:
        return f"Line length must not exceed {self.max_line_length} characters."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.WARNING

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            if len(line) > self.max_line_length:
                violations.append(
                    self.create_violation(
                        file_path=file_path,
                        line=i + 1,
                        message=f"Line exceeds maximum length of {self.max_line_length} characters ({len(line)} > {self.max_line_length})."
                    )
                )
        return violations
