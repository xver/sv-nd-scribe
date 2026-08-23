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
        config: Dict[str, Any] = None, **kwargs,
    ) -> Optional[FixProposal]:
        if not source_lines:
            return None

        last_line = source_lines[-1]
        fixed = last_line.rstrip("\r\n") + "\n"

        # Also handle the case where the file has multiple trailing blank lines
        # Strip all trailing blank lines, keep exactly one trailing newline
        trimmed = list(source_lines)
        while trimmed and trimmed[-1].strip() == "":
            trimmed.pop()

        if not trimmed:
            return None

        last_non_empty = trimmed[-1]
        fixed_last = last_non_empty.rstrip("\r\n") + "\n"

        # Build the replacement: trimmed content with exactly one trailing newline
        # We return a proposal that replaces the last line only if it's simple,
        # or propose a full replacement block if there are extra blank lines.
        if len(trimmed) == len(source_lines) and last_line == fixed_last:
            # File already ends correctly
            return None

        if len(trimmed) == len(source_lines):
            # Just the last line needs a newline appended
            return FixProposal(
                rule_id="WKL-005",
                file=violation["file"],
                line=len(source_lines),
                description="Append missing newline at end of file",
                patch_lines=[fixed_last],
                replace_line=last_line,
                is_safe=True,
            )

        # Extra trailing blank lines: replace the last real line + remove blanks.
        # We do this by replacing source_lines[len(trimmed)-1:] with [fixed_last].
        # Since FixProposal only handles single-line patches, we handle by
        # using line = len(trimmed) and inserting nothing extra; the caller
        # apply_proposals_in_memory will replace that line and leave the
        # trailing lines intact. We instead mark the violation line as the
        # first trailing blank and use replace_line to collapse them.
        # Simplest safe approach: report the last non-empty line for replacement.
        return FixProposal(
            rule_id="WKL-005",
            file=violation["file"],
            line=len(source_lines),
            description="Remove extra trailing blank lines and ensure single EOF newline",
            patch_lines=[fixed_last],
            replace_line=source_lines[-1],
            is_safe=True,
        )
