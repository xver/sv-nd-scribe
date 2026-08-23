# Copyright (c) 2026 IC Verimeter. All rights reserved.
import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal

# Map each end-keyword to its matching open keyword and vice versa
_END_TO_OPEN = {
    "endmodule":    "module",
    "endclass":     "class",
    "endpackage":   "package",
    "endinterface": "interface",
    "endchecker":   "checker",
    "endprogram":   "program",
    "endtask":      "task",
    "endfunction":  "function",
    "endgroup":     "covergroup",
    "endproperty":  "property",
}
_OPEN_KEYWORDS = set(_END_TO_OPEN.values())
_END_KEYWORDS  = set(_END_TO_OPEN.keys())

# Regex to match an end keyword at the start of significant content
_END_RE  = re.compile(r'\b(' + '|'.join(_END_KEYWORDS) + r')\b')
_OPEN_RE = re.compile(
    r'\b(module|class|package|interface|checker|program|task|function|covergroup|property)\s+(\w+)'
)


class FixNd016(BaseFixer):
    """Append : <name> label to closing end* statement using a scope-stack scan."""

    def propose(
        self,
        violation: Dict[str, Any],
        source_lines: List[str],
        config: Dict[str, Any] = None, **kwargs,
    ) -> Optional[FixProposal]:
        line_idx = violation["line"] - 1
        if not (0 <= line_idx < len(source_lines)):
            return None

        orig = source_lines[line_idx]
        stripped_orig = orig.rstrip(" \t\r\n")

        # Determine which end-keyword is on the violation line
        end_match = _END_RE.search(stripped_orig)
        if not end_match:
            return None
        end_kw = end_match.group(1)
        target_open_kw = _END_TO_OPEN.get(end_kw)
        if not target_open_kw:
            return None

        # Scope stack: walk backward, counting nested end/open pairs
        # depth starts at 1 (for the end* we're resolving)
        depth = 1
        name = None
        for idx in range(line_idx - 1, -1, -1):
            line = source_lines[idx]
            # Count any end keywords on this line that match end_kw
            for em in _END_RE.finditer(line):
                if em.group(1) == end_kw:
                    depth += 1
            # Count matching open keywords
            for om in _OPEN_RE.finditer(line):
                if om.group(1) == target_open_kw:
                    depth -= 1
                    if depth == 0:
                        name = om.group(2)
                        break
            if depth == 0:
                break

        if not name:
            return None

        # Only propose if label is not already present
        if stripped_orig.endswith(f": {name}") or stripped_orig.endswith(f":{name}"):
            return None

        fixed = f"{stripped_orig} : {name}\n"
        return FixProposal(
            rule_id="ND-016",
            file=violation["file"],
            line=violation["line"],
            description=f"Append label : {name} to {end_kw} statement",
            patch_lines=[fixed],
            replace_line=orig,
            is_safe=True,
        )

