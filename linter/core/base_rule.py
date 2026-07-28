"""
Base class for linting rules

Company: Copyright (c) 2026  IC Verimeter  
         Licensed under the MIT License.

Description: Abstract base class that all linting rules must inherit from
"""

import re
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Any


class RuleSeverity(Enum):
    """Severity level for rule violations"""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class RuleViolation:
    """
    Represents a single rule violation
    
    Attributes:
        file: Path to the file containing the violation
        line: Line number where violation occurs
        column: Column number (optional, depends on linter)
        severity: Severity level of the violation
        message: Human-readable description of the violation
        rule_id: Unique identifier for the rule
        context: Additional context information (optional)
    """
    file: str
    line: int
    column: int
    severity: RuleSeverity
    message: str
    rule_id: str
    context: Optional[str] = None


class BaseRule(ABC):
    """
    Abstract base class for all linting rules
    
    Each rule should:
    - Have a unique rule_id
    - Implement the check() method
    - Define its default severity level
    - Provide a clear description
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize rule with optional configuration
        
        Args:
            config: Optional configuration dictionary for the rule
        """
        self.config = config or {}
        self._enabled = self.config.get('enabled', True)
        self._severity = self._parse_severity(
            self.config.get('severity', self.default_severity())
        )
    
    @property
    @abstractmethod
    def rule_id(self) -> str:
        """
        Unique identifier for this rule (e.g., 'ND_FILE_HDR_MISS')
        
        Returns:
            String identifier for the rule
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of what this rule checks
        
        Returns:
            String description of the rule
        """
        pass
    
    @abstractmethod
    def default_severity(self) -> RuleSeverity:
        """
        Default severity level for violations of this rule
        
        Returns:
            RuleSeverity enum value
        """
        pass
    
    @abstractmethod
    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        """
        Check file for violations of this rule
        
        Args:
            file_path: Path to the file being checked
            file_content: Content of the file as a string
            context: Additional context (e.g., AST, parsed data)
        
        Returns:
            List of RuleViolation objects found
        """
        pass
    
    @property
    def enabled(self) -> bool:
        """Check if rule is enabled"""
        return self._enabled
    
    @property
    def severity(self) -> RuleSeverity:
        """Get configured severity level"""
        return self._severity
    
    def _parse_severity(self, severity_str) -> RuleSeverity:
        """
        Parse severity string to enum
        
        Args:
            severity_str: Severity as string ("ERROR", "WARNING", "INFO") or RuleSeverity object
        
        Returns:
            RuleSeverity enum value
        """
        # If already a RuleSeverity object, return it
        if isinstance(severity_str, RuleSeverity):
            return severity_str
        
        # Parse string to enum
        if isinstance(severity_str, str):
            severity_upper = severity_str.upper()
            if severity_upper == "ERROR":
                return RuleSeverity.ERROR
            elif severity_upper == "WARNING":
                return RuleSeverity.WARNING
            elif severity_upper == "INFO":
                return RuleSeverity.INFO
        
        # Default fallback
        return self.default_severity()
    
    def create_violation(self, file_path: str, line: int, message: str, 
                        column: int = 0, context: Optional[str] = None) -> RuleViolation:
        """
        Helper method to create a RuleViolation with this rule's configuration
        
        Args:
            file_path: Path to file with violation
            line: Line number
            message: Violation message
            column: Column number (default: 0)
            context: Additional context (default: None)
        
        Returns:
            Configured RuleViolation object
        """
        return RuleViolation(
            file=file_path,
            line=line,
            column=column,
            severity=self.severity,
            message=message,
            rule_id=self.rule_id,
            context=context
        )
    
    def _extract_preceding_comments(self, file_content: str, start_line: int,
                                    context: any = None, max_lines: int = 512) -> List[str]:
        """
        Extract comments preceding a given declaration line.

        Uses Verible rawtokens when available, otherwise falls back to text-based
        comment extraction.
        """
        if context and hasattr(context, 'rawtokens') and context.rawtokens:
            return self._extract_comments_from_rawtokens(context, start_line, file_content)
        return self._extract_comments_from_text(file_content, start_line, max_lines)

    def _source_bytes(self, file_content: str, context: any) -> bytes:
        if context and hasattr(context, 'file_bytes') and context.file_bytes:
            return context.file_bytes
        return file_content.encode('utf-8', errors='ignore')

    def _byte_offset_for_line(self, source_bytes: bytes, line: int) -> int:
        if line <= 1:
            return 0
        offset = 0
        current_line = 1
        while offset < len(source_bytes) and current_line < line:
            if source_bytes[offset] == 0x0A:  # '\n'
                current_line += 1
            offset += 1
        return offset

    def _line_for_byte_offset(self, source_bytes: bytes, offset: int) -> int:
        if offset is None or offset < 0:
            return 1

        line = 1
        idx = 0
        while idx < len(source_bytes) and idx < offset:
            if source_bytes[idx] == 0x0A:  # '\n'
                line += 1
            idx += 1
        return line

    def _node_start_line(self, node: any, file_content: str, context: any) -> int:
        if not node or not hasattr(node, 'start') or node.start is None:
            return 1
        source_bytes = self._source_bytes(file_content, context)
        return self._line_for_byte_offset(source_bytes, node.start)

    def _get_rawtokens(self, context: any):
        return getattr(context, 'rawtokens', []) if context else []

    def _is_comment_token(self, token: any) -> bool:
        if token is None or not hasattr(token, 'tag'):
            return False
        tag = token.tag.upper()
        text = token.text.strip() if hasattr(token, 'text') else ""
        return 'COMMENT' in tag or text.startswith('//') or text.startswith('/*')

    def _is_whitespace_token(self, token: any) -> bool:
        if token is None or not hasattr(token, 'tag'):
            return False
        if token.tag in {'TK_SPACE', 'TK_NEWLINE'}:
            return True
        text = token.text if hasattr(token, 'text') else ""
        return text.isspace()

    def _find_rawtoken_index_before_offset(self, tokens: List[any], offset: int) -> int:
        idx = len(tokens) - 1
        while idx >= 0:
            token = tokens[idx]
            if token is None or not hasattr(token, 'start') or token.start is None:
                idx -= 1
                continue
            if token.start < offset:
                return idx
            idx -= 1
        return -1

    def _find_rawtoken_index_after_offset(self, tokens: List[any], offset: int) -> int:
        for idx, token in enumerate(tokens):
            if token is None or not hasattr(token, 'start') or token.start is None:
                continue
            if token.start >= offset:
                return idx
        return len(tokens)

    def _find_tree_nodes(self, context: any, filter_) -> List[any]:
        if not context or not getattr(context, 'tree', None):
            return []
        try:
            return list(context.tree.find_all(filter_))
        except Exception:
            return []

    def _find_tree_nodes_by_tag(self, context: any, tag: str) -> List[any]:
        return self._find_tree_nodes(context, {'tag': tag})

    def _find_tree_nodes_by_text(self, context: any, pattern: str,
                                 flags: int = 0) -> List[any]:
        if not context or not getattr(context, 'tree', None):
            return []
        regex = re.compile(pattern, flags)
        try:
            return [node for node in context.tree.find_all(lambda node: hasattr(node, 'text') and regex.search(node.text))]
        except Exception:
            return []

    def _get_node_text(self, node: any) -> str:
        if node is None:
            return ""
        if hasattr(node, 'text') and node.text is not None:
            return node.text
        if isinstance(node, dict):
            return node.get('text', '') or ''
        return ""

    def _comments_before_node(self, node: any, file_content: str, context: any) -> List[str]:
        if not node:
            return []
        line = self._node_start_line(node, file_content, context)
        return self._extract_preceding_comments(file_content, line, context)

    def _comment_block_before_node(self, node: any, file_content: str, context: any) -> tuple[list[str], bool]:
        if not node:
            return [], False
        line = self._node_start_line(node, file_content, context)
        return self._extract_preceding_comment_block(file_content, line, context)

    def _extract_comments_from_rawtokens(self, context: any, start_line: int,
                                        file_content: str) -> List[str]:
        if not context or not hasattr(context, 'rawtokens') or not context.rawtokens:
            return []

        source_bytes = self._source_bytes(file_content, context)
        if start_line < 1:
            return []

        target_byte_offset = self._byte_offset_for_line(source_bytes, start_line)
        tokens = self._get_rawtokens(context)
        idx = self._find_rawtoken_index_before_offset(tokens, target_byte_offset)

        comment_lines: List[str] = []
        found_comment = False
        blank_line_count = 0

        while idx >= 0:
            token = tokens[idx]
            if self._is_comment_token(token):
                comment_lines.insert(0, self._strip_comment_markers(token.text))
                found_comment = True
                idx -= 1
                continue

            if self._is_whitespace_token(token):
                if not found_comment:
                    blank_line_count += token.text.count('\n')
                else:
                    if token.text.count('\n') > 1:
                        break
                idx -= 1
                continue

            break

        return comment_lines

    def _extract_preceding_comment_block(self, file_content: str, start_line: int,
                                          context: any = None) -> tuple[list[str], bool]:
        """
        Extract the contiguous NaturalDocs comment block immediately preceding a declaration.

        Returns a tuple of (comment lines, has_blank_line_before_declaration).
        """
        if context and hasattr(context, 'rawtokens') and context.rawtokens:
            source_bytes = self._source_bytes(file_content, context)
            target_byte_offset = self._byte_offset_for_line(source_bytes, start_line)
            tokens = self._get_rawtokens(context)
            idx = self._find_rawtoken_index_before_offset(tokens, target_byte_offset)

            comment_lines: List[str] = []
            blank_lines = 0
            found_comment = False

            while idx >= 0:
                token = tokens[idx]
                if self._is_comment_token(token):
                    comment_lines.insert(0, self._strip_comment_markers(token.text))
                    found_comment = True
                    idx -= 1
                    continue

                if self._is_whitespace_token(token):
                    if not found_comment:
                        blank_lines += token.text.count('\n')
                    else:
                        if token.text.count('\n') > 1:
                            break
                    idx -= 1
                    continue

                break

            return comment_lines, (blank_lines > 1)

        # Text-based fallback when rawtokens are unavailable.
        lines = file_content.splitlines()
        comment_lines_fb: List[str] = []
        blank_lines_fb = 0
        idx = start_line - 2

        while idx >= 0:
            stripped = lines[idx].strip()
            if stripped == "":
                blank_lines_fb += 1
                if blank_lines_fb > 1:
                    break
                idx -= 1
                continue

            if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*') or stripped.endswith('*/'):
                comment_lines_fb.insert(0, self._strip_comment_markers(lines[idx]))
                idx -= 1
                continue

            break

        return comment_lines_fb, (blank_lines_fb > 0)

    def _has_inline_comment_in_rawtokens(self, context: any, line_num: int, file_content: str) -> bool:
        """
        Check if a given 1-based source line number contains an inline comment token in context.rawtokens.
        """
        tokens = self._get_rawtokens(context)
        if not tokens:
            return False

        source_bytes = self._source_bytes(file_content, context)
        for token in tokens:
            if self._is_comment_token(token):
                offset = getattr(token, 'start', None)
                if offset is not None:
                    token_line = self._line_for_byte_offset(source_bytes, offset)
                    if token_line == line_num:
                        return True
        return False

    def _next_comment_token(self, context: any, token_index: int):
        tokens = self._get_rawtokens(context)
        for idx in range(token_index + 1, len(tokens)):
            token = tokens[idx]
            if self._is_whitespace_token(token):
                continue
            if self._is_comment_token(token):
                return token
            break
        return None

    def _strip_comment_markers(self, line: str) -> str:
        stripped = line.strip()
        if stripped.startswith('//'):
            return stripped[2:].strip()
        if stripped.startswith('/*'):
            stripped = stripped[2:]
        if stripped.endswith('*/'):
            stripped = stripped[:-2]
        if stripped.startswith('*'):
            stripped = stripped[1:]
        return stripped.strip()

    def _extract_comments_from_text(self, file_content: str, start_line: int,
                                    max_lines: int = 512) -> List[str]:
        lines = file_content.split('\n')
        if start_line < 1 or start_line > len(lines):
            return []

        comments: List[str] = []
        collecting_block_comment = False
        for i in range(start_line - 2, max(-1, start_line - 1 - max_lines), -1):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                if collecting_block_comment:
                    comments.insert(0, "")
                continue

            if stripped.startswith('/*') or stripped.endswith('*/') or stripped.startswith('*'):
                comments.insert(0, self._strip_comment_markers(line))
                if '/*' in stripped and '*/' not in stripped:
                    collecting_block_comment = True
                if '*/' in stripped and '/*' not in stripped:
                    collecting_block_comment = True
                if '/*' in stripped and '*/' in stripped:
                    collecting_block_comment = False
                continue

            if stripped.startswith('//'):
                comments.insert(0, self._strip_comment_markers(line))
                continue

            break

        return comments
    
    def _line_is_comment_line(self, line: str) -> bool:
        stripped = line.lstrip()
        return (
            stripped.startswith('//') or
            stripped.startswith('/*') or
            stripped.startswith('*/') or
            stripped.startswith('*')
        )



    def _get_preceding_comment_block(self, file_content: str, start_line: int,
                                     max_blank_lines: int = 0) -> List[str]:
        """
        Return the contiguous comment block immediately preceding the given line.

        Args:
            file_content: Full file text
            start_line: 1-based line number at which the documented declaration begins
            max_blank_lines: allowed blank lines between comment block and declaration

        Returns:
            List of comment lines in forward order.
        """
        lines = file_content.split('\n')
        comments: List[str] = []
        blank_lines = 0
        idx = start_line - 2

        while idx >= 0:
            stripped = lines[idx].strip()
            if stripped == "":
                blank_lines += 1
                if blank_lines > max_blank_lines:
                    break
                idx -= 1
                continue

            if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*') or stripped.endswith('*/'):
                comments.insert(0, stripped)
                blank_lines = 0
                idx -= 1
                continue

            break

        return comments

    
    def _has_naturaldocs_keyword(self, comments: list, keywords: list) -> bool:
        """
        Check if comments contain any of the NaturalDocs keywords.
        
        Since comment markers (//, /*, */, *) are already stripped during extraction,
        this method searches for keywords directly without requiring comment markers.
        
        Args:
            comments: List of comment lines (with markers already removed)
            keywords: List of keywords to search for (e.g., ['Package', 'Class'])
        
        Returns:
            True if any keyword is found, False otherwise
        """
        comment_text = ' '.join(comments)
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\s*:'
            if re.search(pattern, comment_text, re.IGNORECASE):
                return True
        return False

    def _extract_documented_name(self, comments: list, keywords: list) -> Optional[str]:
        """
        Extract documented identifier from a NaturalDocs keyword line.

        Examples:
            Class: my_class
            Function: build_phase
            Variable: m_counter

        Returns:
            First identifier after any keyword in ``keywords``, or None.
        """
        for line in comments:
            for keyword in keywords:
                pattern = (
                    r'(?i)\b' + re.escape(keyword) +
                    r'\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)'
                )
                match = re.search(pattern, line)
                if match:
                    return match.group(1)
        return None

    def _validate_naturaldocs_keyword(self, comments: list, expected_keywords: list, node_type: str) -> dict:
        """
        Validate NaturalDocs keyword for a declaration comment block.

        Returns:
            {} if no keyword problem is found, otherwise:
            {'rule_id': '[ND_INVALID_KW]'|'[ND_WRONG_KW]', 'message': str}
        """
        if not comments:
            return {}

        # Complete set of official NaturalDocs keywords from
        # https://naturaldocs.org/reference/keywords
        # Database-only keywords (db table, db view, etc.) are omitted
        # because they are irrelevant for SystemVerilog linting.
        valid_keywords = {
            # General: Information
            'topic', 'topics', 'about', 'list',
            # General: Group / Section
            'group', 'section', 'title',
            # General: File
            'file', 'files', 'program', 'programs', 'script', 'scripts',
            'document', 'documents', 'doc', 'docs', 'header', 'headers',
            # Code: Class
            'class', 'classes', 'package', 'packages', 'namespace', 'namespaces',
            'record', 'records',
            # Code: Interface
            'interface', 'interfaces',
            # Code: Struct / Union
            'struct', 'structs', 'structure', 'structures', 'union', 'unions',
            # Code: Module (SystemVerilog only)
            'module', 'modules', 'macromodule', 'macromodules',
            # Code: Type
            'type', 'types', 'typedef', 'typedefs',
            # Code: Enum
            'enum', 'enums', 'enumeration', 'enumerations',
            # Code: Delegate
            'delegate', 'delegates',
            # Code: Event
            'event', 'events',
            # Code: Function
            'function', 'functions', 'func', 'funcs',
            'task', 'tasks',
            'procedure', 'procedures', 'proc', 'procs',
            'routine', 'routines', 'subroutine', 'subroutines', 'sub', 'subs',
            'method', 'methods', 'callback', 'callbacks',
            'constructor', 'constructors', 'destructor', 'destructors',
            # Code: Property
            'property', 'properties', 'prop', 'props',
            # Code: Constant
            'constant', 'constants', 'const', 'consts',
            # Code: Operator
            'operator', 'operators',
            # Code: Macro
            'macro', 'macros', 'define', 'defines', 'def', 'defs',
            # Code: Coverage (SystemVerilog)
            'coverage', 'coverages', 'covergroup', 'covergroups', 'coverpoint', 'coverpoints', 'cross', 'crosses',
            # Code: Constraint (SystemVerilog)
            'constraint', 'constraints',
            # Code: Variable (full family)
            'variable', 'variables', 'var', 'vars',
            'integer', 'integers', 'int', 'ints', 'uint', 'uints',
            'long', 'longs', 'ulong', 'ulongs',
            'short', 'shorts', 'ushort', 'ushorts',
            'byte', 'bytes', 'ubyte', 'ubytes', 'sbyte', 'sbytes',
            'float', 'floats', 'double', 'doubles', 'real', 'reals',
            'decimal', 'decimals', 'scalar', 'scalars',
            'array', 'arrays', 'arrayref', 'arrayrefs',
            'hash', 'hashes', 'hashref', 'hashrefs',
            'table', 'tables',
            'bool', 'bools', 'boolean', 'booleans',
            'flag', 'flags', 'bit', 'bits', 'bitfield', 'bitfields',
            'field', 'fields',
            'pointer', 'pointers', 'ptr', 'ptrs',
            'reference', 'references', 'ref', 'refs',
            'object', 'objects', 'obj', 'objs',
            'character', 'characters', 'char', 'chars',
            'wcharacter', 'wcharacters', 'wchar', 'wchars',
            'string', 'strings', 'str', 'strs',
            'wstring', 'wstrings', 'wstr', 'wstrs',
            'handle', 'handles',
        }
        skip_keywords = {
            'company', 'author', 'description', 'created', 'modified', 'date', 'version',
            'copyright', 'license', 'email', 'project', 'status', 'note', 'notes',
            'see also', 'see', 'todo', 'fixme', 'bug', 'warning', 'deprecated',
            'parameters', 'returns', 'return', 'throws', 'example',
            'group', 'section', 'chapter', 'topic',
        }

        found_keyword = None
        for line in comments:
            # Match NaturalDocs keyword line, accounting for comment markers: //, /*, or *
            match = re.match(r'^\s*(?://|/\*|\*|)\s*([A-Za-z][A-Za-z\s]*?)\s*:\s*\w+', line)
            if not match:
                continue
            candidate = match.group(1).strip()
            candidate_lower = candidate.lower()
            if candidate_lower in skip_keywords:
                continue
            found_keyword = candidate
            break

        if not found_keyword:
            return {}

        found_lower = found_keyword.lower()
        if found_lower not in valid_keywords:
            return {
                'rule_id': '[ND_INVALID_KW]',
                'message': f"Invalid NaturalDocs keyword '{found_keyword}:'"
            }

        expected_lower = {k.lower() for k in expected_keywords}
        if found_lower not in expected_lower:
            expected_str = "', '".join(expected_keywords)
            return {
                'rule_id': '[ND_WRONG_KW]',
                'message': f"Wrong keyword '{found_keyword}:' for {node_type} (expected: '{expected_str}')"
            }

        return {}

    def _get_line_number(self, file_bytes: bytes, byte_offset: int) -> int:
        """Convert byte offset to 1-based line number."""
        if byte_offset is None:
            return 1
        return file_bytes[:byte_offset].count(b'\n') + 1

    def _check_name_mismatch(
        self,
        comments: list,
        keywords: list,
        actual_name: str,
        construct_type: str,
        file_path: str,
        line: int,
    ) -> Optional[RuleViolation]:
        """
        Compare the documented name against the actual declared name.

        Centralised helper so individual rules don't duplicate the same
        extract-compare-violation pattern.

        Args:
            comments:       Comment lines preceding the declaration.
            keywords:       NaturalDocs keywords to search for (e.g. ['Class']).
            actual_name:    Identifier extracted from the AST node.
            construct_type: Human-readable label for the message (e.g. 'class').
            file_path:      Path to the source file.
            line:           Line number of the declaration.

        Returns:
            A RuleViolation if a mismatch is found, otherwise None.
        """
        documented = self._extract_documented_name(comments, keywords)
        if documented and actual_name and documented != actual_name:
            return RuleViolation(
                file=file_path,
                line=line,
                column=0,
                severity=self.severity,
                rule_id="[ND_NAME_MISMATCH]",
                message=(
                    f"{construct_type.capitalize()} docs name '{documented}' "
                    f"does not match {construct_type} '{actual_name}'"
                ),
            )
        return None

