# Copyright (c) 2026 IC Verimeter. All rights reserved.
import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal

class FixNd005(BaseFixer):
    """Fix space after // in NaturalDocs comments e.g. //Keyword: -> // Keyword:."""
    def propose(self, violation: Dict[str, Any], source_lines: List[str], config: Dict[str, Any] = None, **kwargs) -> Optional[FixProposal]:
        line_idx = violation["line"] - 1
        if 0 <= line_idx < len(source_lines):
            orig = source_lines[line_idx]
            fixed = re.sub(r'//([A-Za-z0-9_]+:)', r'// \1', orig)
            if orig != fixed:
                return FixProposal(
                    rule_id="ND-005",
                    file=violation["file"],
                    line=violation["line"],
                    description="Fix space after // in NaturalDocs comment",
                    patch_lines=[fixed],
                    replace_line=orig,
                    is_safe=True
                )
        return None
