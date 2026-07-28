# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class PropertyAssertionRule(BaseRule):
    """
    [ND-015] Property/Assertion Documentation Rule
    Property and assertion declarations MUST have a preceding NaturalDocs comment.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-015]"

    @property
    def description(self) -> str:
        return "Property and assertion declarations MUST have a preceding NaturalDocs comment."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        lines = file_content.splitlines()
        
        for i, line in enumerate(lines):
            match = re.match(r"^\s*property\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
            if match:
                prop_name = match.group(1)
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments or not any("property" in c.lower() or "assertion" in c.lower() for c in comments):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Property '{prop_name}' is missing preceding NaturalDocs documentation."
                        )
                    )

        return violations
