# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

from typing import List, Any
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class NoTabsRule(BaseRule):
    """
    [WKL-008] No Tabs Rule
    Scans each line to ensure no tab characters (\\t) are used anywhere in the file.
    """
    @property
    def rule_id(self) -> str:
        return "[WKL-008]"
    
    @property
    def description(self) -> str:
        return "No tab characters allowed."
        
    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR
        
    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        lines = file_content.split('\n')
        
        for i, line in enumerate(lines):
            if '\t' in line:
                violations.append(self.create_violation(
                    file_path=file_path, line=i+1,
                    message="Tab character (\\t) found in line."
                ))
                
        return violations
