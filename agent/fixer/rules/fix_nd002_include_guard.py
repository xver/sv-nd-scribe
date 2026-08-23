# Copyright (c) 2026 IC Verimeter. All rights reserved.
import os
import re
from typing import List, Dict, Any, Optional, Union
from agent.fixer.base_fixer import BaseFixer, FixProposal

class FixNd002(BaseFixer):
    """Insert or adjust include guard `ifndef / `define."""
    def propose(self, violation: Dict[str, Any], source_lines: List[str], config: Dict[str, Any] = None, **kwargs) -> Optional[Union[FixProposal, List[FixProposal]]]:
        filename = os.path.basename(violation["file"])
        macro_name = re.sub(r'[^A-Za-z0-9_]', '_', filename).upper()
        if not macro_name.endswith("_SV") and not macro_name.endswith("_SVH"):
            macro_name += "_SV"
        
        msg = violation.get("message", "")
        if "Missing `endif" in msg or "missing trailing comment" in msg:
            line_num = violation["line"]
            if "missing trailing comment" in msg and 0 <= line_num - 1 < len(source_lines):
                orig_line = source_lines[line_num - 1]
                return FixProposal(
                    rule_id="ND-002",
                    file=violation["file"],
                    line=line_num,
                    description=f"Add trailing comment to `endif // {macro_name}",
                    patch_lines=[f"`endif // {macro_name}\n"],
                    replace_line=orig_line,
                    is_safe=True
                )
            return FixProposal(
                rule_id="ND-002",
                file=violation["file"],
                line=len(source_lines) + 1,
                description=f"Append `endif // {macro_name}",
                patch_lines=[f"\n`endif // {macro_name}\n"],
                replace_line=None,
                is_safe=True
            )
        
        guard_block = [
            f"`ifndef {macro_name}\n",
            f"`define {macro_name}\n"
        ]

        # Search for end line of block comment header /* ... */ in top 50 lines
        header_end_idx = -1
        in_header = False
        for idx, l_str in enumerate(source_lines[:50]):
            stripped = l_str.strip()
            if not in_header:
                if stripped.startswith("/*"):
                    in_header = True
                    if "*/" in stripped:
                        header_end_idx = idx
                        break
            else:
                if "*/" in stripped:
                    header_end_idx = idx
                    break

        insert_line = (header_end_idx + 2) if header_end_idx != -1 else 1

        top_proposal = FixProposal(
            rule_id="ND-002",
            file=violation["file"],
            line=insert_line,
            description=f"Insert include guard `ifndef {macro_name} below file header",
            patch_lines=guard_block,
            replace_line=None,
            is_safe=True
        )

        has_endif = any(re.search(r"`endif\b", l) for l in source_lines)
        if not has_endif:
            bottom_proposal = FixProposal(
                rule_id="ND-002",
                file=violation["file"],
                line=len(source_lines) + 1,
                description=f"Append `endif // {macro_name}",
                patch_lines=[f"\n`endif // {macro_name}\n"],
                replace_line=None,
                is_safe=True
            )
            return [top_proposal, bottom_proposal]

        return top_proposal
