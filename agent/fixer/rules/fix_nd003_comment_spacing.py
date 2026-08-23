# Copyright (c) 2026 IC Verimeter. All rights reserved.
import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal

class FixNd003(BaseFixer):
    """Fix space after colon in comment keywords e.g. // Class:name -> // Class: name."""
    def propose(self, violation: Dict[str, Any], source_lines: List[str], config: Dict[str, Any] = None, **kwargs) -> Optional[FixProposal]:
        line_idx = violation["line"] - 1
        if 0 <= line_idx < len(source_lines):
            orig = source_lines[line_idx]
            fixed = re.sub(r'(//\s*[A-Za-z0-9_]+):([^\s])', r'\1: \2', orig)
            if orig != fixed:
                return FixProposal(
                    rule_id="ND-003",
                    file=violation["file"],
                    line=violation["line"],
                    description="Fix space after colon in NaturalDocs comment keyword",
                    patch_lines=[fixed],
                    replace_line=orig,
                    is_safe=True
                )
        return None
