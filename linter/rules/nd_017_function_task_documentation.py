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
        fn_nodes = self._find_tree_nodes_by_tag(context, "kFunctionDeclaration")
        task_nodes = self._find_tree_nodes_by_tag(context, "kTaskDeclaration")
        nodes = fn_nodes + task_nodes

        if nodes:
            for node in nodes:
                text = getattr(node, 'text', '') or ""
                # Skip out-of-class extern method implementations (handled by ND-030)
                if "::" in text or re.search(r"(function|task)\s+(?:[a-zA-Z_0-9_\[\]:]+\s+)?\w+::\w+", text):
                    continue

                kind = "function" if getattr(node, 'tag', '') == "kFunctionDeclaration" else "task"
                name = ""
                if hasattr(node, 'find_all'):
                    try:
                        id_nodes = list(node.find_all(lambda n: getattr(n, 'tag', '') == 'SymbolIdentifier'))
                        if id_nodes:
                            name = id_nodes[0].text
                    except Exception:
                        pass
                if not name:
                    m = re.search(r"(function|task)\s+(?:automatic\s+)?(?:[a-zA-Z_0-9_\[\]:]+\s+)?([a-zA-Z_][a-zA-Z0-9_]*)", text)
                    if m:
                        name = m.group(2)

                if name:
                    line = self._node_start_line(node, file_content, context)
                    comments = self._comments_before_node(node, file_content, context)
                    if not comments or not any(kind in c.lower() for c in comments):
                        violations.append(
                            self.create_violation(
                                file_path=file_path,
                                line=line,
                                message=f"{kind.capitalize()} '{name}' is missing a NaturalDocs comment ('// {kind.capitalize()}: {name}')."
                            )
                        )
                    else:
                        comment_text = "\n".join(comments)
                        if "Parameters:" in comment_text or "Returns:" in comment_text:
                            lines_in_comment = comment_text.splitlines()
                            for idx, cline in enumerate(lines_in_comment):
                                if cline.strip().startswith("Parameters:") or cline.strip().startswith("Returns:"):
                                    if idx + 1 < len(lines_in_comment) and not re.search(r"-\s*\w+", lines_in_comment[idx+1]):
                                        violations.append(
                                            self.create_violation(
                                                file_path=file_path,
                                                line=line,
                                                message=f"Function/Task '{name}' has improper parameters or returns section formatting."
                                            )
                                        )
                                        break
            return violations

        # Fallback text parsing
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            if "::" in line:
                continue
            match = re.match(r"^\s*(?:extern\s+)?(?:virtual\s+)?(?:protected\s+)?(function|task)\s+(?:automatic\s+)?(?:[a-zA-Z_0-9_\[\]:]+\s+)?([a-zA-Z_][a-zA-Z0-9_]*)", line)
            if match:
                kind = match.group(1)
                func_name = match.group(2)
                
                comments = self._extract_comments_from_text(file_content, i + 1)
                if not comments or not any(kind in c.lower() for c in comments):
                    violations.append(
                        self.create_violation(
                            file_path=file_path,
                            line=i + 1,
                            message=f"{kind.capitalize()} '{func_name}' is missing a NaturalDocs comment ('// {kind.capitalize()}: {func_name}')."
                        )
                    )
                else:
                    comment_text = "\n".join(comments)
                    if "Parameters:" in comment_text or "Returns:" in comment_text:
                        lines_in_comment = comment_text.splitlines()
                        for idx, cline in enumerate(lines_in_comment):
                            if cline.strip().startswith("Parameters:") or cline.strip().startswith("Returns:"):
                                if idx + 1 < len(lines_in_comment) and not re.search(r"-\s*\w+", lines_in_comment[idx+1]):
                                    violations.append(
                                        self.create_violation(
                                            file_path=file_path,
                                            line=i + 1,
                                            message=f"Function/Task '{func_name}' has improper parameters or returns section formatting."
                                        )
                                    )
                                    break

        return violations
