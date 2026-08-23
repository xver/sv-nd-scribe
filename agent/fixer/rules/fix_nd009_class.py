# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal
from agent.fixer.doc_helper import (
    build_naturaldocs_comment,
    extract_name_from_violation,
    extract_construct_params_and_ports,
    build_construct_extra_lines,
)

_RE = re.compile(r'\bclass\s+(?:automatic\s+)?([A-Za-z0-9_]+)')


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

        name = extract_name_from_violation(violation)
        if not name or name == "item":
            match = _RE.search(line)
            if match:
                name = match.group(match.lastindex or 1)
            elif line.strip() == "" and line_idx + 1 < len(source_lines):
                next_line = source_lines[line_idx + 1]
                match = _RE.search(next_line)
                if match:
                    name = match.group(match.lastindex or 1)

        if not name:
            name = "item"

        params, ports = extract_construct_params_and_ports(line, source_lines, line_idx)
        extra_lines = build_construct_extra_lines(params, ports, indent)

        doc_comment, llm_generated = build_naturaldocs_comment(
            tag="Class",
            name=name,
            indent=indent,
            source_lines=source_lines,
            line_idx=line_idx,
            kind_label="class",
            provider=kwargs.get("provider"),
            skill_name="nd_comment",
            extra_lines=extra_lines,
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
