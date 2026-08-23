# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal
from agent.fixer.doc_helper import build_naturaldocs_comment


class FixNd009(BaseFixer):
    """Insert NaturalDocs comment before construct for ND-009."""

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
        match = re.search(r'\bclass\s+([A-Za-z0-9_]+)', line)
        if match:
            name = match.group(match.lastindex or 1)

        doc_comment, llm_generated = build_naturaldocs_comment(
            tag="Class",
            name=name,
            indent=indent,
            source_lines=source_lines,
            line_idx=line_idx,
            kind_label="class",
            provider=kwargs.get("provider"),
            skill_name="nd_comment",
        )

        return FixProposal(
            rule_id="ND-009",
            file=violation["file"],
            line=violation["line"],
            description=f"Insert // Class: {name} documentation comment",
            patch_lines=[doc_comment],
            replace_line=None,
            is_safe=True,
            llm_generated=llm_generated,
        )
