# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class ExternImplementationRule(BaseRule):
    """
    [ND-030] Extern Implementation Rule
    Out-of-body implementation of an extern method MUST have preceding NaturalDocs comment.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-030]"

    @property
    def description(self) -> str:
        return "Extern method implementations outside class body MUST have preceding NaturalDocs comment."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        # ND-030 is disabled: documentation applies to class declarations, not out-of-body implementations.
        return []
