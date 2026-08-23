# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal
from agent.fixer.doc_helper import build_naturaldocs_comment

_RE = re.compile(r'\binterface\s+(\w+)')


class FixNd013(BaseFixer):
    """Insert NaturalDocs // Interface: <name> comment for ND-013."""

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

        line = source_lines[line_idx]
        indent = line[: len(line) - len(line.lstrip())]

        name = "item"
        m = _RE.search(line)
        if m:
            name = m.group(1)
        elif line.strip() == "" and line_idx + 1 < len(source_lines):
            next_line = source_lines[line_idx + 1]
            m = _RE.search(next_line)
            if m:
                name = m.group(1)

        doc_comment, llm_generated = build_naturaldocs_comment(
            tag="Interface",
            name=name,
            indent=indent,
            source_lines=source_lines,
            line_idx=line_idx,
            kind_label="interface",
            provider=kwargs.get("provider"),
            skill_name="nd_comment",
        )
        return FixProposal(
            rule_id="ND-013",
            file=violation["file"],
            line=violation["line"],
            description=f"Insert // Interface: {name} documentation comment",
            patch_lines=[doc_comment],
            replace_line=None,
            is_safe=True,
            llm_generated=llm_generated,
        )
