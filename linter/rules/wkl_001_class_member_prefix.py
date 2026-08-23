# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import List, Any
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class ClassMemberPrefixRule(BaseRule):
    """
    [WKL-001] Class Member Prefix Rule
    Checks that class members have the 'm_' or 'is_' prefix, with standard exceptions.
    """
    
    @property
    def rule_id(self) -> str:
        return "[WKL-001]"
    
    @property
    def description(self) -> str:
        return "Class members should have 'm_' prefix (with exceptions)."
        
    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR
        
    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []
        EXCEPTIONS = {'is_active', 'coverage_enable', 'checks_enable', 'regmodel'}

        # AST node driven check
        class_nodes = self._find_tree_nodes_by_tag(context, "kClassDeclaration")
        if class_nodes:
            for class_node in class_nodes:
                data_nodes = []
                if hasattr(class_node, 'find_all'):
                    try:
                        data_nodes = list(class_node.find_all(lambda n: getattr(n, 'tag', '') == 'kDataDeclaration'))
                    except Exception:
                        pass
                for dnode in data_nodes:
                    text = getattr(dnode, 'text', '') or ""
                    if re.search(r"\b(typedef|function|task|const)\b", text):
                        continue
                    vars_found = []
                    if hasattr(dnode, 'find_all'):
                        vars_found = list(dnode.find_all(
                            lambda sub: getattr(sub, 'tag', '') in {'kVariableDeclarationAssignment', 'kRegisterVariable', 'kNetVariable'}
                        ))
                    if vars_found:
                        for v in vars_found:
                            v_text = getattr(v, 'text', '').strip()
                            m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)", v_text)
                            var_name = m.group(1) if m else v_text.split("=")[0].split("[")[0].strip()
                            if var_name and var_name not in EXCEPTIONS and not var_name.startswith("m_") and not var_name.startswith("is_"):
                                line = self._node_start_line(dnode, file_content, context)
                                violations.append(
                                    self.create_violation(
                                        file_path=file_path,
                                        line=line,
                                        message=f"Class member '{var_name}' does not have required 'm_' prefix."
                                    )
                                )
                    else:
                        m = re.match(
                            r"^\s*(?:(?:rand|randc|protected|local|static|const|virtual|automatic)\s+)*"
                            r"(?:(?:logic|bit|byte|shortint|int|longint|integer|time|shortreal|real|realtime|string|[a-zA-Z_][a-zA-Z0-9_]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)*)\s*)"
                            r"(?:\s*\[[^\]]+\])*\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                            text.strip()
                        )
                        if m:
                            var_name = m.group(1)
                            if var_name not in EXCEPTIONS and not var_name.startswith("m_") and not var_name.startswith("is_"):
                                line = self._node_start_line(dnode, file_content, context)
                                violations.append(
                                    self.create_violation(
                                        file_path=file_path,
                                        line=line,
                                        message=f"Class member '{var_name}' does not have required 'm_' prefix."
                                    )
                                )
            return violations

        # Fallback text parsing
        in_class = False
        in_param_header = False
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(r"^\s*class\s+", stripped):
                in_class = True
                if "#(" in stripped and ";" not in stripped:
                    in_param_header = True
                continue
            if in_param_header:
                if ";" in stripped:
                    in_param_header = False
                continue
            if re.match(r"^\s*endclass\b", stripped):
                in_class = False
                continue
            if in_class:
                if re.search(r"\b(typedef|function|task|const)\b", line):
                    continue
                code_part = stripped.split("//")[0].split("/*")[0].strip()
                match = re.match(
                    r"^\s*(?:(?:rand|randc|protected|local|static|const|virtual|automatic)\s+)*"
                    r"(?:(?:logic|bit|byte|shortint|int|longint|integer|time|shortreal|real|realtime|string|[a-zA-Z_][a-zA-Z0-9_]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)*)\s*)"
                    r"(?:\s*\[[^\]]+\])*\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                    code_part
                )
                if match:
                    var_name = match.group(1)
                    if var_name not in EXCEPTIONS and not var_name.startswith("m_") and not var_name.startswith("is_"):
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=i + 1,
                                message=f"Class member '{var_name}' does not have required 'm_' prefix."
                            )
                        )

        return violations

    def _get_identifier_text(self, node):
        if not node:
            return None
        if node.get('text'):
            return node.get('text')
        for child in node.get('children', []):
            if isinstance(child, dict):
                text = self._get_identifier_text(child)
                if text:
                    return text
        return None

    def _validate_member_name(self, name: str, node, file_path: str, file_bytes: bytes, violations: List, exceptions: set):
        if name in exceptions or name.startswith("is_"):
            return
        if name.endswith('_port') or name.endswith('_export') or name == 'vif' or name.endswith('_vif'):
            return
            
        if not name.startswith('m_'):
            start_offset = 0
            if isinstance(node, dict) and 'start' in node:
                start_offset = node['start']
            elif isinstance(node, dict) and 'children' in node and node['children'] and isinstance(node['children'][0], dict) and 'start' in node['children'][0]:
                start_offset = node['children'][0]['start']
                
            line = self._get_line_number(file_bytes, start_offset)
            
            violations.append(
                self.create_violation(
                    file_path=file_path,
                    line=line,
                    message=f"Class member '{name}' should have 'm_' prefix",
                )
            )

    def _get_line_number(self, file_bytes: bytes, byte_offset: int) -> int:
        if byte_offset is None or byte_offset == 0:
            return 1
        return file_bytes[:byte_offset].count(b'\n') + 1
