# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal

_MSG_RE = re.compile(r"Documented identifier '([^']+)' does not match code identifier '([^']+)'")


class FixNd019(BaseFixer):
    """Fixer for mismatch between NaturalDocs comment identifier and code identifier."""

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

        msg = violation.get("message", "")
        m = _MSG_RE.search(msg)
        if not m:
            return None

        doc_name, code_name = m.group(1), m.group(2)

        # Scan backwards from line_idx, allowing blank lines between declaration and comment block
        curr = line_idx - 1
        while curr >= 0 and source_lines[curr].strip() == "":
            curr -= 1

        end_idx = curr
        while curr >= 0:
            l_str = source_lines[curr].strip()
            if l_str.startswith("//") or l_str.startswith("/*") or l_str.startswith("*") or l_str.endswith("*/"):
                curr -= 1
            else:
                break
        start_idx = curr + 1

        # If no preceding comments, check if line_idx itself contains doc_name in a comment (e.g. inline comment)
        if start_idx > end_idx or end_idx < 0:
            if "//" in source_lines[line_idx] and doc_name in source_lines[line_idx].split("//", 1)[1]:
                start_idx = line_idx
                end_idx = line_idx
            else:
                return None

        # Collect lines in comment block that contain doc_name
        affected_indices = [
            i for i in range(start_idx, end_idx + 1)
            if doc_name in source_lines[i]
        ]

        if not affected_indices:
            return None

        patch_start = min(affected_indices)
        patch_end = max(affected_indices)

        patch_lines = []
        for i in range(patch_start, patch_end + 1):
            orig = source_lines[i]
            # Replace occurrences of doc_name with code_name in comments
            updated = re.sub(r'\b' + re.escape(doc_name) + r'\b', code_name, orig)
            if updated == orig and doc_name in orig:
                updated = orig.replace(doc_name, code_name)
            if not updated.endswith("\n"):
                updated += "\n"
            patch_lines.append(updated)

        return FixProposal(
            rule_id="ND-019",
            file=violation["file"],
            line=patch_start + 1,
            description=f"Update documented identifier '{doc_name}' to match code '{code_name}'",
            patch_lines=patch_lines,
            replace_line=None,
            replace_range=(patch_start + 1, patch_end + 1),
            is_safe=True,
        )
