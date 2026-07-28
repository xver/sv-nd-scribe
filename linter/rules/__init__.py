# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

"""
Linter rules package - Re-exports all individual modular rules (1 rule per file)
"""
from .nd_001_file_header import FileHeaderRule
from .nd_002_include_guard import IncludeGuardRule
from .nd_003_comment_spacing import CommentSpacingRule
from .nd_004_documented_statement import DocumentedStatementRule
from .nd_005_naturaldoc_keyword import NaturalDocKeywordRule
from .nd_006_group_heading import GroupHeadingRule
from .nd_007_macro_documentation import MacroDocumentationRule
from .nd_008_package_documentation import PackageDocumentationRule
from .nd_009_class_documentation import ClassDocumentationRule
from .nd_010_enum_documentation import EnumDocumentationRule
from .nd_011_type_documentation import TypeDocumentationRule
from .nd_012_keyword_description import KeywordDescriptionRule
from .nd_013_interface_documentation import InterfaceDocumentationRule
from .nd_014_module_documentation import ModuleDocumentationRule
from .nd_015_property_assertion import PropertyAssertionRule
from .nd_016_end_label import EndLabelRule
from .nd_017_function_task_documentation import FunctionTaskDocumentationRule
from .nd_018_additional_comment_kind import AdditionalCommentKindRule
from .nd_019_identifier_match import IdentifierMatchRule
from .nd_020_constraint_documentation import ConstraintDocumentationRule
from .nd_021_covergroup_documentation import CovergroupDocumentationRule
from .nd_022_coverpoint_documentation import CoverpointDocumentationRule
from .nd_023_variable_documentation import VariableDocumentationRule
from .nd_024_inline_documentation import InlineDocumentationRule
from .nd_025_checker_documentation import CheckerDocumentationRule
from .nd_026_bind_documentation import BindDocumentationRule
from .nd_027_process_documentation import ProcessDocumentationRule
from .nd_028_assign_documentation import AssignDocumentationRule
from .nd_029_program_documentation import ProgramDocumentationRule
from .nd_030_extern_implementation import ExternImplementationRule
from .nd_031_clocking_documentation import ClockingDocumentationRule
from .nd_032_modport_documentation import ModportDocumentationRule

from .wkl_001_class_member_prefix import ClassMemberPrefixRule
from .wkl_002_typedef_suffix import TypedefSuffixRule
from .wkl_003_macro_format import MacroFormatRule
from .wkl_004_interface_naming import InterfaceNamingRule
from .wkl_005_eof_empty_line import EOFEmptyLineRule
from .wkl_006_trailing_whitespace import TrailingWhitespaceRule
from .wkl_007_line_length import LineLengthRule
from .wkl_008_no_tabs import NoTabsRule

__all__ = [
    "FileHeaderRule",
    "IncludeGuardRule",
    "CommentSpacingRule",
    "DocumentedStatementRule",
    "NaturalDocKeywordRule",
    "GroupHeadingRule",
    "MacroDocumentationRule",
    "PackageDocumentationRule",
    "ClassDocumentationRule",
    "EnumDocumentationRule",
    "TypeDocumentationRule",
    "KeywordDescriptionRule",
    "InterfaceDocumentationRule",
    "ModuleDocumentationRule",
    "PropertyAssertionRule",
    "EndLabelRule",
    "FunctionTaskDocumentationRule",
    "AdditionalCommentKindRule",
    "IdentifierMatchRule",
    "ConstraintDocumentationRule",
    "CovergroupDocumentationRule",
    "CoverpointDocumentationRule",
    "VariableDocumentationRule",
    "InlineDocumentationRule",
    "CheckerDocumentationRule",
    "BindDocumentationRule",
    "ProcessDocumentationRule",
    "AssignDocumentationRule",
    "ProgramDocumentationRule",
    "ExternImplementationRule",
    "ClockingDocumentationRule",
    "ModportDocumentationRule",
    "ClassMemberPrefixRule",
    "TypedefSuffixRule",
    "MacroFormatRule",
    "InterfaceNamingRule",
    "EOFEmptyLineRule",
    "TrailingWhitespaceRule",
    "LineLengthRule",
    "NoTabsRule",
]
