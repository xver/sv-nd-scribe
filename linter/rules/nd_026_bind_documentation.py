# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class BindDocumentationRule(BaseRule):
    """
    [ND-026] Bind Documentation Rule
    Bind directives MUST have preceding NaturalDocs comments explaining the binding target.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-026]"

    @property
    def description(self) -> str:
        return "Bind directives MUST have preceding NaturalDocs comments."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("bind ") or re.match(r"^\s*bind\s+[a-zA-Z_]", line):
                comments = self._extract_comments_from_text(file_content, i + 1)
                has_kw = False
                if comments:
                    for c in comments:
                        if re.search(r"^\s*(?://|/\*|\*|)\s*bind\s*:", c, re.IGNORECASE):
                            has_kw = True
                            break
                if not has_kw:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message="Bind directive is missing preceding NaturalDocs comment ('// Bind:')."
                        )
                    )
        return violations
