# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal


class FixNd024(BaseFixer):
    """Insert inline documentation comment (/// ...) for ND-024."""

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
        stripped = line.rstrip()

        # Extract identifier name from enum element or struct member line
        clean_code = stripped.split("//")[0].split("/*")[0].strip().rstrip(",;")
        clean_code = clean_code.split("=")[0].strip()
        tokens = clean_code.split()
        name = tokens[-1] if tokens else "item"

        # Check if line already has trailing comment
        if "//" in stripped or "/*" in stripped:
            return None

        desc = f"TODO description for {name}"
        fixed_line = f"{stripped}///{desc}\n"

        return FixProposal(
            rule_id="ND-024",
            file=violation["file"],
            line=violation["line"],
            description=f"Add inline documentation comment for {name}",
            patch_lines=[fixed_line],
            replace_line=line,
            is_safe=True,
            llm_generated=False,
        )
