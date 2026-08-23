# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

"""
Centralized NaturalDocs comment builder and description extractor for fixer rules.
Ensures all NaturalDocs comment insertions comply with ND-012 (non-empty description line).
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from agent.llm.skill_loader import load_skill

_ND_KEYWORD_RE = re.compile(
    r'^(?:Class|Module|Package|Interface|Function|Task|Checker|Program|Property|'
    r'Covergroup|Coverpoint|Constraint|Variable|Enum|Type|Typedef|Define|Macro|'
    r'Modport|Clocking|Bind|Assign|Section|Group|File|About|Topic)\s*:',
    re.IGNORECASE,
)

_RESERVED_WORDS = {
    # SystemVerilog keywords & directions
    "assign", "begin", "end", "function", "task", "module", "class", "package",
    "interface", "checker", "program", "property", "sequence", "covergroup", "coverpoint",
    "constraint", "clocking", "modport", "typedef", "enum", "struct", "union",
    "void", "automatic", "static", "virtual", "pure", "extern", "protected", "local",
    "const", "rand", "randc", "wire", "reg", "logic", "bit", "byte", "int", "integer",
    "time", "real", "shortint", "longint", "string", "input", "output", "inout", "ref",
    "default", "initial", "always", "always_comb", "always_ff", "always_latch", "final",
    "bind", "import", "export", "return", "item", "null",
    # NaturalDocs Tags & Labels
    "file", "about", "topic", "section", "group", "class", "module", "package", "interface",
    "program", "checker", "property", "constraint", "covergroup", "coverpoint", "function",
    "task", "variable", "enum", "type", "typedef", "define", "macro", "modport", "clocking",
    "bind", "assign"
}

def extract_name_from_violation(violation: Dict[str, Any]) -> Optional[str]:
    """
    Extract the AST-identified construct name from the linter violation message.
    Filters out keywords, tags, directions, and instruction terms.
    """
    msg = violation.get("message", "")
    if not msg:
        return None
    # Special handling for ND-019 mismatch: "Documented identifier 'X' does not match code identifier 'Y'"
    m_nd019 = re.search(r"does not match code identifier '([^']+)'", msg)
    if m_nd019:
        return m_nd019.group(1)

    candidates = re.findall(r"['`]([a-zA-Z0-9_$]+)['`]", msg)
    for c in candidates:
        if c.lower() not in _RESERVED_WORDS and not c.startswith("//"):
            return c
    return None

def extract_comment_from_context(
    source_lines: List[str],
    line_idx: int,
) -> Optional[str]:
    """
    Try to extract an existing human-written comment from the line or adjacent context.
    - Checks trailing line comment `// ...` or `/* ... */` on the same line.
    - Checks previous non-empty line if it is a plain comment (and not a file header or ND keyword).
    """
    if not (0 <= line_idx < len(source_lines)):
        return None

    line = source_lines[line_idx].strip()

    # 1. Check trailing line comment on the same line (e.g., `int m_timeout; // Timeout counter`)
    if "//" in line:
        code_part, comment_part = line.split("//", 1)
        comment_clean = comment_part.strip().rstrip("*/").strip()
        if comment_clean and not _ND_KEYWORD_RE.match(comment_clean):
            # Exclude compiler/lint directives
            if not comment_clean.lower().startswith(("verilator", "synopsys", "synthesis", "pragma")):
                return comment_clean

    # 2. Check inline block comment `/* ... */` on the same line
    m_block = re.search(r'/\*\s*(.*?)\s*\*/', line)
    if m_block:
        comment_clean = m_block.group(1).strip()
        if comment_clean and not _ND_KEYWORD_RE.match(comment_clean):
            if not comment_clean.lower().startswith(("verilator", "synopsys", "synthesis", "pragma")):
                return comment_clean

    # 3. Check previous non-empty line if it was a plain comment (and not a header / ND keyword)
    prev_idx = line_idx - 1
    while prev_idx >= 0 and source_lines[prev_idx].strip() == "":
        prev_idx -= 1
    if prev_idx >= 0:
        prev_line = source_lines[prev_idx].strip()
        if prev_line.startswith("//") and not prev_line.startswith("///"):
            comment_clean = prev_line.lstrip("/ \t").rstrip("*/").strip()
            if comment_clean and not _ND_KEYWORD_RE.match(comment_clean):
                if not comment_clean.startswith(("****", "====", "----", "####")):
                    return comment_clean

    return None

_PARAM_RE = re.compile(r'\(([^)]*)\)')

def extract_function_params(line: str, source_lines: List[str] = None, line_idx: int = None) -> List[str]:
    """
    Extract parameter names from a function/task signature.
    Handles single-line and multi-line parameter lists.
    """
    sig_line = line
    if '(' in line and ')' not in line and source_lines and line_idx is not None:
        for extra_idx in range(line_idx + 1, min(line_idx + 10, len(source_lines))):
            sig_line += " " + source_lines[extra_idx].strip()
            if ')' in source_lines[extra_idx]:
                break

    m = _PARAM_RE.search(sig_line)
    if not m or not m.group(1).strip():
        return []

    params = []
    for part in m.group(1).split(','):
        part = part.strip()
        if not part:
            continue
        # Strip default assignment (= value)
        part_clean = part.split('=', 1)[0].strip()
        # Strip array dimensions
        part_clean = re.sub(r'\[[^\]]*\]', '', part_clean).strip()
        tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', part_clean)
        if tokens:
            params.append(tokens[-1])
    return params

def build_parameters_block(params: List[str], indent: str) -> List[str]:
    """Build the // Parameters: section lines for NaturalDocs."""
    if not params:
        return []
    param_lines = [
        f"{indent}//\n",
        f"{indent}// Parameters:\n"
    ]
    for p in params:
        param_lines.append(f"{indent}//   {p} - Description for {p}\n")
    return param_lines

def extract_construct_params_and_ports(
    line: str,
    source_lines: List[str] = None,
    line_idx: int = None
) -> Tuple[List[str], List[str]]:
    """
    Extract parameter names and port names from a class, module, or interface header.
    Handles single-line and multi-line headers up to ';' or begin of body.
    """
    header_text = line
    if source_lines and line_idx is not None and ';' not in header_text and '{' not in header_text:
        for extra_idx in range(line_idx + 1, min(line_idx + 25, len(source_lines))):
            header_text += " " + source_lines[extra_idx].strip()
            if ';' in source_lines[extra_idx] or '{' in source_lines[extra_idx]:
                break

    params = []
    ports = []

    # 1. Extract parameters from #( ... )
    m_param = re.search(r'#\s*\((.*?)\)(?:\s*(?:extends|\(|;))', header_text, re.DOTALL)
    if m_param:
        param_content = m_param.group(1)
        for part in param_content.split(','):
            part = part.strip()
            if not part:
                continue
            # Strip default assignment
            part_clean = part.split('=', 1)[0].strip()
            part_clean = re.sub(r'\[[^\]]*\]', '', part_clean).strip()
            tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', part_clean)
            if tokens:
                valid_tokens = [t for t in tokens if t not in ('parameter', 'localparam', 'type', 'int', 'logic', 'bit', 'byte', 'shortint', 'longint', 'string', 'real')]
                if valid_tokens:
                    params.append(valid_tokens[-1])
                elif tokens:
                    params.append(tokens[-1])

    # 2. Extract ports from ( ... ) port list (excluding parameter list)
    text_no_params = re.sub(r'#\s*\(.*?\)', '', header_text, flags=re.DOTALL)
    m_ports = re.search(r'\((.*?)\)\s*;', text_no_params, re.DOTALL)
    if m_ports:
        port_content = m_ports.group(1)
        for part in port_content.split(','):
            part = part.strip()
            if not part:
                continue
            part_clean = part.split('=', 1)[0].strip()
            part_clean = re.sub(r'\[[^\]]*\]', '', part_clean).strip()
            tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', part_clean)
            if tokens:
                valid_tokens = [t for t in tokens if t not in ('input', 'output', 'inout', 'ref', 'wire', 'reg', 'logic', 'bit', 'byte', 'int', 'string', 'const', 'var', 'clocking')]
                if valid_tokens:
                    ports.append(valid_tokens[-1])
                elif tokens:
                    ports.append(tokens[-1])

    return params, ports

def build_ports_block(ports: List[str], indent: str) -> List[str]:
    """Build the // Ports: section lines for NaturalDocs."""
    if not ports:
        return []
    port_lines = [
        f"{indent}//\n",
        f"{indent}// Ports:\n"
    ]
    for p in ports:
        port_lines.append(f"{indent}//   {p} - Description for {p}\n")
    return port_lines

def build_construct_extra_lines(params: List[str], ports: List[str], indent: str) -> List[str]:
    """Build NaturalDocs comment sections for parameters and ports."""
    extra_lines = []
    if params:
        extra_lines.extend(build_parameters_block(params, indent))
    if ports:
        extra_lines.extend(build_ports_block(ports, indent))
    return extra_lines

def build_naturaldocs_comment(
    tag: str,
    name: str,
    indent: str,
    source_lines: List[str],
    line_idx: int,
    kind_label: Optional[str] = None,
    provider: Any = None,
    skill_name: Optional[str] = None,
    extra_lines: Optional[List[str]] = None,
) -> Tuple[str, bool]:
    """
    Builds a standard NaturalDocs comment block:
      // <Tag>: <name>
      // <description or TODO: Add description for <kind> '<name>'>
      [extra lines, e.g. Parameters...]

    Order of description resolution:
      1. Extract human-written comment from code context in file.
      2. If LLM provider is active, infer concise description from surrounding code.
      3. Deterministic fallback: '// TODO: Add description for <kind> '<name>''.
    """
    kind = kind_label or tag.lower()

    # 1. Try to extract existing description from source file
    extracted_desc = extract_comment_from_context(source_lines, line_idx)
    if extracted_desc:
        desc_line = f"{indent}// {extracted_desc}\n"
        doc_comment = f"{indent}// {tag}: {name}\n{desc_line}"
        if extra_lines:
            doc_comment += "".join(extra_lines)
        return doc_comment, False

    # 2. Try LLM provider if available
    llm_generated = False
    if provider and getattr(provider, "is_available", False) and getattr(provider, "name", "none") != "none":
        try:
            skill = load_skill(skill_name or "nd_comment", __file__) if skill_name else load_skill("nd_comment", __file__)
            start_idx = max(0, line_idx - 5)
            end_idx = min(len(source_lines), line_idx + 15)
            context = "".join(source_lines[start_idx:end_idx])

            prompt = f"""Given the following SystemVerilog context:
```systemverilog
{context}
```
Generate a NaturalDocs comment block for the `{kind}` named `{name}`.
Format must strictly be:
// {tag}: {name}
// <concise description of what this {kind} does based on the code context>

Output ONLY the NaturalDocs comment lines starting with `//`. Do not include markdown block markers or explanations."""

            response = provider.complete(prompt=prompt, system=skill)
            if response:
                lines = [l.strip() for l in response.strip().splitlines() if l.strip().startswith("//")]
                if lines:
                    doc_comment = "".join(f"{indent}{l}\n" for l in lines)
                    if not doc_comment.endswith("\n"):
                        doc_comment += "\n"
                    if extra_lines:
                        doc_comment += "".join(extra_lines)
                    return doc_comment, True
        except Exception:
            pass

    # 3. Fallback: Add TODO description
    doc_comment = f"{indent}// {tag}: {name}\n{indent}// TODO: Add description for {kind} '{name}'\n"
    if extra_lines:
        doc_comment += "".join(extra_lines)
    return doc_comment, False
