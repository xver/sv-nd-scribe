# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class EndLabelRule(BaseRule):
    """
    [ND-016] End Label Rule
    End statements (endclass, endfunction, endtask, endpackage, endmodule, endinterface) MUST carry a label (`end<construct> : <name>`).
    """

    @property
    def rule_id(self) -> str:
        return "[ND-016]"

    @property
    def description(self) -> str:
        return "End statements MUST carry a labeled end statement (`end<construct> : <name>`)."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        tags = [
            "kClassDeclaration", "kFunctionDeclaration", "kTaskDeclaration",
            "kPackageDeclaration", "kModuleDeclaration", "kInterfaceDeclaration",
            "kCovergroupDeclaration", "kCheckerDeclaration", "kProgramDeclaration",
            "kPropertyDeclaration"
        ]
        has_ast = False
        for tag in tags:
            nodes = self._find_tree_nodes_by_tag(context, tag)
            if nodes:
                has_ast = True
                for node in nodes:
                    text = getattr(node, 'text', '') or ""
                    match = re.search(r"\b(endclass|endfunction|endtask|endpackage|endmodule|endinterface|endgroup|endchecker|endprogram|endproperty)\b(\s*:[^\n;]+)?", text)
                    if match:
                        kw = match.group(1)
                        label = match.group(2)
                        if not label:
                            # Estimate end line
                            end_offset = getattr(node, 'end', None)
                            source_bytes = self._source_bytes(file_content, context)
                            line = self._line_for_byte_offset(source_bytes, end_offset) if end_offset else self._node_start_line(node, file_content, context)
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line,
                                    message=f"Missing labeled end statement for '{kw}'. Expected '{kw} : <name>'."
                                )
                            )
        if has_ast:
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        end_keywords = ["endclass", "endfunction", "endtask", "endpackage", "endmodule", "endinterface", "endgroup", "endchecker", "endprogram", "endproperty"]
        pattern = r"^\s*(" + "|".join(end_keywords) + r")\b(\s*:[^\n]+)?"
        for i, line in enumerate(lines):
            match = re.match(pattern, line)
            if match:
                kw = match.group(1)
                label = match.group(2)
                if not label:
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Missing labeled end statement for '{kw}'. Expected '{kw} : <name>'."
                        )
                    )

        return violations
