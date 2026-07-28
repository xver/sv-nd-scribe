# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

"""
SV ND Scribe - NaturalDoc Linter

Description: Adapter for SV ND Scribe NaturalDoc rules linting using Verible AST
"""

import os
import sys
import shutil
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

_current_dir = os.path.dirname(os.path.abspath(__file__))

from .core.base_linter import BaseLinter
from .core.linter_registry import register_linter

# Try to import verible_verilog_syntax
try:
    from . import verible_verilog_syntax
    VERIBLE_AVAILABLE = True
except ImportError:
    VERIBLE_AVAILABLE = False


@dataclass
class ASTContext:
    """Context object containing AST and file data"""
    tree: any
    file_bytes: bytes
    rawtokens: Optional[List] = None  # Verible rawtokens including comment tokens
    errors: Optional[List] = None


@register_linter
class NaturalDocLinter(BaseLinter):
    """
    NaturalDoc conventions linter for sv-nd-scribe using Verible AST parser.
    """

    @property
    def name(self) -> str:
        return "naturaldoc_linter"

    @property
    def supported_extensions(self) -> List[str]:
        return ['.sv', '.svh']

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize linter
        """
        self.is_available = VERIBLE_AVAILABLE
        super().__init__(config)

        if not self.is_available:
            return

        self.verible_bin = self._find_verible_binary()
        if not self.verible_bin:
            self.is_available = False
            return

    def _find_verible_binary(self) -> Optional[str]:
        for bin_name in ["verible-verilog-syntax", "verible-verilog-syntax.exe"]:
            verible_bin = shutil.which(bin_name)
            if verible_bin:
                return verible_bin

        verible_home = os.environ.get('VERIBLE_HOME')
        if verible_home:
            for bin_name in ['verible-verilog-syntax', 'verible-verilog-syntax.exe']:
                verible_bin = os.path.join(verible_home, 'bin', bin_name)
                if os.path.exists(verible_bin):
                    return verible_bin

            for bin_name in ['verible-verilog-syntax', 'verible-verilog-syntax.exe']:
                verible_bin = os.path.join(verible_home, bin_name)
                if os.path.exists(verible_bin):
                    return verible_bin

        return None

    def _rule_config(self, rule_id: str) -> Dict[str, Any]:
        """
        Build BaseRule kwargs from config.
        """
        cfg: Dict[str, Any] = {}
        rules_cfg = self.config.get("rules", {})
        if rule_id in rules_cfg:
            rule_spec = rules_cfg[rule_id]
            if isinstance(rule_spec, dict):
                if 'enabled' in rule_spec:
                    cfg['enabled'] = rule_spec['enabled']
                if 'severity' in rule_spec:
                    cfg['severity'] = rule_spec['severity']
        return cfg

    def _register_rules(self):
        """Register all NaturalDoc linter rules"""

        from .rules import (
            ClassMemberPrefixRule,
            TypedefSuffixRule,
            MacroFormatRule,
            InterfaceNamingRule,
            EOFEmptyLineRule,
            TrailingWhitespaceRule,
            LineLengthRule,
            NoTabsRule,
            FileHeaderRule,
            IncludeGuardRule,
            CommentSpacingRule,
            GroupHeadingRule,
            MacroDocumentationRule,
            PackageDocumentationRule,
            ClassDocumentationRule,
            EnumDocumentationRule,
            TypeDocumentationRule,
            DocumentedStatementRule,
            NaturalDocKeywordRule,
            KeywordDescriptionRule,
            InterfaceDocumentationRule,
            ModuleDocumentationRule,
            PropertyAssertionRule,
            EndLabelRule,
            FunctionTaskDocumentationRule,
            AdditionalCommentKindRule,
            IdentifierMatchRule,
            ConstraintDocumentationRule,
            CovergroupDocumentationRule,
            CoverpointDocumentationRule,
            VariableDocumentationRule,
            InlineDocumentationRule,
            CheckerDocumentationRule,
            BindDocumentationRule,
            ProcessDocumentationRule,
            AssignDocumentationRule,
            ProgramDocumentationRule,
            ExternImplementationRule,
            ClockingDocumentationRule,
            ModportDocumentationRule,
        )

        # 1. Naming Rules
        self.add_rule(ClassMemberPrefixRule(self._rule_config("[WKL-001]")))
        self.add_rule(TypedefSuffixRule(self._rule_config("[WKL-002]")))
        self.add_rule(MacroFormatRule(self._rule_config("[WKL-003]")))
        self.add_rule(InterfaceNamingRule(self._rule_config("[WKL-004]")))

        # 2. Format Rules
        self.add_rule(EOFEmptyLineRule(self._rule_config("[WKL-005]")))
        self.add_rule(TrailingWhitespaceRule(self._rule_config("[WKL-006]")))
        self.add_rule(LineLengthRule(self._rule_config("[WKL-007]")))
        self.add_rule(NoTabsRule(self._rule_config("[WKL-008]")))

        # 3. Doc Rules
        self.add_rule(FileHeaderRule(self._rule_config("[ND-001]")))
        self.add_rule(IncludeGuardRule(self._rule_config("[ND-002]")))
        self.add_rule(CommentSpacingRule(self._rule_config("[ND-003]")))
        self.add_rule(GroupHeadingRule(self._rule_config("[ND-006]")))
        self.add_rule(MacroDocumentationRule(self._rule_config("[ND-007]")))
        self.add_rule(PackageDocumentationRule(self._rule_config("[ND-008]")))
        self.add_rule(ClassDocumentationRule(self._rule_config("[ND-009]")))
        self.add_rule(EnumDocumentationRule(self._rule_config("[ND-010]")))
        self.add_rule(TypeDocumentationRule(self._rule_config("[ND-011]")))
        self.add_rule(DocumentedStatementRule(self._rule_config("[ND-004]")))
        self.add_rule(NaturalDocKeywordRule(self._rule_config("[ND-005]")))
        self.add_rule(KeywordDescriptionRule(self._rule_config("[ND-012]")))
        self.add_rule(InterfaceDocumentationRule(self._rule_config("[ND-013]")))
        self.add_rule(ModuleDocumentationRule(self._rule_config("[ND-014]")))
        self.add_rule(PropertyAssertionRule(self._rule_config("[ND-015]")))
        self.add_rule(EndLabelRule(self._rule_config("[ND-016]")))
        self.add_rule(FunctionTaskDocumentationRule(self._rule_config("[ND-017]")))
        self.add_rule(AdditionalCommentKindRule(self._rule_config("[ND-018]")))
        self.add_rule(IdentifierMatchRule(self._rule_config("[ND-019]")))
        self.add_rule(ConstraintDocumentationRule(self._rule_config("[ND-020]")))
        self.add_rule(CovergroupDocumentationRule(self._rule_config("[ND-021]")))
        self.add_rule(CoverpointDocumentationRule(self._rule_config("[ND-022]")))
        self.add_rule(VariableDocumentationRule(self._rule_config("[ND-023]")))
        self.add_rule(InlineDocumentationRule(self._rule_config("[ND-024]")))
        self.add_rule(CheckerDocumentationRule(self._rule_config("[ND-025]")))
        self.add_rule(BindDocumentationRule(self._rule_config("[ND-026]")))
        self.add_rule(ProcessDocumentationRule(self._rule_config("[ND-027]")))
        self.add_rule(AssignDocumentationRule(self._rule_config("[ND-028]")))
        self.add_rule(ProgramDocumentationRule(self._rule_config("[ND-029]")))
        self.add_rule(ExternImplementationRule(self._rule_config("[ND-030]")))
        self.add_rule(ClockingDocumentationRule(self._rule_config("[ND-031]")))
        self.add_rule(ModportDocumentationRule(self._rule_config("[ND-032]")))

    def prepare_context(self, file_path: str, file_content: str) -> Optional[ASTContext]:
        try:
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
        except Exception:
            file_bytes = file_content.encode('utf-8', errors='ignore')

        if not self.is_available or not getattr(self, 'verible_bin', None):
            return ASTContext(tree=None, file_bytes=file_bytes, rawtokens=None, errors=None)

        try:
            parser = verible_verilog_syntax.VeribleVerilogSyntax(executable=self.verible_bin)
            file_data = parser.parse_string(file_content, options={
                'gen_tree': True,
                'gen_rawtokens': True
            })

            if not file_data:
                return ASTContext(tree=None, file_bytes=file_bytes, rawtokens=None, errors=None)

            rawtokens = getattr(file_data, 'rawtokens', None)
            errors = getattr(file_data, 'errors', None)
            tree = getattr(file_data, 'tree', None)

            if tree is None:
                return ASTContext(tree=None, file_bytes=file_bytes, rawtokens=rawtokens, errors=errors)

            return ASTContext(tree=tree, file_bytes=file_bytes, rawtokens=rawtokens, errors=errors)
        except Exception as e:
            print(f"Exception in prepare_context: {e}")
            import traceback
            traceback.print_exc()
            return ASTContext(tree=None, file_bytes=file_bytes, rawtokens=None, errors=[str(e)])
