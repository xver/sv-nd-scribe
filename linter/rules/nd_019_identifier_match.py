# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List, Optional
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity

VAR_KEYWORDS = ["Variable", "variable", "var", "Var", "parameter", "localparam", "port", "signal", "event", "instance", "field", "item"]
TYPE_KEYWORDS = ["Type", "type", "Typedef", "typedef", "Enum", "enum", "Struct", "struct", "Union", "union"]
MACRO_KEYWORDS = ["define", "Define", "Macro", "macro"]
FUNC_KEYWORDS = ["Function", "function", "Method", "method"]
TASK_KEYWORDS = ["Task", "task", "Method", "method"]
BIND_KEYWORDS = ["Bind", "bind"]
ASSIGN_KEYWORDS = ["Assign", "assign"]
SEQ_KEYWORDS = ["Sequence", "sequence"]


class IdentifierMatchRule(BaseRule):
    """
    [ND-019] Identifier Match Rule
    The identifier in a NaturalDocs comment MUST match the code identifier.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-019]"

    @property
    def description(self) -> str:
        return "The identifier in a NaturalDocs comment MUST match the code identifier."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def _get_comments(self, node: Any, file_content: str, context: Any, line_num: int) -> List[str]:
        comments = []
        if node is not None and context is not None:
            comments = self._comments_before_node(node, file_content, context)
        if not comments:
            comments = self._extract_comments_from_text(file_content, line_num)
        if not comments:
            lines = file_content.splitlines()
            if 1 <= line_num <= len(lines):
                line = lines[line_num - 1]
                if "//" in line:
                    comments = ["//" + line.split("//", 1)[1]]
        return comments

    def _extract_node_code_name(self, node: Any, pattern: str) -> Optional[str]:
        text = getattr(node, 'text', '') or ""
        clean_lines = [l for l in text.splitlines() if not l.strip().startswith(("//", "/*", "*"))]
        clean_text = "\n".join(clean_lines)
        m = re.search(pattern, clean_text)
        if m:
            return m.group(1)
        if hasattr(node, 'find_all'):
            try:
                id_nodes = list(node.find_all(lambda n: getattr(n, 'tag', '') == 'SymbolIdentifier'))
                if id_nodes:
                    return id_nodes[0].text.strip()
            except Exception:
                pass
        return None

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        tag_to_keyword = {
            "kClassDeclaration": ("class", ["Class", "class"], r"\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kPackageDeclaration": ("package", ["Package", "package"], r"\bpackage\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kInterfaceDeclaration": ("interface", ["Interface", "interface"], r"\binterface\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kModuleDeclaration": ("module", ["Module", "module"], r"\bmodule\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kFunctionDeclaration": ("function", FUNC_KEYWORDS, r"\bfunction\s+(?:automatic\s+)?(?:void\s+|[\w:<>\[\]]+\s+)?([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kTaskDeclaration": ("task", TASK_KEYWORDS, r"\btask\s+(?:automatic\s+)?([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kCovergroupDeclaration": ("covergroup", ["Covergroup", "covergroup"], r"\bcovergroup\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kCheckerDeclaration": ("checker", ["Checker", "checker"], r"\bchecker\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kClockingDeclaration": ("clocking", ["Clocking", "clocking"], r"\bclocking\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kModportDeclaration": ("modport", ["Modport", "modport"], r"\bmodport\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kPropertyDeclaration": ("property", ["Property", "property"], r"\bproperty\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kSequenceDeclaration": ("sequence", SEQ_KEYWORDS, r"\bsequence\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kConstraintDeclaration": ("constraint", ["Constraint", "constraint"], r"\bconstraint\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kProgramDeclaration": ("program", ["Program", "program"], r"\bprogram\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            "kBindDirective": ("bind", BIND_KEYWORDS, r"\bbind\s+(?:[a-zA-Z_][a-zA-Z0-9_]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)?\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|$)"),
            "kBindDeclaration": ("bind", BIND_KEYWORDS, r"\bbind\s+(?:[a-zA-Z_][a-zA-Z0-9_]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)?\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|$)"),
            "kContinuousAssignmentStatement": ("assign", ASSIGN_KEYWORDS, r"\bassign\s+(?:#\s*\([^)]*\)\s*)?([a-zA-Z_][a-zA-Z0-9_]*)"),
        }

        # AST node driven check
        has_ast = False
        for tag, (c_kw, kw_list, pattern) in tag_to_keyword.items():
            nodes = self._find_tree_nodes_by_tag(context, tag)
            if nodes:
                has_ast = True
                for node in nodes:
                    text = getattr(node, 'text', '') or ""
                    # Skip out-of-body method implementations (e.g. function void Class::method)
                    if tag in ["kFunctionDeclaration", "kTaskDeclaration"] and "::" in text:
                        continue

                    actual_name = self._extract_node_code_name(node, pattern)
                    if actual_name:
                        line = self._node_start_line(node, file_content, context)
                        comments = self._get_comments(node, file_content, context, line)
                        if comments:
                            doc_name = self._extract_documented_name(comments, kw_list)
                            if doc_name and doc_name != actual_name:
                                violations.append(
                                    self.create_violation(
                                        file_path=file_path,
                                        line=line,
                                        message=f"Documented identifier '{doc_name}' does not match code identifier '{actual_name}'."
                                    )
                                )

        # Also check kDataDeclaration and kNetDeclaration nodes in AST mode using SymbolIdentifier
        decl_nodes = self._find_tree_nodes_by_tag(context, "kDataDeclaration") + self._find_tree_nodes_by_tag(context, "kNetDeclaration")
        if decl_nodes:
            has_ast = True
            for node in decl_nodes:
                vars_found = []
                if hasattr(node, 'find_all'):
                    vars_found = list(node.find_all(
                        lambda sub: getattr(sub, 'tag', '') in {'kVariableDeclarationAssignment', 'kRegisterVariable', 'kNetVariable'}
                    ))
                for v in vars_found:
                    idents = list(v.find_all(lambda sub: getattr(sub, 'tag', '') == 'SymbolIdentifier'))
                    actual_name = idents[0].text.strip() if idents else None
                    if actual_name and actual_name not in ["module", "package", "class", "function", "task", "interface", "end", "begin", "assign", "bind", "property", "sequence", "clocking", "modport", "constraint", "program", "checker", "covergroup"]:
                        line = self._node_start_line(node, file_content, context)
                        comments = self._get_comments(node, file_content, context, line)
                        if comments:
                            doc_name = self._extract_documented_name(comments, VAR_KEYWORDS)
                            if doc_name and doc_name != actual_name:
                                violations.append(
                                    self.create_violation(
                                        file_path=file_path,
                                        line=line,
                                        message=f"Documented identifier '{doc_name}' does not match code identifier '{actual_name}'."
                                    )
                                )

        if has_ast:
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        constructs = [
            ("class", ["Class", "class"], r"^\s*(?:virtual\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            ("package", ["Package", "package"], r"^\s*package\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            ("interface", ["Interface", "interface"], r"^\s*interface\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            ("module", ["Module", "module"], r"^\s*module\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            ("function", FUNC_KEYWORDS, r"^\s*(?:pure\s+|virtual\s+|protected\s+|local\s+|static\s+)*function\s+(?:automatic\s+)?(?:void\s+|[\w:<>\[\]\$\s]+\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|;)"),
            ("task", TASK_KEYWORDS, r"^\s*(?:pure\s+|virtual\s+|protected\s+|local\s+|static\s+)*task\s+(?:automatic\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|;)"),
            ("covergroup", ["Covergroup", "covergroup"], r"^\s*covergroup\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            ("checker", ["Checker", "checker"], r"^\s*checker\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            ("modport", ["Modport", "modport"], r"^\s*modport\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            ("clocking", ["Clocking", "clocking"], r"^\s*(?:default\s+)?clocking\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            ("property", ["Property", "property"], r"^\s*property\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            ("sequence", SEQ_KEYWORDS, r"^\s*sequence\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            ("constraint", ["Constraint", "constraint"], r"^\s*(?:static\s+)?constraint\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
            ("program", ["Program", "program"], r"^\s*(?:automatic\s+)?program\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
        ]
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                continue

            for c, kw_list, pattern in constructs:
                if c in ["function", "task"] and "::" in stripped:
                    continue
                match = re.match(pattern, line)
                if match:
                    actual_name = match.group(1)
                    comments = self._get_comments(None, file_content, None, i + 1)
                    if comments:
                        doc_name = self._extract_documented_name(comments, kw_list)
                        if doc_name and doc_name != actual_name:
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=i + 1,
                                    message=f"Documented identifier '{doc_name}' does not match code identifier '{actual_name}'."
                                )
                            )

            # Bind matching: bind <target> <checker/module> <inst_name> (...)
            bind_match = re.match(r"^\s*bind\s+(?:[a-zA-Z_][a-zA-Z0-9_]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)?\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|$)", line)
            if bind_match:
                actual_name = bind_match.group(1)
                comments = self._get_comments(None, file_content, None, i + 1)
                if comments:
                    doc_name = self._extract_documented_name(comments, BIND_KEYWORDS)
                    if doc_name and doc_name != actual_name:
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=i + 1,
                                message=f"Documented identifier '{doc_name}' does not match code identifier '{actual_name}'."
                            )
                        )

            # Assign matching: assign <lhs> = ...
            assign_match = re.match(r"^\s*assign\s+(?:#\s*\([^)]*\)\s*)?([a-zA-Z_][a-zA-Z0-9_]*)", line)
            if assign_match:
                actual_name = assign_match.group(1)
                comments = self._get_comments(None, file_content, None, i + 1)
                if comments:
                    doc_name = self._extract_documented_name(comments, ASSIGN_KEYWORDS)
                    if doc_name and doc_name != actual_name:
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=i + 1,
                                message=f"Documented identifier '{doc_name}' does not match code identifier '{actual_name}'."
                            )
                        )

            # Typedef matching
            type_match = re.match(r"^\s*typedef\s+(?:enum\b|struct\b|union\b)?.*?\b([a-zA-Z_][a-zA-Z0-9_]*)\s*;", line)
            if type_match:
                actual_name = type_match.group(1)
                comments = self._get_comments(None, file_content, None, i + 1)
                if comments:
                    doc_name = self._extract_documented_name(comments, TYPE_KEYWORDS)
                    if doc_name and doc_name != actual_name:
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=i + 1,
                                message=f"Documented identifier '{doc_name}' does not match code identifier '{actual_name}'."
                            )
                        )

            # Macro define matching
            macro_match = re.match(r"^\s*`define\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
            if macro_match:
                actual_name = macro_match.group(1)
                comments = self._get_comments(None, file_content, None, i + 1)
                if comments:
                    doc_name = self._extract_documented_name(comments, MACRO_KEYWORDS)
                    if doc_name and doc_name != actual_name:
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=i + 1,
                                message=f"Documented identifier '{doc_name}' does not match code identifier '{actual_name}'."
                            )
                        )

            # Coverpoint matching
            cp_match = re.match(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*coverpoint\b", line)
            if cp_match:
                actual_name = cp_match.group(1)
                comments = self._get_comments(None, file_content, None, i + 1)
                if comments:
                    doc_name = self._extract_documented_name(comments, ["Coverpoint", "coverpoint", "Point", "point"])
                    if doc_name and doc_name != actual_name:
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=i + 1,
                                message=f"Documented identifier '{doc_name}' does not match code identifier '{actual_name}'."
                            )
                        )

            # Variable / instance matching
            var_match = re.match(
                r"^\s*(?:rand\s+|randc\s+|parameter\s+|localparam\s+|const\s+|static\s+|automatic\s+|protected\s+|local\s+|virtual\s+|var\s+)*(?:logic|bit|int|byte|shortint|longint|integer|time|real|shortreal|string|event|reg|wire|[a-zA-Z_][a-zA-Z0-9_]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)?(?:\s*#\s*\([^)]*\))?)\s+(?:\[[^\]]+\]\s*)*([a-zA-Z_][a-zA-Z0-9_]*)",
                line
            )
            if var_match:
                actual_name = var_match.group(1)
                if actual_name not in ["module", "package", "class", "function", "task", "interface", "end", "begin", "assign", "bind", "property", "sequence", "clocking", "modport", "constraint", "program", "checker", "covergroup", "typedef"]:
                    comments = self._get_comments(None, file_content, None, i + 1)
                    if comments:
                        doc_name = self._extract_documented_name(comments, VAR_KEYWORDS)
                        if doc_name and doc_name != actual_name:
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=i + 1,
                                    message=f"Documented identifier '{doc_name}' does not match code identifier '{actual_name}'."
                                )
                            )

        return violations
