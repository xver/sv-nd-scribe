# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal


class FixWkl009(BaseFixer):
    """Split multiple variable declarations in a single statement into separate statements."""

    def propose(
        self,
        violation: Dict[str, Any],
        source_lines: List[str],
        config: Dict[str, Any] = None,
        **kwargs,
    ) -> Optional[FixProposal]:
        line_idx = violation["line"] - 1
        if not (0 <= line_idx < len(source_lines)):
            return None

        line = source_lines[line_idx]
        indent = line[: len(line) - len(line.lstrip())]
        stripped = line.strip()

        # Strip trailing comment
        code_part = stripped.split("//")[0].split("/*")[0].strip()
        if not code_part.endswith(";"):
            return None

        # Match qualifier + type + optional packed dimensions
        m = re.match(
            r"^((?:rand\s+|randc\s+|const\s+|static\s+|automatic\s+|local\s+|protected\s+|public\s+)*"
            r"(?:wire|tri|tri0|tri1|wand|wor|supply0|supply1|logic|bit|int|integer|byte|shortint|longint|time|shortreal|real|realtime|string|[a-zA-Z_][a-zA-Z0-9_]*)"
            r"(?:\s*\[[^\]]+\])*)\s+(.+);$",
            code_part
        )
        if not m:
            return None

        type_prefix = m.group(1).strip()
        rest = m.group(2).strip()

        # Split rest by comma respecting brackets/parentheses
        vars_in_line = []
        current = []
        depth = 0
        for ch in rest:
            if ch in "([{'\"":
                depth += 1
                current.append(ch)
            elif ch in ")]}'\"":
                depth -= 1
                current.append(ch)
            elif ch == "," and depth == 0:
                vars_in_line.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        if current:
            vars_in_line.append("".join(current).strip())

        if len(vars_in_line) <= 1:
            return None

        patch_lines = []
        for var_expr in vars_in_line:
            patch_lines.append(f"{indent}{type_prefix} {var_expr};\n")

        var_names = [v.split("=")[0].split("[")[0].strip() for v in vars_in_line]
        var_list_str = ", ".join(var_names)

        return FixProposal(
            rule_id="WKL-009",
            file=violation["file"],
            line=violation["line"],
            description=f"Split multiple declarations ('{var_list_str}') into separate statements",
            patch_lines=patch_lines,
            replace_line=line,
            is_safe=True,
            llm_generated=False,
        )
