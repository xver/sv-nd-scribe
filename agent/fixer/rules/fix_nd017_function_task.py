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
)

_SIG_RE = re.compile(
    r'\b(?:extern\s+|external\s+)?(?:pure\s+virtual\s+|virtual\s+|protected\s+|local\s+|static\s+)*(function|task)(?:\s+automatic)?(?:\s+(?:void|(?:[\w:<>\$]+(?:\s*\[[^\]]+\])*)|\s*(?:\[[^\]]+\])))?\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|;)',
    re.IGNORECASE,
)


class FixNd017(BaseFixer):
    """Insert NaturalDocs Function/Task comment with Parameters block for ND-017."""

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

        # 1. First priority: Extract the AST-derived name from the linter violation message
        kw = None
        name = extract_name_from_violation(violation)
        msg = violation.get("message", "")
        if msg:
            m_msg = re.search(r"\b(Function|Task)\s+'([^']+)'", msg, re.IGNORECASE)
            if m_msg:
                kw = m_msg.group(1).capitalize()
                if not name:
                    name = m_msg.group(2)

        # 2. Fallback: Parse line signature using comprehensive SystemVerilog regex
        m = _SIG_RE.search(line)
        if not name or name == "item":
            name = m.group(2) if m else "item"
        if name and name.lower() == "new":
            kw = "Function"
        elif not kw:
            kw = m.group(1).capitalize() if m else "Function"

        params = extract_function_params(line, source_lines, line_idx)
        param_lines = build_parameters_block(params, indent)

        # Check if there is already a // Function: / // Task: comment block above line_idx
        has_existing_header = False
        for k in range(line_idx - 1, -1, -1):
            prev_line = source_lines[k].strip()
            if prev_line.startswith("// Function:") or prev_line.startswith("// Task:") or prev_line.startswith("// function:") or prev_line.startswith("// task:"):
                has_existing_header = True
                break
            elif not prev_line.startswith("//") and not prev_line.startswith("/*") and not prev_line.startswith("*"):
                break

        if has_existing_header:
            return FixProposal(
                rule_id="ND-017",
                file=violation["file"],
                line=violation["line"],
                description=f"Insert Parameters section for {kw.lower()} '{name}'",
                patch_lines=param_lines,
                replace_line=None,
                is_safe=True,
                llm_generated=False,
            )

        doc_comment, llm_generated = build_naturaldocs_comment(
            tag=kw,
            name=name,
            indent=indent,
            source_lines=source_lines,
            line_idx=line_idx,
            kind_label=kw.lower(),
            provider=kwargs.get("provider"),
            skill_name="function_task",
            extra_lines=param_lines,
        )

        return FixProposal(
            rule_id="ND-017",
            file=violation["file"],
            line=violation["line"],
            description=f"Insert // {kw}: {name} documentation comment",
            patch_lines=[doc_comment],
            replace_line=None,
            is_safe=True,
            llm_generated=llm_generated,
        )
