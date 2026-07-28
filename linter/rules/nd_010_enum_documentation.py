# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class EnumDocumentationRule(BaseRule):
    """
    [ND-010] Enum Documentation Rule
    Each enum type should have a preceding NaturalDocs comment and each enum value should have a comment.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-010]"

    @property
    def description(self) -> str:
        return "Enum declarations MUST have a preceding NaturalDocs comment block."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        lines = file_content.splitlines()
        
        for i, line in enumerate(lines):
            if "enum" in line and "typedef" in line:
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments or not any("enum" in c.lower() for c in comments):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message="Enum typedef is missing preceding NaturalDocs documentation ('// enum: <name>')."
                        )
                    )

        return violations
