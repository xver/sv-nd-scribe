# Copyright (c) 2026 IC Verimeter. All rights reserved.
import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal

# Map each end-keyword to its matching open keyword and vice versa
_END_TO_OPEN = {
    "endmodule":    "module",
    "endclass":     "class",
    "endpackage":   "package",
    "endinterface": "interface",
    "endchecker":   "checker",
    "endprogram":   "program",
    "endtask":      "task",
    "endfunction":  "function",
    "endgroup":     "covergroup",
    "endproperty":  "property",
}
_OPEN_KEYWORDS = set(_END_TO_OPEN.values())
_END_KEYWORDS  = set(_END_TO_OPEN.keys())

# Regex to match an end keyword at the start of significant content
_END_RE = re.compile(r'\b(' + '|'.join(_END_KEYWORDS) + r')\b')


def _extract_open_construct_name(
    target_open_kw: str,
    source_lines: List[str],
    start_idx: int
) -> Optional[str]:
    """
    Extract declared identifier for construct beginning at start_idx.
    Skips prototype declarations, external methods, and typedefs.
    """
    sig_lines = []
    for j in range(start_idx, min(len(source_lines), start_idx + 10)):
        line_clean = re.sub(r'//.*$', '', source_lines[j]).strip()
        sig_lines.append(line_clean)
        if any(ch in line_clean for ch in ('(', ';', '{')):
            break
    sig = " ".join(sig_lines)

    if target_open_kw in ("function", "task"):
        # Exclude extern, external, or pure virtual prototypes
        if re.search(r'\b(extern|external|pure\s+virtual)\b', sig):
            return None
        m_head = re.search(rf'\b{target_open_kw}\b(.*?)(?:\(|;|$)', sig)
        if m_head:
            head = m_head.group(1).strip()
            # Strip bracketed dimensions like [31:0]
            head = re.sub(r'\[[^\]]*\]', '', head).strip()
            if '::' in head:
                after_colons = head.split('::')[-1].strip()
                m_id = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)$', after_colons)
                if m_id:
                    return m_id.group(1)
            tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', head)
            if tokens:
                return tokens[-1]
    else:
        # module, class, package, interface, checker, program, covergroup, prop
        if re.search(r'\btypedef\s+class\b', sig):
            return None
        m = re.search(rf'\b{target_open_kw}\s+([a-zA-Z_][a-zA-Z0-9_]*)', sig)
        if m:
            return m.group(1)
    return None


class FixNd016(BaseFixer):
    """Append : <name> label to closing end* statement using scope scan."""

    def propose(
        self,
        violation: Dict[str, Any],
        source_lines: List[str],
        config: Dict[str, Any] = None, **kwargs,
    ) -> Optional[FixProposal]:
        line_idx = violation["line"] - 1
        if not (0 <= line_idx < len(source_lines)):
            return None

        orig = source_lines[line_idx]
        stripped_orig = orig.rstrip(" \t\r\n")

        # Determine which end-keyword is on the violation line
        end_match = _END_RE.search(stripped_orig)
        if not end_match:
            return None
        end_kw = end_match.group(1)
        target_open_kw = _END_TO_OPEN.get(end_kw)
        if not target_open_kw:
            return None

        name = None

        # 1. Try AST extraction first if Verible parser is available
        try:
            from linter.verible_verilog_syntax import VeribleVerilogSyntax
            v_syntax = VeribleVerilogSyntax()
            full_source = "".join(source_lines)
            tree, _ = v_syntax.parse(full_source)
            if tree is not None:
                tag_map = {
                    "module": "kModuleDeclaration",
                    "class": "kClassDeclaration",
                    "package": "kPackageDeclaration",
                    "interface": "kInterfaceDeclaration",
                    "checker": "kCheckerDeclaration",
                    "program": "kProgramDeclaration",
                    "task": "kTaskDeclaration",
                    "function": "kFunctionDeclaration",
                    "covergroup": "kCovergroupDeclaration",
                    "property": "kPropertyDeclaration",
                }
                target_tag = tag_map.get(target_open_kw)
                if target_tag:
                    source_bytes = full_source.encode('utf-8')
                    for node in tree.find_all(
                        lambda n: getattr(n, 'tag', '') == target_tag
                    ):
                        end_off = getattr(node, 'end', None)
                        if end_off is not None:
                            end_ln = source_bytes[:end_off].count(b'\n') + 1
                            if end_ln == violation["line"]:
                                if target_open_kw in ("function", "task"):
                                    headers = list(node.find_all(
                                        lambda n: getattr(n, 'tag', '') in (
                                            'kFunctionHeader', 'kTaskHeader'
                                        )
                                    ))
                                    for h in headers:
                                        for child in getattr(h, 'children', []):
                                            ctag = getattr(child, 'tag', '')
                                            if ctag == 'kUnqualifiedId':
                                                syms = list(child.find_all(
                                                    lambda n: getattr(n, 'tag', '') == 'SymbolIdentifier'
                                                ))
                                                if syms:
                                                    name = syms[0].text.strip()
                                                    break
                                            elif ctag == 'kQualifiedId':
                                                unquals = list(child.find_all(
                                                    lambda n: getattr(n, 'tag', '') == 'kUnqualifiedId'
                                                ))
                                                if unquals:
                                                    syms = list(unquals[-1].find_all(
                                                        lambda n: getattr(n, 'tag', '') == 'SymbolIdentifier'
                                                    ))
                                                    if syms:
                                                        name = syms[0].text.strip()
                                                        break
                                        if name:
                                            break
                                else:
                                    idents = list(node.find_all(
                                        lambda n: getattr(n, 'tag', '') == 'SymbolIdentifier'
                                    ))
                                    if idents:
                                        name = idents[0].text.strip()
                                if name:
                                    break
        except Exception:
            pass

        # 2. Scope stack fallback: walk backward counting nested pairs
        if not name:
            depth = 1
            open_kw_re = re.compile(rf'\b{target_open_kw}\b')
            for idx in range(line_idx - 1, -1, -1):
                line = source_lines[idx]
                for em in _END_RE.finditer(line):
                    if em.group(1) == end_kw:
                        depth += 1
                if open_kw_re.search(line):
                    cand_name = _extract_open_construct_name(
                        target_open_kw, source_lines, idx
                    )
                    if cand_name is not None:
                        depth -= 1
                        if depth == 0:
                            name = cand_name
                            break
                if depth == 0:
                    break

        if not name:
            return None

        # Only propose if label is not already present
        if stripped_orig.endswith(f": {name}") or stripped_orig.endswith(f":{name}"):
            return None

        fixed = f"{stripped_orig} : {name}\n"
        return FixProposal(
            rule_id="ND-016",
            file=violation["file"],
            line=violation["line"],
            description=f"Append label : {name} to {end_kw} statement",
            patch_lines=[fixed],
            replace_line=orig,
            is_safe=True,
        )

