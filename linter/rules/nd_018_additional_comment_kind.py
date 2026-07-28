# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class AdditionalCommentKindRule(BaseRule):
    """
    [ND-018] Additional Comment Kind Rule
    Checkers and specific construct blocks MUST have NaturalDocs comments. Process blocks are optional.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-018]"

    @property
    def description(self) -> str:
        return "Checkers and construct blocks MUST have NaturalDocs comments."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        lines = file_content.splitlines()
        
        for i, line in enumerate(lines):
            match = re.match(r"^\s*checker\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
            if match:
                name = match.group(1)
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Checker '{name}' is missing documentation."
                        )
                    )

        return violations
