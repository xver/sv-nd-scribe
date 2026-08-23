# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal
from agent.fixer.doc_helper import build_naturaldocs_comment

_RE = re.compile(r'\b(module|class|package|interface|function|task|checker|program|property)\s+(\w+)')
ND_TAG_MAP = {
    "class": "Class",
    "module": "Module",
    "package": "Package",
    "interface": "Interface",
    "function": "Function",
    "task": "Task",
    "checker": "Checker",
    "program": "Program",
    "property": "Property",
}


class FixNd004(BaseFixer):
    """Insert construct-specific NaturalDocs comment for ND-004."""

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

        keyword = None
        name = "item"
        m = _RE.search(line)
        if not m and line.strip() == "" and line_idx + 1 < len(source_lines):
            next_line = source_lines[line_idx + 1]
            m = _RE.search(next_line)

        if m:
            keyword = m.group(1).lower()
            name = m.group(2)

        tag = ND_TAG_MAP.get(keyword, "Documented Statement")
        doc_comment, llm_generated = build_naturaldocs_comment(
            tag=tag,
            name=name,
            indent=indent,
            source_lines=source_lines,
            line_idx=line_idx,
            kind_label=keyword or "construct",
            provider=kwargs.get("provider"),
            skill_name="nd_comment",
        )

        return FixProposal(
            rule_id="ND-004",
            file=violation["file"],
            line=violation["line"],
            description=f"Insert // {tag}: {name} documentation comment",
            patch_lines=[doc_comment],
            replace_line=None,
            is_safe=True,
            llm_generated=llm_generated,
        )
