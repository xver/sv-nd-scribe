# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal
from agent.fixer.doc_helper import (
    extract_comment_from_context,
    extract_function_params,
    build_parameters_block,
    extract_construct_params_and_ports,
    build_construct_extra_lines,
    build_ports_block,
)
from agent.llm.skill_loader import load_skill

_KW_RE = re.compile(
    r'^\s*//\s*(Package|Class|Function|Task|Interface|Module|Define|Enum|Type|Variable|Modport|Clocking|Checker|Property|Constraint|Covergroup|Coverpoint|Program):\s*(\w+)',
    re.IGNORECASE,
)


class FixNd012(BaseFixer):
    """Insert description line for ND-012 when NaturalDocs keyword is missing description."""

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

        kind = "element"
        name = "item"
        m = _KW_RE.search(line)
        if m:
            kind = m.group(1).lower()
            name = m.group(2)
        elif line.strip() == "" and line_idx + 1 < len(source_lines):
            next_line = source_lines[line_idx + 1]
            m = _KW_RE.search(next_line)
            if m:
                kind = m.group(1).lower()
                name = m.group(2)

        # 1. Try to extract existing comment from code following keyword line
        extracted_desc = None
        if line_idx + 1 < len(source_lines):
            extracted_desc = extract_comment_from_context(source_lines, line_idx + 1)

        if extracted_desc:
            desc_line = f"{indent}// {extracted_desc}\n"
            llm_generated = False
        else:
            desc_line = f"{indent}// TODO: Add description for {kind} '{name}'\n"
            llm_generated = False

            provider = kwargs.get("provider")
            if provider and getattr(provider, "is_available", False) and getattr(provider, "name", "none") != "none":
                try:
                    system_prompt = load_skill("nd_comment", __file__)
                    start_idx = max(0, line_idx - 5)
                    end_idx = min(len(source_lines), line_idx + 15)
                    context = "".join(source_lines[start_idx:end_idx])

                    prompt = f"""Given the following SystemVerilog context:
```systemverilog
{context}
```
The NaturalDocs keyword comment `{line.strip()}` is missing a description on the following line.
Generate a concise 1-line description comment for `{kind}` `{name}`.
Output ONLY a single comment line starting with `// `, e.g. `// Description of {name}`. Do not output code or markdown."""

                    response = provider.complete(prompt=prompt, system=system_prompt)
                    if response:
                        res_line = response.strip().splitlines()[0].strip()
                        if res_line.startswith("//"):
                            desc_line = f"{indent}{res_line}\n"
                            llm_generated = True
                except Exception:
                    pass

        # 2. Check if the underlying construct has parameters or ports that should be documented
        existing_has_params = False
        existing_has_ports = False
        code_idx = line_idx + 1
        while code_idx < len(source_lines):
            cline = source_lines[code_idx].strip()
            if cline.startswith("//") or cline.startswith("/*") or cline.startswith("*"):
                if "parameters:" in cline.lower():
                    existing_has_params = True
                if "ports:" in cline.lower():
                    existing_has_ports = True
                code_idx += 1
            elif cline == "":
                code_idx += 1
            else:
                break

        extra_lines = []
        if code_idx < len(source_lines):
            code_line = source_lines[code_idx]
            if kind in ("function", "task") and not existing_has_params:
                params = extract_function_params(code_line, source_lines, code_idx)
                extra_lines = build_parameters_block(params, indent)
            elif kind in ("class", "module", "interface", "checker", "program"):
                c_params, c_ports = extract_construct_params_and_ports(code_line, source_lines, code_idx)
                p_lines = build_parameters_block(c_params, indent) if not existing_has_params and c_params else []
                po_lines = build_ports_block(c_ports, indent) if not existing_has_ports and c_ports else []
                extra_lines = p_lines + po_lines

        target_line = violation["line"] + 1
        if target_line > len(source_lines) + 1:
            target_line = len(source_lines) + 1

        patch_lines = [desc_line] + extra_lines

        return FixProposal(
            rule_id="ND-012",
            file=violation["file"],
            line=target_line,
            description=f"Insert description comment for {kind} '{name}'",
            patch_lines=patch_lines,
            replace_line=None,
            is_safe=True,
            llm_generated=llm_generated,
        )
