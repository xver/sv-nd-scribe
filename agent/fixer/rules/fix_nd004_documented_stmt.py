# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal
from agent.fixer.doc_helper import (
    build_naturaldocs_comment,
    extract_name_from_violation,
    extract_function_params,
    build_parameters_block,
    extract_construct_params_and_ports,
    build_construct_extra_lines,
)

_FN_RE = re.compile(
    r'\b(?:extern\s+|external\s+)?(?:pure\s+virtual\s+|virtual\s+|protected\s+|local\s+|static\s+)*(function|task)(?:\s+automatic)?(?:\s+(?:void|(?:[\w:<>\$]+(?:\s*\[[^\]]+\])*)|\s*(?:\[[^\]]+\])))?\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|;)',
    re.IGNORECASE
)
_CONSTRUCT_RE = re.compile(
    r'\b(class|module|package|interface|checker|program|property|covergroup|clocking|modport|constraint)\s+(?:automatic\s+)?([a-zA-Z_][a-zA-Z0-9_]*)',
    re.IGNORECASE
)

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
    "covergroup": "Covergroup",
    "clocking": "Clocking",
    "modport": "Modport",
    "constraint": "Constraint",
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
        name = extract_name_from_violation(violation)

        # Check line or next line if empty
        target_line = line
        if target_line.strip() == "" and line_idx + 1 < len(source_lines):
            target_line = source_lines[line_idx + 1]

        m_fn = _FN_RE.search(target_line)
        extra_lines = []
        if m_fn:
            keyword = m_fn.group(1).lower()
            if not name or name == "item":
                name = m_fn.group(2)
            params = extract_function_params(target_line, source_lines, line_idx)
            extra_lines = build_parameters_block(params, indent)
        else:
            m_c = _CONSTRUCT_RE.search(target_line)
            if m_c:
                keyword = m_c.group(1).lower()
                if not name or name == "item":
                    name = m_c.group(2)
                if keyword in ("class", "module", "interface", "checker", "program"):
                    c_params, c_ports = extract_construct_params_and_ports(target_line, source_lines, line_idx)
                    extra_lines = build_construct_extra_lines(c_params, c_ports, indent)

        if not name:
            name = "item"

        tag = ND_TAG_MAP.get(keyword, "Documented Statement")
        doc_comment, llm_generated = build_naturaldocs_comment(
            tag=tag,
            name=name,
            indent=indent,
            source_lines=source_lines,
            line_idx=line_idx,
            kind_label=keyword or "construct",
            provider=kwargs.get("provider"),
            skill_name="function_task" if keyword in ("function", "task") else "nd_comment",
            extra_lines=extra_lines,
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
