# Copyright (c) 2026 IC Verimeter. All rights reserved.
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal

class FixWkl006(BaseFixer):
    """Strip trailing whitespace from violation line."""
    def propose(self, violation: Dict[str, Any], source_lines: List[str], config: Dict[str, Any] = None, **kwargs) -> Optional[FixProposal]:
        line_idx = violation["line"] - 1
        if 0 <= line_idx < len(source_lines):
            orig = source_lines[line_idx]
            fixed = orig.rstrip(" \t\r\n") + "\n"
            if orig != fixed:
                return FixProposal(
                    rule_id="WKL-006",
                    file=violation["file"],
                    line=violation["line"],
                    description="Strip trailing whitespace from line",
                    patch_lines=[fixed],
                    replace_line=orig,
                    is_safe=True
                )
        return None
