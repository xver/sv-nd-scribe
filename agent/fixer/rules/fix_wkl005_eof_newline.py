# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal


class FixWkl005(BaseFixer):
    """Ensure file ends with exactly one newline (WKL-005)."""

    def propose(
        self,
        violation: Dict[str, Any],
        source_lines: List[str],
        config: Dict[str, Any] = None,
        **kwargs,
    ) -> Optional[FixProposal]:
        if not source_lines:
            return None

        # Strip all trailing blank lines
        trimmed = list(source_lines)
        while trimmed and trimmed[-1].strip() == "":
            trimmed.pop()

        if not trimmed:
            return None

        last_non_empty_idx = len(trimmed) - 1
        last_non_empty = trimmed[last_non_empty_idx]
        fixed_last = last_non_empty.rstrip("\r\n") + "\n"

        # Case 1: Extra trailing blank lines exist
        if len(trimmed) < len(source_lines):
            # Replace from the last non-empty line through the end of the file
            # with just the single properly-terminated last line.
            return FixProposal(
                rule_id="WKL-005",
                file=violation["file"],
                line=len(trimmed),
                description="Remove extra trailing blank lines and ensure single EOF newline",
                patch_lines=[fixed_last],
                replace_range=(len(trimmed), len(source_lines)),
                is_safe=True,
            )

        # Case 2: No extra blank lines, but last line is missing trailing newline
        last_line = source_lines[-1]
        if last_line != fixed_last:
            return FixProposal(
                rule_id="WKL-005",
                file=violation["file"],
                line=len(source_lines),
                description="Append missing newline at end of file",
                patch_lines=[fixed_last],
                replace_range=(len(source_lines), len(source_lines)),
                is_safe=True,
            )

        return None
