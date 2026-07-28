# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class IncludeGuardRule(BaseRule):
    """
    [ND-002] Include Guard Rule
    Files MUST use `ifndef / `define / `endif` include guards with trailing comment.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-002]"

    @property
    def description(self) -> str:
        return "Files MUST use `ifndef / `define / `endif` include guards with trailing comment."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # Exclude package files (_pkg.sv or package declaration) from include guard requirement
        if file_path.endswith("_pkg.sv") or re.search(r"\bpackage\s+[a-zA-Z_]", file_content) or self._find_tree_nodes_by_tag(context, "kPackageDeclaration"):
            return violations

        has_ifndef = bool(re.search(r"`ifndef\s+\w+", file_content))
        has_define = bool(re.search(r"`define\s+\w+", file_content))
        
        if not (has_ifndef and has_define):
            violations.append(
                self.create_violation(
                    file_path=file_path,
                    line=1,
                    message="Missing include guard (`ifndef / `define)."
                )
            )
            return violations

        # Check endif trailing comment
        lines = file_content.splitlines()
        endif_found = False
        for i, line in enumerate(lines):
            if line.strip().startswith("`endif"):
                endif_found = True
                if not re.search(r"`endif\s*//\s*\w+", line):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message="Include guard `endif missing trailing comment with macro name."
                        )
                    )
                break
                
        if not endif_found:
            violations.append(
                self.create_violation(
                    file_path=file_path,
                    line=len(lines),
                    message="Missing `endif for include guard."
                )
            )

        return violations
