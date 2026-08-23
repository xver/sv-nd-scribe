# Copyright (c) 2026 IC Verimeter. All rights reserved.
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal

class FixWkl008(BaseFixer):
    """Replace tab characters with spaces."""
    def propose(self, violation: Dict[str, Any], source_lines: List[str], config: Dict[str, Any] = None, **kwargs) -> Optional[FixProposal]:
        line_idx = violation["line"] - 1
        if 0 <= line_idx < len(source_lines):
            orig = source_lines[line_idx]
            tab_width = int((config or {}).get("tab_width", 2))
            fixed = orig.replace("\t", " " * tab_width)
            if orig != fixed:
                return FixProposal(
                    rule_id="WKL-008",
                    file=violation["file"],
                    line=violation["line"],
                    description=f"Replace tab characters with {tab_width} spaces",
                    patch_lines=[fixed],
                    replace_line=orig,
                    is_safe=True
                )
        return None
