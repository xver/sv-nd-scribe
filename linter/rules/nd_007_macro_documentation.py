# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class MacroDocumentationRule(BaseRule):
    """
    [ND-007] Macro Documentation Rule
    NaturalDocs keyword `define` is mapped to the Macro comment type. Include guard defines are exempted.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-007]"

    @property
    def description(self) -> str:
        return "Macros (`define) MUST have a preceding NaturalDocs comment block."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        lines = file_content.splitlines()
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("`define"):
                parts = stripped.split()
                if len(parts) < 2:
                    continue
                macro_name = parts[1].split("(")[0].strip()
                
                # Exclude include guard defines (e.g. preceded by `ifndef or matching filename guard)
                if i > 0 and lines[i-1].strip().startswith("`ifndef"):
                    continue
                file_guard = file_path.replace("\\", "/").split("/")[-1].replace(".", "_").upper()
                if not file_guard.endswith("_SV") and not file_guard.endswith("_SVH"):
                    file_guard += "_SV"
                if macro_name.upper() == file_guard or macro_name.upper() == file_path.replace("\\", "/").split("/")[-1].replace(".", "_").upper():
                    continue
                
                # Check preceding comments
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments or not any("define" in c.lower() for c in comments):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Macro `{macro_name}` is missing NaturalDocs documentation ('// define: {macro_name}')."
                        )
                    )

        return violations
