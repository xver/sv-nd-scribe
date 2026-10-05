# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

"""
Centralized NaturalDocs comment builder and description extractor for fixer rules.
Ensures all NaturalDocs comment insertions comply with ND-012 (non-empty description line).
"""

import re
import os
import sys
import json
import subprocess
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

def infer_param_description(param_name: str) -> str:
    """
    Generate an informative NaturalDocs description for a parameter based on agent knowledge and naming conventions.
    Never returns generic placeholders like 'Description for {param_name}'.
    """
    p = param_name.strip()
    p_lower = p.lower()

    # Standard UVM / SystemVerilog parameters
    known_params = {
        "phase": "UVM phase object governing test execution flow.",
        "name": "Instance name for UVM factory registration and hierarchy.",
        "parent": "Parent component in the UVM verification hierarchy.",
        "req_t": "Type parameter specifying request sequence item type.",
        "rsp_t": "Type parameter specifying response sequence item type.",
        "data_width": "Bus or payload data width in bits.",
        "addr_width": "Bus address width in bits.",
        "timeout": "Timeout limit in clock cycles before aborting.",
        "a": "First operand input.",
        "b": "Second operand input.",
        "c": "Third operand or carry input.",
        "clk": "Primary clock signal.",
        "clock": "Primary clock signal.",
        "rst_n": "Active-low asynchronous reset signal.",
        "reset_n": "Active-low asynchronous reset signal.",
        "rst": "Active-high reset signal.",
        "reset": "Active-high reset signal.",
        "vif": "Virtual interface handle for pin-level DUT interaction.",
        "result": "Computed operation result.",
    }
    if p_lower in known_params:
        return known_params[p_lower]

    clean_words = p.replace("_", " ").strip()

    # Contextual suffix / prefix pattern matching
    if p_lower.endswith("_width"):
        base = clean_words[:-6].strip()
        return f"Bit width specification for {base}."
    elif p_lower.endswith("_depth"):
        base = clean_words[:-6].strip()
        return f"Queue or buffer depth in entries for {base}."
    elif p_lower.endswith("_size"):
        base = clean_words[:-5].strip()
        return f"Total size configuration for {base}."
    elif p_lower.endswith("_count") or p_lower.startswith("num_"):
        return f"Total count of {clean_words}."
    elif p_lower.endswith("_timeout"):
        return f"Timeout threshold in clock cycles for {clean_words}."
    elif p_lower.endswith(("_t", "_type")):
        return f"Type parameter specification for {clean_words}."
    elif p_lower.endswith("_default"):
        return f"Default value configuration for {clean_words}."

    if p.isupper():
        return f"Configuration parameter specifying {clean_words.lower()}."

    return f"Input parameter {clean_words}."


def infer_port_description(port_name: str) -> str:
    """
    Generate an informative NaturalDocs description for a port or signal based on agent knowledge and naming conventions.
    Never returns generic placeholders like 'Description for {port_name}'.
    """
    p = port_name.strip()
    p_lower = p.lower()

    known_ports = {
        "clk": "Primary clock signal.",
        "clock": "Primary clock signal.",
        "rst_n": "Active-low asynchronous reset.",
        "reset_n": "Active-low asynchronous reset.",
        "rst": "Active-high reset signal.",
        "reset": "Active-high reset signal.",
        "result": "Computed operation result.",
        "vif": "Virtual interface handle for pin-level DUT interaction.",
        "a": "First operand input.",
        "b": "Second operand input.",
        "c": "Third operand or carry input.",
        "data_in": "Input data bus stream.",
        "data_out": "Output data bus stream.",
        "addr": "Address bus selection.",
        "enable": "Active-high module enable signal.",
    }
    if p_lower in known_ports:
        return known_ports[p_lower]

    clean_words = p.replace("_", " ").strip()

    if p_lower.endswith(("_clk", "_clock")):
        return f"Clock signal for {clean_words[:-4].strip()} domain."
    elif p_lower.endswith(("_rst_n", "_reset_n")):
        return f"Active-low reset signal for {clean_words[:-6].strip()} domain."
    elif p_lower.endswith(("_rst", "_reset")):
        return f"Active-high reset signal for {clean_words[:-4].strip()} domain."
    elif p_lower.endswith(("_valid", "_vld")):
        return f"Valid indicator signaling available data on {clean_words}."
    elif p_lower.endswith(("_ready", "_rdy")):
        return f"Ready handshake signal indicating receiver availability."
    elif p_lower.endswith(("_data", "_payload")):
        return f"Data payload transfer bus for {clean_words}."
    elif p_lower.endswith(("_addr", "_address")):
        return f"Memory or register address bus for {clean_words}."
    elif p_lower.endswith(("_en", "_enable")):
        return f"Enable control signal for {clean_words}."
    elif p_lower.endswith("_we"):
        return f"Write enable control strobe for {clean_words}."
    elif p_lower.endswith("_re"):
        return f"Read enable control strobe for {clean_words}."
    elif p_lower.endswith(("_err", "_error")):
        return f"Error status indicator for {clean_words}."
    elif p_lower.endswith(("_ack", "_done")):
        return f"Completion or acknowledgment signal for {clean_words}."
    elif p_lower.endswith("_req"):
        return f"Transfer request initiation signal for {clean_words}."
    elif p_lower.endswith("_rsp"):
        return f"Transfer response completion signal for {clean_words}."

    return f"Interface port signal for {clean_words}."


def build_parameters_block(params: List[str], indent: str) -> List[str]:
    """Build the // Parameters: section lines for NaturalDocs."""
    if not params:
        return []
    param_lines = [
        f"{indent}//\n",
        f"{indent}// Parameters:\n"
    ]
    for p in params:
        desc = infer_param_description(p)
        param_lines.append(f"{indent}//   {p} - {desc}\n")
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
        desc = infer_port_description(p)
        port_lines.append(f"{indent}//   {p} - {desc}\n")
    return port_lines

def build_construct_extra_lines(params: List[str], ports: List[str], indent: str) -> List[str]:
    """Build NaturalDocs comment sections for parameters and ports."""
    extra_lines = []
    if params:
        extra_lines.extend(build_parameters_block(params, indent))
    if ports:
        extra_lines.extend(build_ports_block(ports, indent))
    return extra_lines

def analyze_process_block(source_lines: List[str], line_idx: int) -> Tuple[str, str]:
    """
    Analyzes a SystemVerilog process block (initial, always, always_ff, always_comb, always_latch, final)
    by deeply examining its code structure, statements, function calls, and enclosing scope.

    Returns:
        Tuple[str, str]: (process_name, detailed_description)
    Never returns generic placeholders like 'item' or 'definition for item'.
    """
    if not (0 <= line_idx < len(source_lines)):
        return ("init_proc", "Initial process executing startup verification logic.")

    # 1. Look for enclosing construct (interface, module, class)
    enclosing_kind = ""
    enclosing_name = ""
    for pi in range(line_idx - 1, max(-1, line_idx - 60), -1):
        prev = source_lines[pi].strip()
        em = re.search(r"\b(interface|module|class|package)\s+([a-zA-Z_][a-zA-Z0-9_]*)", prev)
        if em:
            enclosing_kind = em.group(1).lower()
            enclosing_name = em.group(2)
            break

    # 2. Determine process keyword
    proc_kw = "process"
    for ci in range(line_idx, min(len(source_lines), line_idx + 3)):
        pkm = re.search(r"\b(initial|always_ff|always_comb|always_latch|always|final)\b", source_lines[ci])
        if pkm:
            proc_kw = pkm.group(1)
            break

    # 3. Collect lines of the process body (up to 45 lines or matching end)
    block_lines = []
    explicit_name = None
    nesting = 0
    started = False

    for ci in range(line_idx, min(len(source_lines), line_idx + 45)):
        b_line = source_lines[ci]
        block_lines.append(b_line)

        # Check for label on begin or end
        bm = re.search(r"\bbegin\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)", b_line)
        if bm and not explicit_name:
            explicit_name = bm.group(1)

        em = re.search(r"\bend\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)", b_line)
        if em and not explicit_name:
            explicit_name = em.group(1)

        if re.search(r"\bbegin\b", b_line):
            nesting += 1
            started = True
        if re.search(r"\bend\b", b_line):
            nesting -= 1
            if started and nesting <= 0:
                break

    # Check preceding lines (up to 6 lines above) for enclosing generate blocks:
    gen_label = None
    for pi in range(max(0, line_idx - 6), line_idx):
        gm = re.search(r"\bbegin\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)", source_lines[pi])
        if gm:
            gen_label = gm.group(1)
            break

    block_text = " ".join(block_lines)

    # 4. Deep Inspection of Process Body & Actions

    # Pattern A: Virtual Interface Binding / Agent Connection
    is_vif_binding = (
        "set_vif" in block_text or
        ".vif" in block_text or
        ("m_config" in block_text and any(k in block_text for k in ("CONNECT_ACTIVE", "CONNECT_PASSIVE", "watchdog_if", "rst_if", "clk_if")))
    )
    if is_vif_binding:
        # 1. Watchdog interface binding and clock forcing
        if "watchdog" in block_text.lower():
            proc_name = explicit_name or (gen_label if gen_label else "watchdog_connect")
            if "force" in block_text:
                desc = (
                    "Retrieves testbench configuration object. "
                    "Binds watchdog virtual interface to watchdog agent configuration. "
                    "Forces watchdog clock to primary clock signal (clk_if[0].clk)."
                )
            else:
                desc = (
                    "Retrieves testbench configuration object. "
                    "Binds watchdog virtual interface to watchdog agent configuration."
                )
            return (proc_name, desc)

        # 2. Reset interface binding
        if "rst" in block_text.lower() or "reset" in block_text.lower():
            proc_name = explicit_name or "rst_vif_connect"
            desc = (
                "Retrieves testbench configuration object. "
                "Binds physical reset virtual interface (rst_if) to reset agent configuration."
            )
            return (proc_name, desc)

        # 3. Clock interface binding
        if "clk" in block_text.lower() or "clock" in block_text.lower():
            proc_name = explicit_name or "clk_vif_connect"
            desc = (
                "Retrieves testbench configuration object. "
                "Binds physical clock virtual interface (clk_if) to clock agent configuration."
            )
            return (proc_name, desc)

        # 4. Abstract agent slot binding (e.g. ABS_AGENT0)
        agent_match = re.search(r"\b(?:TB_TEMPLATE_)?(ABS_AGENT\w*|[a-zA-Z0-9_]*_agent\w*)\b", block_text, re.IGNORECASE)
        agent_slot = ""
        if agent_match:
            cand = agent_match.group(1)
            cand = re.sub(r'(_link_if|_if)$', '', cand, flags=re.I)
            if cand.lower() not in ("tb_template", "agent", "agents", "link"):
                agent_slot = cand.upper()

        if not agent_slot and enclosing_name:
            am = re.search(r"(?:tb_template_)?(abs_agent\w*?)(?:_link_if|_if)?$", enclosing_name, re.IGNORECASE)
            if am:
                agent_slot = am.group(1).upper()

        proc_name = explicit_name or (f"{agent_slot.lower()}_connect" if agent_slot else "vif_connect")
        slot_desc = f" for {agent_slot}" if agent_slot else ""
        desc = (
            f"Retrieves top-level testbench configuration object. "
            f"Evaluates connection mode{slot_desc} and binds virtual interface to agent configuration in active or passive mode."
        )
        return (proc_name, desc)

    # Pattern B: Clock Generation
    if ("forever" in block_text or "#" in block_text) and ("~" in block_text or "clk" in block_text.lower() or "clock" in block_text.lower()):
        clk_m = re.search(r"([a-zA-Z0-9_]*clk[a-zA-Z0-9_]*|[a-zA-Z0-9_]*clock[a-zA-Z0-9_]*)\s*=\s*~\s*\1", block_text, re.IGNORECASE)
        clk_name = clk_m.group(1) if clk_m else "clk"
        proc_name = explicit_name or f"{clk_name}_gen"
        desc = f"Initializes and generates primary {clk_name} signal with periodic toggling."
        return (proc_name, desc)

    # Pattern C: Reset Sequencing
    if re.search(r"\b(rst_n|reset_n|rst|reset)\b", block_text, re.IGNORECASE) and ("= 0" in block_text or "<= 0" in block_text) and ("#" in block_text):
        rst_m = re.search(r"\b(rst_n|reset_n|rst|reset)\b", block_text, re.IGNORECASE)
        rst_name = rst_m.group(1) if rst_m else "rst_n"
        proc_name = explicit_name or f"{rst_name}_seq"
        desc = f"Drives initial {rst_name} reset sequence to initialize design registers and testbench state."
        return (proc_name, desc)

    # Pattern D: UVM Test Kickoff
    if "run_test" in block_text:
        proc_name = explicit_name or "run_test_proc"
        desc = "Initiates UVM test phase execution and starts testbench simulation."
        return (proc_name, desc)

    # Pattern E: UVM Configuration DB Setup
    if "uvm_config_db" in block_text:
        proc_name = explicit_name or "config_db_init"
        desc = "Populates and registers interface handles into the UVM configuration database."
        return (proc_name, desc)

    # Pattern F: Sequential State / Register Update (always_ff)
    if proc_kw == "always_ff" or (proc_kw == "always" and "@(" in block_text and "posedge" in block_text):
        tgt_m = re.search(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*<=", block_text)
        tgt_name = tgt_m.group(1) if tgt_m else "state"
        clean_tgt = tgt_name.replace("_", " ").strip()
        proc_name = explicit_name or f"{tgt_name}_seq"
        desc = f"Sequential process updating {clean_tgt} synchronously on clock edges with reset handling."
        return (proc_name, desc)

    # Pattern G: Combinational Logic (always_comb)
    if proc_kw == "always_comb":
        tgt_m = re.search(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=", block_text)
        tgt_name = tgt_m.group(1) if tgt_m else "comb"
        clean_tgt = tgt_name.replace("_", " ").strip()
        proc_name = explicit_name or f"{tgt_name}_comb"
        desc = f"Combinational logic process evaluating and driving {clean_tgt} based on input transitions."
        return (proc_name, desc)

    # Pattern H: Specific initial block actions
    if proc_kw == "initial":
        statements = []
        for bl in block_lines:
            s = bl.strip()
            if not s or s.startswith(("//", "/*", "*")) or s in ("begin", "end", "initial", "initial begin"):
                continue
            s_clean = re.sub(r'^(?:begin\s*:\s*\w+|end\s*:\s*\w+)\s*;?', '', s).strip()
            if s_clean and s_clean not in ("begin", "end"):
                statements.append(s_clean.rstrip(";"))

        actions = []
        if any("get_m_config" in st or "get_config" in st for st in statements):
            actions.append("Retrieves testbench configuration object.")

        assign_stmts = [st for st in statements if ("=" in st or "<=" in st) and "get_m_config" not in st and "uvm_info" not in st]
        if assign_stmts:
            lhs_signals = [re.split(r'\s*<=|\s*=', st)[0].strip() for st in assign_stmts[:3]]
            clean_signals = ", ".join(s for s in lhs_signals if s)
            if clean_signals:
                actions.append(f"Initializes signals: {clean_signals}.")

        info_stmts = [st for st in statements if "uvm_info" in st]
        if info_stmts and not assign_stmts:
            im = re.search(r'`uvm_info\s*\([^,]+,\s*"([^"]+)"', info_stmts[0])
            if im:
                clean_info = re.sub(r'^(?:START|STARTING)\s*', '', im.group(1), flags=re.I).strip()
                actions.append(f"Executes startup sequence: {clean_info}.")

        calls = [st for st in statements if "(" in st and "=" not in st and "uvm_" not in st and "get_m_config" not in st]
        if calls and not assign_stmts:
            call_name = re.split(r'\s*\(', calls[0])[0].strip()
            actions.append(f"Calls {call_name} to execute initialization.")

        if actions:
            name_cand = explicit_name or (gen_label if gen_label else (enclosing_name if enclosing_name else "init"))
            proc_name = f"{name_cand}_connect" if ("connect" in " ".join(actions).lower() and not name_cand.endswith("connect")) else (explicit_name or (gen_label if gen_label else "init_proc"))
            return (proc_name, " ".join(actions))

        target_name = explicit_name or (gen_label if gen_label else (enclosing_name if enclosing_name else "initial_proc"))
        return (target_name, f"Executes initialization routine for {target_name.replace('_', ' ')}.")

    # Pattern I: Final Block
    if proc_kw == "final":
        proc_name = explicit_name or "final_proc"
        return (proc_name, "Executes end-of-simulation checks and status reporting.")

    # Fallback
    target_name = explicit_name or (gen_label if gen_label else (enclosing_name if enclosing_name else f"{proc_kw}_proc"))
    return (target_name, f"Executes verification operations for {target_name.replace('_', ' ')}.")


def analyze_assign_statement(source_lines: List[str], line_idx: int) -> Tuple[str, str]:
    """
    Analyzes a SystemVerilog continuous assignment (assign <lhs> = <rhs>;)
    deeply inspecting LHS target, RHS expression, and enclosing scope.

    Returns:
        Tuple[str, str]: (target_name, detailed_description)
    Never returns generic placeholders or boilerplate like 'SystemVerilog assignment definition for...'.
    """
    if not (0 <= line_idx < len(source_lines)):
        return ("assign_target", "Continuous assignment driving verification signal.")

    # Find the line with assign statement (check line_idx or subsequent lines)
    assign_line = ""
    found_idx = line_idx
    for ci in range(max(0, line_idx - 1), min(len(source_lines), line_idx + 5)):
        if "assign" in source_lines[ci]:
            assign_line = source_lines[ci]
            found_idx = ci
            break
    if not assign_line and 0 <= line_idx < len(source_lines):
        assign_line = source_lines[line_idx]

    # Accumulate full statement until ';' (in case it spans multiple lines)
    stmt = assign_line.strip()
    for ci in range(found_idx + 1, min(len(source_lines), found_idx + 6)):
        if ";" in stmt:
            break
        stmt += " " + source_lines[ci].strip()

    # Parse LHS and RHS
    m = re.search(
        r"\bassign\s+(?:(?:\([^)]*\)|#[0-9a-zA-Z_()#\s]+)\s+)*\{?\s*([^=;]+?)\s*=\s*(.+?);",
        stmt,
    )
    if not m:
        m = re.search(
            r"\bassign\s+(?:(?:\([^)]*\)|#[0-9a-zA-Z_()#\s]+)\s+)*\{?\s*([^=;]+?)\s*=\s*(.+)$",
            stmt,
        )

    if m:
        raw_lhs = m.group(1).strip()
        raw_rhs = m.group(2).strip().rstrip(";")
    else:
        raw_lhs = "item"
        raw_rhs = ""

    # Clean target name
    target_name = raw_lhs if raw_lhs and raw_lhs != "item" else "target_signal"
    parts = target_name.split(".")
    leaf_signal = parts[-1].strip()
    parent_scope = parts[-2].strip() if len(parts) >= 2 else ""

    # Form human-readable component name
    comp_desc = ""
    if parent_scope:
        comp_clean = re.sub(r"^[mp]_", "", parent_scope)
        comp_clean = re.sub(r"_if$", "", comp_clean)
        comp_desc = comp_clean.upper() if "agent" in comp_clean.lower() else comp_clean.replace("_", " ")

    rhs_clean = raw_rhs.strip()

    # 1. Handshake ready tie-off (1'b1, 1, '1)
    if "ready" in leaf_signal.lower() and re.match(r"^(?:1'b1|1|'1|1'h1)\b", rhs_clean):
        if comp_desc:
            return (target_name, f"Ties the {comp_desc} ready handshake signal permanently high, indicating responder is always ready to receive transactions.")
        return (target_name, f"Ties the {leaf_signal} ready handshake signal permanently high, indicating responder is always ready to accept transactions.")

    # 2. Handshake valid tie-off (1'b1, 1, '1)
    if "valid" in leaf_signal.lower() and re.match(r"^(?:1'b1|1|'1|1'h1)\b", rhs_clean):
        if comp_desc:
            return (target_name, f"Permanently asserts the {comp_desc} valid signal high, indicating continuous data availability.")
        return (target_name, f"Permanently asserts {leaf_signal} high, indicating continuous data availability.")

    # 3. Constant high / enable
    if re.match(r"^(?:1'b1|1|'1|1'h1)\b", rhs_clean):
        if comp_desc:
            return (target_name, f"Permanently ties {comp_desc} {leaf_signal} high (1'b1) for active enable.")
        return (target_name, f"Permanently ties {target_name} high (1'b1) for continuous active assertion.")

    # 4. Constant low / disable / reset (1'b0, 0, '0)
    if re.match(r"^(?:1'b0|0|'0|1'h0)\b", rhs_clean):
        if "rst" in leaf_signal.lower() or "reset" in leaf_signal.lower():
            return (target_name, f"Permanently ties {target_name} low to hold block out of reset.")
        if comp_desc:
            return (target_name, f"Permanently ties {comp_desc} {leaf_signal} low (1'b0) to inactive/idle state.")
        return (target_name, f"Permanently ties {target_name} low (1'b0) to inactive/idle state.")

    # 5. Data bus mirroring / passthrough
    if "data" in leaf_signal.lower() and ("data" in rhs_clean.lower() or "last_" in rhs_clean.lower()):
        if comp_desc:
            return (target_name, f"Mirrors captured transfer data from {rhs_clean} onto {comp_desc} data bus for downstream observation.")
        return (target_name, f"Mirrors captured transfer data from {rhs_clean} onto {target_name} for downstream verification.")

    # 6. Multiplexing / Ternary operator
    if "?" in rhs_clean and ":" in rhs_clean:
        return (target_name, f"Multiplexes data onto {target_name} based on active arbitration condition.")

    # 7. Comparison / status flag
    if any(op in rhs_clean for op in ("!=", "==", ">=", "<=", ">", "<")):
        return (target_name, f"Asserts {target_name} when evaluation condition ({rhs_clean}) is satisfied.")

    # 8. Concatenation
    if rhs_clean.startswith("{") and rhs_clean.endswith("}"):
        return (target_name, f"Combines sub-fields into {target_name} bus vector from {rhs_clean}.")

    # 9. Generic signal drive
    if comp_desc:
        return (target_name, f"Continuously drives {comp_desc} {leaf_signal} from {rhs_clean}.")
    return (target_name, f"Continuously drives {target_name} with signal {rhs_clean}.")


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
    deep_synth: bool = False,
) -> Tuple[str, bool]:
    """
    Builds a standard NaturalDocs comment block:
      // <Tag>: <name>
      // <description or TODO: Add description for <kind> '<name>'>
      [extra lines, e.g. Parameters...]

    Order of description resolution:
      1. Extract human-written comment from code context in file.
      2. If LLM provider is active, infer concise description from surrounding code.
      3. Deep deterministic synthesis for process blocks or assignments (when deep_synth=True).
      4. Deterministic fallback: '// TODO: Add description for <kind> '<name>''.
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

    # 3. Deep deterministic synthesis for processes
    if kind == "process" or tag.lower() == "process":
        import textwrap
        inferred_name, inferred_desc = analyze_process_block(source_lines, line_idx)
        actual_name = name if (name and name != "item") else inferred_name
        doc_lines = [f"{indent}// {tag}: {actual_name}\n"]
        wrap_width = max(40, 78 - len(indent) - 5)
        for sentence in inferred_desc.split(". "):
            sentence = sentence.strip()
            if not sentence:
                continue
            if not sentence.endswith("."):
                sentence += "."
            wrapped = textwrap.wrap(sentence, width=wrap_width)
            for w in wrapped:
                doc_lines.append(f"{indent}//   {w}\n")
        if extra_lines:
            doc_lines.extend(extra_lines)
        return "".join(doc_lines), False

    # 3b. Deep deterministic synthesis for assignments (when deep_synth is enabled)
    if deep_synth and (kind in ("assign", "assignment") or tag.lower() == "assign"):
        import textwrap
        inferred_name, inferred_desc = analyze_assign_statement(source_lines, line_idx)
        actual_name = name if (name and name not in ("item", "tb_if", "assign")) else inferred_name
        doc_lines = [f"{indent}// {tag}: {actual_name}\n"]
        wrap_width = max(40, 78 - len(indent) - 5)
        for sentence in inferred_desc.split(". "):
            sentence = sentence.strip()
            if not sentence:
                continue
            if not sentence.endswith("."):
                sentence += "."
            wrapped = textwrap.wrap(sentence, width=wrap_width)
            for w in wrapped:
                doc_lines.append(f"{indent}//   {w}\n")
        if extra_lines:
            doc_lines.extend(extra_lines)
        return "".join(doc_lines), False

    # 4. Fallback: Add TODO [SVND] description
    doc_comment = f"{indent}// {tag}: {name}\n{indent}// TODO [SVND]: Add description for {kind} '{name}'\n"
    if extra_lines:
        doc_comment += "".join(extra_lines)
    return doc_comment, False


def _has_valid_email(val: str) -> bool:
    if not val:
        return False
    return bool(re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9_.-]+\.[a-zA-Z0-9-.]+", val))


def get_git_config_author(dir_path: Optional[str] = None) -> Optional[str]:
    """
    Attempt to read author name and email from Git configuration in dir_path or current directory.
    Checks repository local config first, then global config.
    Returns: 'Name <email>' if email is present, or None if no valid email.
    """
    cwd = dir_path if (dir_path and os.path.exists(dir_path)) else os.getcwd()
    if os.path.isfile(cwd):
        cwd = os.path.dirname(cwd)

    name = ""
    email = ""
    try:
        res = subprocess.run(
            ["git", "config", "user.name"],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            name = res.stdout.strip()
    except Exception:
        pass

    try:
        res = subprocess.run(
            ["git", "config", "user.email"],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            email = res.stdout.strip()
    except Exception:
        pass

    if name and email and _has_valid_email(email):
        return f"{name} <{email}>"
    if email and _has_valid_email(email):
        return email
    return None


def get_vscode_setting(setting_key: str, start_dir: Optional[str] = None) -> Optional[str]:
    """
    Look for .vscode/settings.json in start_dir and up to 10 parent directories.
    Returns the string value for setting_key if configured.
    """
    curr = start_dir if (start_dir and os.path.exists(start_dir)) else os.getcwd()
    if os.path.isfile(curr):
        curr = os.path.dirname(curr)

    for _ in range(10):
        settings_path = os.path.join(curr, ".vscode", "settings.json")
        if os.path.isfile(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                val = data.get(setting_key)
                if val and isinstance(val, str) and val.strip() and "TODO" not in val:
                    return val.strip()
            except Exception:
                pass
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    return None


def resolve_company(
    file_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """
    Resolve the company name from explicit config, VS Code settings, or environment.
    Falls back to 'TODO_COMPANY' if not configured.
    """
    agent_cfg = (config or {}).get("agent", config or {})
    header_defaults = agent_cfg.get("header_defaults", {}) if isinstance(agent_cfg, dict) else {}
    explicit_company = (
        (header_defaults.get("company") if isinstance(header_defaults, dict) else None)
        or agent_cfg.get("header_company")
        or (config.get("company") if isinstance(config, dict) else None)
    )
    if (
        explicit_company
        and isinstance(explicit_company, str)
        and explicit_company.strip()
        and "TODO" not in explicit_company
        and not explicit_company.startswith("${")
    ):
        return explicit_company.strip(), "explicit_config"

    env_company = os.environ.get("SV_ND_SCRIBE_COMPANY", "").strip()
    if env_company and "TODO" not in env_company:
        return env_company, "env_var"

    file_dir = os.path.dirname(os.path.abspath(file_path)) if file_path else os.getcwd()
    vscode_company = get_vscode_setting("sv-nd-scribe.company", file_dir)
    if vscode_company:
        return vscode_company, "vscode_settings"

    return "TODO_COMPANY", "fallback"


def resolve_legal(
    file_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """
    Resolve legal/license notice from explicit config, VS Code settings, or environment.
    Falls back to 'TODO_LEGAL' if not configured.
    """
    agent_cfg = (config or {}).get("agent", config or {})
    header_defaults = agent_cfg.get("header_defaults", {}) if isinstance(agent_cfg, dict) else {}
    explicit_legal = (
        (header_defaults.get("legal") if isinstance(header_defaults, dict) else None)
        or agent_cfg.get("header_legal")
        or (config.get("legal") if isinstance(config, dict) else None)
    )
    if (
        explicit_legal
        and isinstance(explicit_legal, str)
        and explicit_legal.strip()
        and "TODO" not in explicit_legal
        and not explicit_legal.startswith("${")
    ):
        return explicit_legal.strip(), "explicit_config"

    env_legal = os.environ.get("SV_ND_SCRIBE_LEGAL", "").strip()
    if env_legal and "TODO" not in env_legal:
        return env_legal, "env_var"

    file_dir = os.path.dirname(os.path.abspath(file_path)) if file_path else os.getcwd()
    vscode_legal = get_vscode_setting("sv-nd-scribe.legal", file_dir)
    if vscode_legal:
        return vscode_legal, "vscode_settings"

    return "TODO_LEGAL", "fallback"


def resolve_author(
    file_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """
    Resolve author string following precedence:
      1. Explicit config override (if contains valid email)
      2. Environment variable: SV_ND_SCRIBE_AUTHOR (if contains valid email)
      3. VS Code settings: sv-nd-scribe.author in .vscode/settings.json (if contains valid email)
      4. Git config: user.name and user.email (if email is valid)
      5. Fallback: 'TODO_AUTHOR'

    Note: Any author value lacking a valid email address is rejected and defaults to 'TODO_AUTHOR'.
    """
    file_dir = os.path.dirname(os.path.abspath(file_path)) if file_path else os.getcwd()

    agent_cfg = (config or {}).get("agent", config or {})
    header_defaults = agent_cfg.get("header_defaults", {}) if isinstance(agent_cfg, dict) else {}
    explicit_author = (
        (header_defaults.get("author") if isinstance(header_defaults, dict) else None)
        or agent_cfg.get("header_author")
        or (config.get("author") if isinstance(config, dict) else None)
    )
    if (
        explicit_author
        and isinstance(explicit_author, str)
        and explicit_author.strip()
        and "TODO" not in explicit_author
        and not explicit_author.startswith("${")
    ):
        if _has_valid_email(explicit_author.strip()):
            return explicit_author.strip(), "explicit_config"
        git_auth = get_git_config_author(file_dir)
        if git_auth and "<" in git_auth:
            git_email = git_auth.split("<")[-1].rstrip(">").strip()
            return f"{explicit_author.strip()} <{git_email}>", "explicit_config"

    env_author = os.environ.get("SV_ND_SCRIBE_AUTHOR", "").strip()
    if env_author and "TODO" not in env_author:
        if _has_valid_email(env_author):
            return env_author, "env_var"

    vscode_author = get_vscode_setting("sv-nd-scribe.author", file_dir)
    if vscode_author:
        if _has_valid_email(vscode_author):
            return vscode_author, "vscode_settings"
        # If vscode_author is just a name, try pairing with git email
        git_auth = get_git_config_author(file_dir)
        if git_auth and "<" in git_auth:
            git_email = git_auth.split("<")[-1].rstrip(">").strip()
            return f"{vscode_author} <{git_email}>", "vscode_settings"

    git_author = get_git_config_author(file_dir)
    if git_author:
        return git_author, "git_config"

    return "TODO_AUTHOR", "fallback"


def clean_nested_comment_markers(text: str) -> str:
    """
    Remove redundant comment markers from a text or comment line:
      - Strips redundant leading '//' from lines inside block comments
      - Strips redundant nested '/*' or '*/'
      - Strips redundant multiple slashes ('// //', '////')
    """
    if not text:
        return ""
    # Strip nested // e.g. "// text" or "  // text"
    cleaned = re.sub(r'^\s*(?:\*\s*)?//\s*', '', text)
    # Strip nested /* or */
    cleaned = re.sub(r'/\*|\*/', '', cleaned)
    # Strip redundant leading slashes
    cleaned = re.sub(r'^\s*//\s*', '', cleaned)
    return cleaned.strip()


def clean_all_nested_comments(source_lines: List[str]) -> Tuple[List[str], int]:
    """
    Scan source_lines, identify all nested comments in block comments and single-line comments,
    and remove redundant comment markers. Also deduplicates duplicate stub comment blocks.
    Returns (modified_lines, change_count).
    """
    modified = list(source_lines)
    changes = 0
    i = 0

    while i < len(modified):
        line = modified[i]
        stripped = line.strip()

        # 1. Detect block comment: /* ... */
        if stripped.startswith("/*"):
            start_idx = i
            base_ind = len(line) - len(line.lstrip())
            block_indent = " " * (base_ind + 2)

            # Find matching */
            end_idx = i
            while end_idx < len(modified):
                if "*/" in modified[end_idx]:
                    break
                end_idx += 1

            if end_idx >= len(modified):
                i += 1
                continue

            # First check if this block comment is a duplicate stub followed immediately by another comment
            # e.g. /* Function: foo ... */ followed by // Function: foo ...
            block_slice = modified[start_idx : end_idx + 1]
            block_text = "".join(block_slice)
            kw_match = re.search(r'\b(Function|Task|Class|Module|Interface|Variable):\s*(\w+)', block_text, re.IGNORECASE)

            is_dup_stub = False
            if kw_match and (end_idx - start_idx) <= 4:
                name = kw_match.group(2).lower()
                next_non_empty = end_idx + 1
                while next_non_empty < len(modified) and modified[next_non_empty].strip() == "":
                    next_non_empty += 1
                if next_non_empty < len(modified):
                    follow_line = modified[next_non_empty].strip()
                    m_follow = re.search(r'//\s*(Function|Task|Class|Module|Interface|Variable):\s*(\w+)', follow_line, re.IGNORECASE)
                    if m_follow and m_follow.group(2).lower() == name:
                        tag_block = kw_match.group(1).capitalize()
                        tag_follow = m_follow.group(1).capitalize()
                        del modified[start_idx:next_non_empty]
                        changes += 1
                        is_dup_stub = True
                        if tag_block != tag_follow and tag_block in ("Function", "Task") and tag_follow in ("Function", "Task"):
                            decl_idx = start_idx
                            while decl_idx < len(modified) and (modified[decl_idx].strip().startswith("//") or modified[decl_idx].strip() == ""):
                                decl_idx += 1
                            if decl_idx < len(modified):
                                decl_text = modified[decl_idx]
                                correct_tag = "Function" if re.search(r'\bfunction\b', decl_text, re.I) or name == "new" else ("Task" if re.search(r'\btask\b', decl_text, re.I) else tag_block)
                                fixed_line = re.sub(rf'//\s*{tag_follow}:', f'// {correct_tag}:', modified[start_idx])
                                fixed_line = re.sub(rf'\b{tag_follow.lower()}\s*\'?{name}\'?', f'{correct_tag.lower()} \'{name}\'', fixed_line, flags=re.I)
                                if fixed_line != modified[start_idx]:
                                    modified[start_idx] = fixed_line

            if not is_dup_stub:
                for row in range(start_idx, end_idx + 1):
                    row_line = modified[row]
                    row_stripped = row_line.strip()
                    if row == start_idx and row_stripped.startswith("/*") and not re.search(r'/\*.*?\b//', row_line):
                        continue

                    new_line = row_line
                    m_star = re.match(r"^(\s*\*\s*)//\s*(.*)$", new_line)
                    if m_star:
                        prefix = m_star.group(1)
                        content = m_star.group(2)
                        new_line = f"{prefix}{content}\n" if content else f"{prefix}\n"
                    else:
                        m_nested = re.match(r"^(\s*)//\s*(.*)$", new_line)
                        if m_nested:
                            leading_ws = m_nested.group(1)
                            content = m_nested.group(2)
                            target_indent = leading_ws
                            if len(leading_ws) < len(block_indent):
                                target_indent = block_indent
                            new_line = f"{target_indent}{content}\n" if content else f"{target_indent}\n"

                    if "/*" in new_line and not new_line.lstrip().startswith("/*"):
                        new_line = re.sub(r'/\*\s*', '', new_line)

                    new_line = re.sub(r'((?://|/\*|\*|)\s*[A-Za-z0-9_]+):([^\s\n/])', r'\1: \2', new_line)

                    if new_line != row_line:
                        modified[row] = new_line
                        changes += 1

                i = end_idx + 1
            continue

        # 2. Single-line comment checks outside block comments
        elif stripped.startswith("//"):
            new_line = line
            if re.match(r"^\s*//\s*//", new_line):
                new_line = re.sub(r"^(\s*//)\s*//\s*", r"\1 ", new_line)
            elif re.match(r"^\s*/{4,}\s*[a-zA-Z0-9_]", new_line):
                new_line = re.sub(r"^(\s*)/{4,}\s*", r"\1// ", new_line)
            elif re.match(r"^\s*//\s*/\*", new_line):
                if "*/" in new_line:
                    new_line = re.sub(r"^(\s*//)\s*/\*\s*(.*?)\s*\*/\s*$", r"\1 \2\n", new_line.rstrip("\r\n")) + "\n"
                else:
                    new_line = re.sub(r"^(\s*//)\s*/\*\s*", r"\1 ", new_line)

            new_line = re.sub(r'((?://|/\*|\*|)\s*[A-Za-z0-9_]+):([^\s\n/])', r'\1: \2', new_line)

            # Check if this single-line comment is a Function/Task header whose tag doesn't match following code
            m_fn_task = re.match(r'^(\s*//\s*)(Function|Task)(:\s*([a-zA-Z_][a-zA-Z0-9_]*))', new_line, re.IGNORECASE)
            if m_fn_task:
                cur_tag = m_fn_task.group(2).capitalize()
                fn_name = m_fn_task.group(4)
                # Look ahead to code declaration
                decl_idx = i + 1
                while decl_idx < len(modified) and (modified[decl_idx].strip().startswith("//") or modified[decl_idx].strip() == ""):
                    decl_idx += 1
                if decl_idx < len(modified):
                    decl_text = modified[decl_idx]
                    correct_tag = None
                    if (re.search(r'\bfunction\b', decl_text, re.I) or fn_name.lower() == "new") and cur_tag == "Task":
                        correct_tag = "Function"
                    elif re.search(r'\btask\b', decl_text, re.I) and cur_tag == "Function":
                        correct_tag = "Task"

                    if correct_tag and correct_tag != cur_tag:
                        new_line = re.sub(rf'//\s*{cur_tag}:', f'// {correct_tag}:', new_line)
                        # Also check description line right below if it has "description for task '...'"
                        if i + 1 < len(modified) and modified[i + 1].strip().startswith("//"):
                            mod_desc = re.sub(rf'\b{cur_tag.lower()}\s*\'?{fn_name}\'?', f'{correct_tag.lower()} \'{fn_name}\'', modified[i + 1], flags=re.I)
                            if mod_desc != modified[i + 1]:
                                modified[i + 1] = mod_desc

            if new_line != line:
                modified[i] = new_line
                changes += 1

        i += 1

    return modified, changes

