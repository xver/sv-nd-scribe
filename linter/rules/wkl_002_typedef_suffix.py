# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import List, Any
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class TypedefSuffixRule(BaseRule):
    """
    [WKL-002] Typedef Suffix Rule
    Checks that non-enum typedefs end in '_t' and enums end in '_e'.
    """
    @property
    def rule_id(self) -> str:
        return "[WKL-002]"
    
    @property
    def description(self) -> str:
        return "Non-enum typedefs must end in '_t', enums must end in '_e'."
        
    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR
        
    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # AST node driven check
        type_nodes = self._find_tree_nodes_by_tag(context, "kTypeDeclaration")
        if type_nodes:
            for node in type_nodes:
                text = getattr(node, 'text', '') or ""
                is_enum = "enum" in text
                m = re.search(r"\btypedef\b.*?\b([a-zA-Z_][a-zA-Z0-9_]*)\s*;\s*$", text.strip(), re.DOTALL)
                if m:
                    t_name = m.group(1)
                    line = self._node_start_line(node, file_content, context)
                    if is_enum and not t_name.endswith("_e"):
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line,
                                message=f"Enum typedef '{t_name}' must end in '_e'."
                            )
                        )
                    elif not is_enum and not t_name.endswith("_t"):
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line,
                                message=f"Typedef '{t_name}' must end in '_t'."
                            )
                        )
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            match = re.match(r"^\s*typedef\s+.*?\b([a-zA-Z_][a-zA-Z0-9_]*)\s*;\s*$", line)
            if match:
                t_name = match.group(1)
                is_enum = "enum" in line
                if is_enum and not t_name.endswith("_e"):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Enum typedef '{t_name}' must end in '_e'."
                        )
                    )
                elif not is_enum and not t_name.endswith("_t"):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"Typedef '{t_name}' must end in '_t'."
                        )
                    )

        return violations

    def _get_identifier_text(self, node):
        if not node:
            return None
        if node.get('text'):
            return node.get('text')
        for child in node.get('children', []):
            if isinstance(child, dict):
                text = self._get_identifier_text(child)
                if text:
                    return text
        return None

    def _get_line_number(self, file_bytes: bytes, byte_offset: int) -> int:
        if byte_offset is None or byte_offset == 0:
            return 1
        return file_bytes[:byte_offset].count(b'\n') + 1
