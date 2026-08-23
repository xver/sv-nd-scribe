from agent.fixer.doc_helper import extract_function_params
# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import Any, List
from linter.core.base_rule import BaseRule, RuleViolation, RuleSeverity


class FunctionTaskDocumentationRule(BaseRule):
    """
    [ND-017] Function/Task Documentation Rule
    Functions and tasks MUST have NaturalDocs comment with correct parameter and return documentation format.
    """

    @property
    def rule_id(self) -> str:
        return "[ND-017]"

    @property
    def description(self) -> str:
        return "Function and task declarations MUST have NaturalDocs documentation."

    def default_severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    def check(self, file_path: str, file_content: str, context: Any) -> List[RuleViolation]:
        violations = []

        # AST node driven check
        fn_tags = [
            "kFunctionDeclaration", "kTaskDeclaration",
            "kFunctionPrototype", "kTaskPrototype",
            "kClassConstructorDeclaration", "kClassConstructorPrototype",
            "kMethodDeclaration", "kMethodPrototype",
        ]
        has_ast = False
        for tag in fn_tags:
            nodes = self._find_tree_nodes_by_tag(context, tag)
            if nodes:
                has_ast = True
                for node in nodes:
                    text = getattr(node, 'text', '') or ""
                    # Skip out-of-class extern method implementations (e.g. Class::method)
                    if "::" in text or re.search(r"(function|task)\s+(?:[a-zA-Z_0-9_\[\]:]+\s+)?\w+::\w+", text):
                        continue

                    kind = "task" if "task" in tag.lower() or re.search(r"\btask\b", text) else "function"
                    name = ""
                    if "Constructor" in tag or re.search(r"\bfunction\s+(?:automatic\s+)?new\b", text):
                        name = "new"
                    else:
                        m = re.search(
                            r"\b(?:extern\s+|external\s+)?(?:pure\s+virtual\s+|virtual\s+|protected\s+|local\s+|static\s+)*(?:function|task)(?:\s+automatic)?(?:\s+(?:void|(?:[\w:<>\$]+(?:\s*\[[^\]]+\])*)|\s*(?:\[[^\]]+\])))?\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|;)",
                            text
                        )
                        if m:
                            name = m.group(1)
                        elif hasattr(node, 'find_all'):
                            try:
                                id_nodes = list(node.find_all(lambda n: getattr(n, 'tag', '') == 'SymbolIdentifier'))
                                if id_nodes:
                                    name = id_nodes[-1].text
                            except Exception:
                                pass

                    if name:
                        line = self._node_start_line(node, file_content, context)
                        comments = self._comments_before_node(node, file_content, context)
                        if not comments or not any(re.search(rf'\b{kind}\s*:', c, re.I) for c in comments):
                            violations.append(
                                self.create_violation(
                                    file_path=file_path,
                                    line=line,
                                    message=f"{kind.capitalize()} '{name}' is missing a NaturalDocs comment ('// {kind.capitalize()}: {name}')."
                                )
                            )
                        else:
                            comment_text = "\n".join(comments)
                            src_lines = file_content.splitlines()
                            line_zero_idx = max(0, min(len(src_lines) - 1, line - 1))
                            fn_params = extract_function_params(src_lines[line_zero_idx], src_lines, line_zero_idx)
                            if fn_params and "parameters:" not in comment_text.lower():
                                violations.append(
                                    self.create_violation(
                                        file_path=file_path,
                                        line=line,
                                        message=f"Function/Task '{name}' has parameters but is missing a 'Parameters:' section."
                                    )
                                )
                            elif "Parameters:" in comment_text or "Returns:" in comment_text:
                                lines_in_comment = comment_text.splitlines()
                                for idx, cline in enumerate(lines_in_comment):
                                    if cline.strip().startswith("Parameters:"):
                                        if idx + 1 < len(lines_in_comment) and not re.search(r"-\s*\S+", lines_in_comment[idx+1]):
                                            violations.append(
                                                self.create_violation(
                                                    file_path=file_path,
                                                    line=line,
                                                    message=f"Function/Task '{name}' has improper parameters section formatting."
                                                )
                                            )
                                            break
                                    elif cline.strip().startswith("Returns:"):
                                        if idx + 1 >= len(lines_in_comment) or not lines_in_comment[idx+1].strip():
                                            violations.append(
                                                self.create_violation(
                                                    file_path=file_path,
                                                    line=line,
                                                    message=f"Function/Task '{name}' has improper returns section formatting."
                                                )
                                            )
                                            break
        if has_ast:
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            if "::" in line:
                continue
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                continue

            match = re.match(
                r"^\s*(?:extern\s+|external\s+)?(?:pure\s+virtual\s+|virtual\s+|protected\s+|local\s+|static\s+)*(function|task)(?:\s+automatic)?(?:\s+(?:void|(?:[\w:<>\$]+(?:\s*\[[^\]]+\])*)|\s*(?:\[[^\]]+\])))?\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|;)",
                line
            )
            if match:
                kind = match.group(1)
                func_name = match.group(2)
                
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments or not any(re.search(rf'\b{kind}\s*:', c, re.I) for c in comments):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"{kind.capitalize()} '{func_name}' is missing a NaturalDocs comment ('// {kind.capitalize()}: {func_name}')."
                        )
                    )
                else:
                    comment_text = "\n".join(comments)
                    fn_params = extract_function_params(lines[i], lines, i)
                    if fn_params and "parameters:" not in comment_text.lower():
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=i + 1,
                                message=f"Function/Task '{func_name}' has parameters but is missing a 'Parameters:' section."
                            )
                        )
                    elif "Parameters:" in comment_text or "Returns:" in comment_text:
                        lines_in_comment = comment_text.splitlines()
                        for idx, cline in enumerate(lines_in_comment):
                            if cline.strip().startswith("Parameters:"):
                                if idx + 1 < len(lines_in_comment) and not re.search(r"-\s*\S+", lines_in_comment[idx+1]):
                                    violations.append(
                                        self.create_violation(
                                            file_path=file_path,
                                            line=i + 1,
                                            message=f"Function/Task '{func_name}' has improper parameters section formatting."
                                        )
                                    )
                                    break
                            elif cline.strip().startswith("Returns:"):
                                if idx + 1 >= len(lines_in_comment) or not lines_in_comment[idx+1].strip():
                                    violations.append(
                                        self.create_violation(
                                            file_path=file_path,
                                            line=i + 1,
                                            message=f"Function/Task '{func_name}' has improper returns section formatting."
                                        )
                                    )
                                    break

        return violations
