# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class IncludeGuardRule(BaseRule):
    """
    [ND-002] Include Guard Rule
    Files MUST use `ifndef / `define / `endif` include guards with trailing comment.
    Include guards MUST be located below the file header comment.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-002]"

    @property
    def description(self) -> str:
        return "Files MUST use `ifndef / `define / `endif` include guards located below file header comment."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # Exclude package files (_pkg.sv or package declaration) from include guard requirement
        if file_path.endswith("_pkg.sv") or re.search(r"\bpackage\s+[a-zA-Z_]", file_content) or self._find_tree_nodes_by_tag(context, "kPackageDeclaration"):
            return violations

        has_ifndef = bool(re.search(r"`ifndef\s+\w+", file_content))
        has_define = bool(re.search(r"`define\s+\w+", file_content))
        has_endif = bool(re.search(r"`endif\b", file_content))
        
        lines = file_content.splitlines()

        # Find line numbers of `ifndef and block header comment /*
        ifndef_line = -1
        header_line = -1
        for i, line in enumerate(lines[:30]):
            stripped = line.strip()
            if ifndef_line == -1 and stripped.startswith("`ifndef"):
                ifndef_line = i + 1
            if header_line == -1 and stripped.startswith("/*"):
                header_line = i + 1

        if not (has_ifndef and has_define):
            violations.append(
                self.create_violation(
                    file_path=file_path,
                    line=1,
                    message="Missing include guard (`ifndef / `define)."
                )
            )
            return violations

        # If include guard is placed BEFORE the header comment, flag it
        if ifndef_line != -1 and header_line != -1 and ifndef_line < header_line:
            violations.append(
                self.create_violation(
                    file_path=file_path,
                    line=ifndef_line,
                    message="Include guard (`ifndef / `define) must be located below the file header comment block."
                )
            )

        if not has_endif:
            violations.append(
                self.create_violation(
                    file_path=file_path,
                    line=max(1, len(lines)),
                    message="Missing `endif for include guard."
                )
            )
        else:
            for i, line in enumerate(lines):
                if line.strip().startswith("`endif"):
                    if not re.search(r"`endif\s*//\s*\w+", line):
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=i + 1,
                                message="Include guard `endif missing trailing comment with macro name."
                            )
                        )
                    break

        return violations
