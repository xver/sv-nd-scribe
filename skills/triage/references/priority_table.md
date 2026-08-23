# Priority Tiers

## Critical (fix first)
| Rule | Reason |
|---|---|
| ND-001 | Missing file header — required by every file |
| ND-002 | Missing include guard — causes double-include errors |
| ND-016 | Missing end labels — SV style error, affects all `end*` statements |

## High (fix second — structural constructs)
| Rule | Reason |
|---|---|
| ND-014 | Module undocumented — top-level construct |
| ND-013 | Interface undocumented — shared protocol definition |
| ND-009 | Class undocumented — primary UVM component |
| ND-008 | Package undocumented — shared type container |
| ND-017 | Function/Task undocumented — primary API surface |
| ND-025 | Checker undocumented — formal verification construct |
| ND-029 | Program undocumented |

## Medium (fix third — members and types)
| Rule | Reason |
|---|---|
| ND-007 | Macro undocumented |
| ND-010 | Enum undocumented |
| ND-011 | Typedef undocumented |
| ND-015 | Property/assertion undocumented |
| ND-020 | Constraint undocumented |
| ND-021 | Covergroup undocumented |
| ND-022 | Coverpoint undocumented |
| ND-023 | Variable undocumented |
| ND-026 | Bind undocumented |
| ND-027 | Process undocumented |
| ND-028 | Assign undocumented |
| ND-030 | Extern implementation undocumented |
| ND-031 | Clocking block undocumented |
| ND-032 | Modport undocumented |

## Low (fix last — formatting and style)
| Rule | Reason |
|---|---|
| ND-003 | Comment spacing — cosmetic |
| ND-004 | Documented statement — minor |
| ND-005 | Keyword spacing — cosmetic |
| ND-006 | Group heading missing — organisational |
| ND-012 | Missing description — cosmetic |
| ND-018 | Additional comment kind — checker |
| ND-019 | Identifier mismatch — INTERACTIVE, requires human decision |
| ND-024 | Inline doc — supplemental |
| WKL-005 | EOF newline — compiler hygiene |
| WKL-006 | Trailing whitespace — cosmetic |
| WKL-008 | No tabs — formatting |

## Report-Only (unsafe — no auto-fix)
| Rule | Reason |
|---|---|
| WKL-001 | Class member prefix — renaming risk |
| WKL-002 | Typedef suffix — renaming risk |
| WKL-003 | Macro format — renaming risk |
| WKL-004 | Interface naming — renaming risk |
| WKL-007 | Line length — structural change needed |
