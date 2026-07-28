# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

from typing import List, Any
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class TrailingWhitespaceRule(BaseRule):
    """
    [WKL-006] Trailing Whitespace Rule
    Scans each line to ensure no spaces/tabs exist before the newline.
    """
    @property
    def rule_id(self) -> str:
        return "[WKL-006]"
    
    @property
    def description(self) -> str:
        return "Lines must not have trailing whitespace."
        
    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR
        
    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        lines = file_content.split('\n')
        
        for i, line in enumerate(lines):
            if line.endswith(' ') or line.endswith('\t'):
                violations.append(self.create_violation(
                    file_path=file_path, line=i+1,
                    message="Trailing whitespace found."
                ))
                
        return violations
