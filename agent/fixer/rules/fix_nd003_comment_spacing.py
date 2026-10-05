# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal


class FixNd003(BaseFixer):
    """
    Fix comment formatting:
      - Remove redundant nested '//' markers inside block comments
      - Remove redundant nested '/*' markers inside block comments
      - Normalize redundant single-line comment markers ('// //', '////')
      - Fix space after colon in comment keywords
    """

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

        orig = source_lines[line_idx]
        fixed = orig

        # 1. Check if line has a nested '//' inside a block comment
        # e.g., '  //   Description text' or '* // Description text' or '// Description'
        m_asterisk = re.match(r"^(\s*\*\s*)//\s*(.*)$", fixed)
        if m_asterisk:
            content = m_asterisk.group(2)
            prefix = m_asterisk.group(1)
            fixed = f"{prefix}{content}\n" if content else f"{prefix}\n"
        else:
            m_nested_slash = re.match(r"^(\s*)//\s*(.*)$", fixed)
            if m_nested_slash:
                # Determine if this line is inside an enclosing /* ... */ block comment
                is_inside_block = False
                block_indent = None
                prev_idx = line_idx - 1
                while prev_idx >= 0:
                    prev_line = source_lines[prev_idx]
                    if "*/" in prev_line:
                        # Another block comment closed before this line
                        break
                    if "/*" in prev_line:
                        is_inside_block = True
                        base_ind = len(prev_line) - len(prev_line.lstrip())
                        if block_indent is None:
                            block_indent = " " * (base_ind + 2)
                        break
                    elif prev_line.strip() != "":
                        if block_indent is None:
                            prev_ind = len(prev_line) - len(prev_line.lstrip())
                            block_indent = " " * prev_ind
                    prev_idx -= 1

                if is_inside_block:
                    leading_ws = m_nested_slash.group(1)
                    content = m_nested_slash.group(2)
                    target_indent = leading_ws
                    if block_indent is not None and len(leading_ws) < len(block_indent):
                        target_indent = block_indent
                    fixed = f"{target_indent}{content}\n" if content else f"{target_indent}\n"

        # 2. Check for nested '/*' inside block comment
        if not fixed.lstrip().startswith("//") and "/*" in fixed and not fixed.lstrip().startswith("/*"):
            fixed = re.sub(r'/\*\s*', '', fixed)

        # 3. Check for redundant comment markers in single-line comments
        if fixed.lstrip().startswith("//"):
            if not re.search(r'[a-zA-Z0-9_]', fixed):
                pass
            elif re.match(r"^\s*//\s*/\*", fixed):
                if "*/" in fixed:
                    fixed = re.sub(r"^(\s*//)\s*/\*\s*(.*?)\s*\*/\s*$", r"\1 \2", fixed.rstrip("\r\n")) + "\n"
                else:
                    fixed = re.sub(r"^(\s*//)\s*/\*\s*", r"\1 ", fixed)
            elif re.match(r"^\s*//\s*//", fixed):
                fixed = re.sub(r"^(\s*//)\s*//\s*", r"\1 ", fixed)
            elif re.match(r"^\s*/{4,}\s*[a-zA-Z0-9_]", fixed):
                fixed = re.sub(r"^(\s*)/{4,}\s*", r"\1// ", fixed)

        # 4. Check for space after colon in comment keywords
        fixed = re.sub(r'((?://|/\*|\*|)\s*[A-Za-z0-9_]+):([^\s\n/])', r'\1: \2', fixed)

        if fixed != orig:
            return FixProposal(
                rule_id="ND-003",
                file=violation["file"],
                line=violation["line"],
                description="Remove redundant/nested comment markers and fix spacing",
                patch_lines=[fixed],
                replace_line=orig,
                is_safe=True,
            )

        return None

