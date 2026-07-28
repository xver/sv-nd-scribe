# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

from typing import List, Any
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class EOFEmptyLineRule(BaseRule):
    """
    [WKL-005] EOF Empty Line Rule
    Validates that the file ends with exactly one newline character.
    """
    @property
    def rule_id(self) -> str:
        return "[WKL-005]"
    
    @property
    def description(self) -> str:
        return "File must end with exactly one empty line."
        
    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.WARNING
        
    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        if not file_content:
            return violations
            
        lines = file_content.split('\n')
        
        if not file_content.endswith('\n'):
            violations.append(self.create_violation(
                file_path=file_path, line=len(lines),
                message="File does not end with a newline."
            ))
        elif len(file_content) >= 2 and file_content.endswith('\n\n'):
            violations.append(self.create_violation(
                file_path=file_path, line=len(lines),
                message="File ends with multiple empty lines."
            ))
            
        return violations
