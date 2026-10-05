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

        file_guard = file_path.replace("\\", "/").split("/")[-1].replace(".", "_").upper()
        if not file_guard.endswith("_SV") and not file_guard.endswith("_SVH"):
            file_guard += "_SV"
        file_guard_alt = file_path.replace("\\", "/").split("/")[-1].replace(".", "_").upper()

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

                if not macro_name:
                    continue

                if macro_name.upper() in (file_guard, file_guard_alt):
                    continue

                line = self._node_start_line(node, file_content, context)
                # Check if preceded by `ifndef
                lines = file_content.splitlines()
                if line > 1 and lines[line - 2].strip().startswith("`ifndef"):
                    continue

                comments = self._comments_before_node(node, file_content, context)
                if not comments or not any("define" in c.lower() for c in comments):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=line,
                            message=f"Macro `{macro_name}` is missing NaturalDocs documentation ('// define: {macro_name}')."
                        )
                    )
            return violations

        # Fallback text parsing
        clean_content = self._mask_comments_and_strings(file_content)
        clean_lines = clean_content.splitlines()
        lines = file_content.splitlines()
        
        for i, line in enumerate(clean_lines):
            stripped = line.strip()
            if stripped.startswith("`define"):
                parts = stripped.split()
                if len(parts) < 2:
                    continue
                macro_name = parts[1].split("(")[0].strip()
                
                # Exclude include guard defines (e.g. preceded by `ifndef or matching filename guard)
                prev_line_idx = i - 1
                while prev_line_idx >= 0 and not clean_lines[prev_line_idx].strip():
                    prev_line_idx -= 1
                if prev_line_idx >= 0 and clean_lines[prev_line_idx].strip().startswith("`ifndef"):
                    continue
                if i > 0 and lines[i-1].strip().startswith("`ifndef"):
                    continue
                if macro_name.upper() == file_guard or macro_name.upper() == file_guard_alt:
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
