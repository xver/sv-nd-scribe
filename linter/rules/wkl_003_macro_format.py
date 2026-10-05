# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import List, Any
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class MacroFormatRule(BaseRule):
    """
    [WKL-003] Macro Format Rule
    Checks that macro defines are in UPPER_SNAKE_CASE.
    """
    @property
    def rule_id(self) -> str:
        return "[WKL-003]"
    
    @property
    def description(self) -> str:
        return "Macro defines should be UPPER_SNAKE_CASE."
        
    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR
        
    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # AST node driven check
        has_ast = context is not None and getattr(context, 'tree', None) is not None
        if has_ast:
            nodes = self._find_tree_nodes_by_tag(context, "kPreprocessorDefine")
            for node in nodes:
                text = (getattr(node, 'text', '') or "").strip()
                macro_name = ""
                if hasattr(node, 'find_all'):
                    try:
                        id_nodes = list(node.find_all(lambda n: getattr(n, 'tag', '') == 'PP_Identifier'))
                        if id_nodes:
                            macro_name = id_nodes[0].text.strip()
                    except Exception:
                        pass
                if not macro_name:
                    m = re.search(r"^`define\s+([a-zA-Z_][a-zA-Z0-9_]*)", text)
                    if m:
                        macro_name = m.group(1)

                if macro_name and not re.match(r"^[A-Z0-9_]+$", macro_name):
                    line = self._node_start_line(node, file_content, context)
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=line,
                            message=f"Macro `{macro_name}` should be in UPPER_SNAKE_CASE."
                        )
                    )
            return violations

        # Fallback text parsing
        clean_content = self._mask_comments_and_strings(file_content)
        lines = clean_content.splitlines()
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("`define"):
                parts = stripped.split()
                if len(parts) >= 2:
                    macro_name = parts[1].split("(")[0].strip()
                    if not re.match(r"^[A-Z0-9_]+$", macro_name):
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=i + 1,
                                message=f"Macro `{macro_name}` should be in UPPER_SNAKE_CASE."
                            )
                        )

        return violations
