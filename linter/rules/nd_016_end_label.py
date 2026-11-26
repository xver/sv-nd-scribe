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

        tag_to_kw = {
            "kClassDeclaration": "endclass",
            "kFunctionDeclaration": "endfunction",
            "kTaskDeclaration": "endtask",
            "kPackageDeclaration": "endpackage",
            "kModuleDeclaration": "endmodule",
            "kInterfaceDeclaration": "endinterface",
            "kCovergroupDeclaration": "endgroup",
            "kCheckerDeclaration": "endchecker",
            "kProgramDeclaration": "endprogram",
            "kPropertyDeclaration": "endproperty",
        }
        has_ast = context is not None and getattr(context, 'tree', None) is not None
        if has_ast:
            for tag, kw in tag_to_kw.items():
                nodes = self._find_tree_nodes_by_tag(context, tag)
                for node in nodes:
                    children = getattr(node, 'children', [])
                    # Check whether construct ends with end keyword via AST
                    has_end_kw = any(
                        getattr(c, 'tag', '') == kw or
                        (getattr(c, 'text', '') or "").strip() == kw
                        for c in children
                    )
                    if not has_end_kw:
                        continue

                    # Check for kLabel or kFunctionEndlabel AST node
                    has_label = any(
                        getattr(c, 'tag', '') in ('kLabel', 'kFunctionEndlabel')
                        for c in children
                    )
                    if not has_label:
                        end_offset = getattr(node, 'end', None)
                        source_bytes = self._source_bytes(file_content, context)
                        line = (
                            self._line_for_byte_offset(source_bytes, end_offset)
                            if end_offset
                            else self._node_start_line(node, file_content, context)
                        )
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line,
                                message=f"Missing labeled end statement for '{kw}'. Expected '{kw} : <name>'."
                            )
                        )
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
